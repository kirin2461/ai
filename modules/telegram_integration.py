"""Telegram бот интеграция"""
import asyncio
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BotStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"


@dataclass
class TelegramConfig:
    """Конфигурация Telegram бота"""
    token: str = ""
    allowed_users: list = None  # None = все пользователи
    max_message_length: int = 4096
    typing_simulation: bool = True
    
    def __post_init__(self):
        if self.allowed_users is None:
            self.allowed_users = []


class TelegramBot:
    """Telegram бот для AI Humanity"""
    
    def __init__(self, config: TelegramConfig, cognitive_cycle=None):
        self.config = config
        self.cognitive = cognitive_cycle
        self.status = BotStatus.STOPPED
        self.app = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._on_message_callback: Optional[Callable] = None
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
    
    def set_message_callback(self, callback: Callable):
        """Установить callback для получения сообщений в GUI"""
        self._on_message_callback = callback
    
    async def start(self) -> bool:
        """Запустить бота"""
        if not self.config.token:
            logger.error("[Telegram] Токен не указан!")
            self.status = BotStatus.ERROR
            return False
        
        try:
            from telegram import Update, Bot
            from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
            
            self.status = BotStatus.STARTING
            logger.info("[Telegram] Запуск бота...")
            
            # Создаём приложение
            self.app = Application.builder().token(self.config.token).build()
            
            # Регистрируем обработчики
            self.app.add_handler(CommandHandler("start", self._cmd_start))
            self.app.add_handler(CommandHandler("help", self._cmd_help))
            self.app.add_handler(CommandHandler("status", self._cmd_status))
            self.app.add_handler(CommandHandler("emotion", self._cmd_emotion))
            self.app.add_handler(CommandHandler("skills", self._cmd_skills))
            self.app.add_handler(CommandHandler("reset", self._cmd_reset))
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
            
            # Запускаем
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            
            self.status = BotStatus.RUNNING
            logger.info("[Telegram] Бот запущен успешно!")
            return True
            
        except ImportError:
            logger.error("[Telegram] python-telegram-bot не установлен. Выполните: pip install python-telegram-bot")
            self.status = BotStatus.ERROR
            return False
        except Exception as e:
            logger.error(f"[Telegram] Ошибка запуска: {e}")
            self.status = BotStatus.ERROR
            return False
    
    async def stop(self):
        """Остановить бота"""
        if self.app:
            logger.info("[Telegram] Остановка бота...")
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            self.status = BotStatus.STOPPED
            logger.info("[Telegram] Бот остановлен")
    
    def _check_user(self, user_id: int) -> bool:
        """Проверить, разрешён ли пользователь"""
        if not self.config.allowed_users:
            return True  # Пустой список = все разрешены
        return user_id in self.config.allowed_users
    
    def _get_session(self, user_id: int) -> Dict[str, Any]:
        """Получить или создать сессию пользователя"""
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                "message_count": 0,
                "last_emotion": None,
            }
        return self.user_sessions[user_id]
    
    async def _cmd_start(self, update, context):
        """Команда /start"""
        user = update.effective_user
        if not self._check_user(user.id):
            await update.message.reply_text("⛔ Доступ запрещён")
            return
        
        welcome = (
            f"👋 Привет, {user.first_name}!\n\n"
            "Я **AI Humanity** — твой AI-компаньон с эмоциями.\n\n"
            "📝 Просто напиши мне что-нибудь!\n"
            "📋 Команды: /help"
        )
        await update.message.reply_text(welcome, parse_mode="Markdown")
    
    async def _cmd_help(self, update, context):
        """Команда /help"""
        help_text = (
            "🤖 **AI Humanity — Команды**\n\n"
            "/start — Начать общение\n"
            "/status — Мой статус\n"
            "/emotion — Текущая эмоция\n"
            "/skills — Мои навыки\n"
            "/reset — Сбросить контекст\n"
            "/help — Эта справка\n\n"
            "💬 Или просто напиши сообщение!"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
    
    async def _cmd_status(self, update, context):
        """Команда /status"""
        if not self._check_user(update.effective_user.id):
            return
        
        if self.cognitive:
            state = self.cognitive.get_state()
            status_text = (
                "📊 **Мой статус**\n\n"
                f"🧠 Цикл: {state['cycle']}\n"
                f"😊 Эмоция: {state['emotion']}\n"
                f"💭 Настроение: {state['mood']}\n"
                f"⚡ Уровень: {state['total_level']}\n"
                f"🛡️ Режим безопасности: {state['safety_mode']}"
            )
        else:
            status_text = "⚠️ Когнитивная система не подключена"
        
        await update.message.reply_text(status_text, parse_mode="Markdown")
    
    async def _cmd_emotion(self, update, context):
        """Команда /emotion"""
        if not self._check_user(update.effective_user.id):
            return
        
        if self.cognitive:
            state = self.cognitive.get_state()
            pad = state['pad']
            emotion_text = (
                "😊 **Эмоциональное состояние**\n\n"
                f"Эмоция: **{state['emotion']}**\n"
                f"Уверенность: {state['confidence']:.0%}\n\n"
                "📊 PAD модель:\n"
                f"• Pleasure: {pad['pleasure']:.2f}\n"
                f"• Arousal: {pad['arousal']:.2f}\n"
                f"• Dominance: {pad['dominance']:.2f}\n\n"
                f"💭 {state['mood']}"
            )
        else:
            emotion_text = "⚠️ Система эмоций не подключена"
        
        await update.message.reply_text(emotion_text, parse_mode="Markdown")
    
    async def _cmd_skills(self, update, context):
        """Команда /skills"""
        if not self._check_user(update.effective_user.id):
            return
        
        if self.cognitive:
            skills = self.cognitive.skills.skills
            skills_text = "⚡ **Мои навыки**\n\n"
            for name, skill in list(skills.items())[:10]:
                skills_text += f"• {skill.name}: {skill.level.value} ({int(skill.experience)} XP)\n"
            skills_text += f"\n🎯 Общий уровень: {self.cognitive.skills.get_total_level()}"
        else:
            skills_text = "⚠️ Система навыков не подключена"
        
        await update.message.reply_text(skills_text, parse_mode="Markdown")
    
    async def _cmd_reset(self, update, context):
        """Команда /reset"""
        user_id = update.effective_user.id
        if not self._check_user(user_id):
            return
        
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        await update.message.reply_text("🔄 Контекст сброшен. Начнём сначала!")
    
    async def _handle_message(self, update, context):
        """Обработка текстовых сообщений"""
        user = update.effective_user
        if not self._check_user(user.id):
            await update.message.reply_text("⛔ Доступ запрещён")
            return
        
        text = update.message.text
        session = self._get_session(user.id)
        session["message_count"] += 1
        
        # Уведомляем GUI если есть callback
        if self._on_message_callback:
            self._on_message_callback(user.first_name, text)
        
        # Имитация набора текста
        if self.config.typing_simulation:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Генерируем ответ
        if self.cognitive:
            response = self.cognitive.run_cycle(text)
            session["last_emotion"] = self.cognitive.get_state()["emotion"]
        else:
            response = "🤖 Привет! Я работаю в автономном режиме."
        
        # Разбиваем длинные сообщения
        if len(response) > self.config.max_message_length:
            chunks = [response[i:i+self.config.max_message_length] 
                     for i in range(0, len(response), self.config.max_message_length)]
            for chunk in chunks:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text(response)


class TelegramManager:
    """Менеджер Telegram бота для интеграции с AI Humanity"""
    
    def __init__(self, cognitive_cycle=None):
        self.cognitive = cognitive_cycle
        self.bot: Optional[TelegramBot] = None
        self._thread = None
    
    def initialize(self, token: str, allowed_users: list = None) -> bool:
        """Инициализировать бота"""
        config = TelegramConfig(token=token, allowed_users=allowed_users or [])
        self.bot = TelegramBot(config, self.cognitive)
        return True
    
    def start_async(self):
        """Запустить бота в отдельном потоке"""
        import threading
        
        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.bot.start())
            loop.run_forever()
        
        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Остановить бота"""
        if self.bot:
            asyncio.run(self.bot.stop())
    
    @property
    def is_running(self) -> bool:
        return self.bot and self.bot.status == BotStatus.RUNNING
