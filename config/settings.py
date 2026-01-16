"""Настройки AI Humanity - поддержка .env файла"""
import os
from pathlib import Path

# Пробуем загрузить .env файл
try:
    from dotenv import load_dotenv
    # Ищем .env в корне проекта
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"[Config] Загружен .env из {env_path}")
    else:
        load_dotenv()  # Попробовать найти автоматически
except ImportError:
    pass  # python-dotenv не установлен

# === API Ключи ===
# Приоритет: переменная окружения > значение по умолчанию
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
GOOGLE_CALENDAR_CREDENTIALS = os.getenv('GOOGLE_CALENDAR_CREDENTIALS', 'config/google_credentials.json')

# === Настройки приложения ===
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# === TTS Настройки ===
TTS_USE_GPU = os.getenv('TTS_USE_GPU', 'True').lower() in ('true', '1', 'yes')
TTS_LANGUAGE = os.getenv('TTS_LANGUAGE', 'ru')
TTS_SPEED = float(os.getenv('TTS_SPEED', '1.0'))

# === Проверка обязательных настроек ===
def validate_config():
    """Проверить наличие необходимых настроек"""
    warnings = []
    
    if not OPENAI_API_KEY:
        warnings.append("OPENAI_API_KEY не установлен - AI будет работать в offline режиме")
    
    if not TELEGRAM_TOKEN:
        warnings.append("TELEGRAM_TOKEN не установлен - Telegram бот недоступен")
    
    return warnings

# Выводим предупреждения при импорте
if DEBUG:
    for warning in validate_config():
        print(f"[Config] Предупреждение: {warning}")
