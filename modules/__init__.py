from .desktop_avatar import AvatarManager, DesktopAvatar
from .tts_engine import TTSEngine, TTSConfig, TTSStatus
from .telegram_integration import TelegramBot, TelegramManager, TelegramConfig
from .face_emotion import (
    FaceEmotionDetector,
    FaceEmotionManager,
    FaceEmotionConfig,
    EmotionResult,
)
from .calendar_integration import (
    GoogleCalendarAPI,
    CalendarManager,
    CalendarConfig,
    CalendarEvent,
)
from .online_brain import OnlineBrain  # новый импорт


__all__ = [
    "AvatarManager",
    "DesktopAvatar",
    "TTSEngine",
    "TTSConfig",
    "TTSStatus",
    "TelegramBot",
    "TelegramManager",
    "TelegramConfig",
    "FaceEmotionDetector",
    "FaceEmotionManager",
    "FaceEmotionConfig",
    "EmotionResult",
    "GoogleCalendarAPI",
    "CalendarManager",
    "CalendarConfig",
    "CalendarEvent",
    "OnlineBrain",
]
