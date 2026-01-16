"""Google Calendar интеграция с поддержкой timezone"""
import os
import json
import datetime
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

# Настройка логирования
logger = logging.getLogger(__name__)

# Получаем timezone из переменных окружения
DEFAULT_TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow')


@dataclass
class CalendarEvent:
    """Событие календаря"""
    id: str
    title: str
    description: str
    start: datetime.datetime
    end: datetime.datetime
    location: str = ""
    attendees: List[str] = field(default_factory=list)
    is_all_day: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "location": self.location,
            "attendees": self.attendees,
            "is_all_day": self.is_all_day
        }
    
    def __str__(self):
        time_str = self.start.strftime("%H:%M") if not self.is_all_day else "Весь день"
        return f"{time_str} — {self.title}"


@dataclass
class CalendarConfig:
    """Конфигурация Google Calendar"""
    credentials_path: str = "config/google_credentials.json"
    token_path: str = "config/google_token.json"
    scopes: List[str] = field(default_factory=lambda: [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events"
    ])
    calendar_id: str = "primary"
    timezone: str = field(default_factory=lambda: DEFAULT_TIMEZONE)


class GoogleCalendarAPI:
    """API для работы с Google Calendar"""
    
    def __init__(self, config: CalendarConfig = None):
        self.config = config or CalendarConfig()
        self.service = None
        self._is_authenticated = False
    
    def authenticate(self) -> bool:
        """Аутентификация через OAuth 2.0"""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            
            creds = None
            
            if os.path.exists(self.config.token_path):
                creds = Credentials.from_authorized_user_file(
                    self.config.token_path, 
                    self.config.scopes
                )
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.config.credentials_path):
                        logger.warning(f"Файл credentials не найден: {self.config.credentials_path}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.config.credentials_path,
                        self.config.scopes
                    )
                    creds = flow.run_local_server(port=0)
                
                os.makedirs(os.path.dirname(self.config.token_path), exist_ok=True)
                with open(self.config.token_path, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('calendar', 'v3', credentials=creds)
            self._is_authenticated = True
            logger.info("Calendar аутентификация успешна!")
            return True
            
        except ImportError:
            logger.error("Не установлены зависимости для Google Calendar")
            return False
        except Exception as e:
            logger.error(f"Ошибка аутентификации Calendar: {e}")
            return False
    
    def get_upcoming_events(self, max_results: int = 10, days_ahead: int = 7) -> List[CalendarEvent]:
        """Получить предстоящие события"""
        if not self._is_authenticated:
            if not self.authenticate():
                return []
        
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            time_min = now.isoformat()
            time_max = (now + datetime.timedelta(days=days_ahead)).isoformat()
            
            events_result = self.service.events().list(
                calendarId=self.config.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return [self._parse_event(e) for e in events]
            
        except Exception as e:
            logger.error(f"Ошибка получения событий: {e}")
            return []
    
    def get_today_events(self) -> List[CalendarEvent]:
        """Получить события на сегодня"""
        if not self._is_authenticated:
            if not self.authenticate():
                return []
        
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + datetime.timedelta(days=1)
            
            events_result = self.service.events().list(
                calendarId=self.config.calendar_id,
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return [self._parse_event(e) for e in events]
            
        except Exception as e:
            logger.error(f"Ошибка получения событий: {e}")
            return []
    
    def create_event(
        self,
        title: str,
        start: datetime.datetime,
        end: datetime.datetime = None,
        description: str = "",
        location: str = ""
    ) -> Optional[CalendarEvent]:
        """Создать событие"""
        if not self._is_authenticated:
            if not self.authenticate():
                return None
        
        try:
            if end is None:
                end = start + datetime.timedelta(hours=1)
            
            event_body = {
                'summary': title,
                'description': description,
                'location': location,
                'start': {
                    'dateTime': start.isoformat(),
                    'timeZone': self.config.timezone,
                },
                'end': {
                    'dateTime': end.isoformat(),
                    'timeZone': self.config.timezone,
                },
            }
            
            event = self.service.events().insert(
                calendarId=self.config.calendar_id,
                body=event_body
            ).execute()
            
            logger.info(f"Создано событие: {title}")
            return self._parse_event(event)
            
        except Exception as e:
            logger.error(f"Ошибка создания события: {e}")
            return None
    
    def delete_event(self, event_id: str) -> bool:
        """Удалить событие"""
        if not self._is_authenticated:
            if not self.authenticate():
                return False
        
        try:
            self.service.events().delete(
                calendarId=self.config.calendar_id,
                eventId=event_id
            ).execute()
            logger.info(f"Событие удалено: {event_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления события: {e}")
            return False
    
    def _parse_event(self, event_data: Dict) -> CalendarEvent:
        """Парсинг события из API"""
        start_data = event_data.get('start', {})
        end_data = event_data.get('end', {})
        
        is_all_day = 'date' in start_data
        
        if is_all_day:
            start = datetime.datetime.fromisoformat(start_data['date'])
            end = datetime.datetime.fromisoformat(end_data['date'])
        else:
            start_str = start_data.get('dateTime', '')
            end_str = end_data.get('dateTime', '')
            start = datetime.datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            end = datetime.datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        
        attendees = [a.get('email', '') for a in event_data.get('attendees', [])]
        
        return CalendarEvent(
            id=event_data.get('id', ''),
            title=event_data.get('summary', 'Без названия'),
            description=event_data.get('description', ''),
            start=start,
            end=end,
            location=event_data.get('location', ''),
            attendees=attendees,
            is_all_day=is_all_day
        )


class CalendarManager:
    """Менеджер календаря для AI Humanity"""
    
    def __init__(self, cognitive_cycle=None):
        self.cognitive = cognitive_cycle
        self.api: Optional[GoogleCalendarAPI] = None
        self.enabled = False
        self._cached_events: List[CalendarEvent] = []
        self._last_update: Optional[datetime.datetime] = None
    
    def initialize(self, config: CalendarConfig = None) -> bool:
        """Инициализировать API календаря"""
        self.api = GoogleCalendarAPI(config)
        success = self.api.authenticate()
        self.enabled = success
        return success
    
    def get_schedule_summary(self) -> str:
        """Получить краткую сводку расписания"""
        if not self.enabled or not self.api:
            return "Календарь не подключён"
        
        today = self.api.get_today_events()
        upcoming = self.api.get_upcoming_events(max_results=5, days_ahead=3)
        
        summary = "📅 **Расписание**\n\n"
        
        if today:
            summary += "**Сегодня:**\n"
            for event in today:
                summary += f"• {event}\n"
        else:
            summary += "Сегодня событий нет\n"
        
        today_ids = {e.id for e in today}
        upcoming_filtered = [e for e in upcoming if e.id not in today_ids]
        
        if upcoming_filtered:
            summary += "\n**Ближайшие:**\n"
            for event in upcoming_filtered[:3]:
                date_str = event.start.strftime("%d.%m")
                summary += f"• {date_str}: {event.title}\n"
        
        return summary
    
    def check_reminders(self) -> List[str]:
        """Проверить события, требующие напоминания"""
        if not self.enabled or not self.api:
            return []
        
        reminders = []
        now = datetime.datetime.now(datetime.timezone.utc)
        
        for event in self.api.get_today_events():
            event_start = event.start
            if event_start.tzinfo is None:
                event_start = event_start.replace(tzinfo=datetime.timezone.utc)
            
            time_until = (event_start - now).total_seconds()
            if 0 < time_until <= 900:
                minutes = int(time_until / 60)
                reminders.append(f"⏰ Через {minutes} мин: {event.title}")
        
        return reminders
    
    def quick_add(self, title: str, when: str = "tomorrow") -> Optional[CalendarEvent]:
        """Быстрое добавление события"""
        if not self.enabled or not self.api:
            return None
        
        now = datetime.datetime.now()
        
        if when == "tomorrow":
            start = now.replace(hour=10, minute=0, second=0) + datetime.timedelta(days=1)
        elif when == "today":
            start = now.replace(hour=now.hour + 1, minute=0, second=0)
        else:
            start = now + datetime.timedelta(hours=1)
        
        return self.api.create_event(title, start)
