# 🤖 AI Humanity

**AI-компаньон с эмоциональным интеллектом, 3D аватаром и голосом**

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🚀 Быстрый старт

```bash
# Windows - просто запустите:
start.bat

# Или вручную:
pip install -r requirements.txt
python main.py
```

## ✨ Возможности

| Функция | Описание |
|---------|----------|
| 🧠 PAD эмоции | 8 типов эмоций, затухание, уверенность |
| ⚡ Прокачка | Система навыков с 5 уровнями |
| 👤 3D Аватар | VRM/GLB/OBJ на рабочем столе |
| 🔊 XTTS v2 | Клонирование голоса, 15+ языков |
| 🤖 Telegram | Бот с командами |
| 📷 FaceEmotion | Распознавание эмоций через камеру |
| 📅 Calendar | Google Calendar интеграция |
| 🎮 Sci-Fi UI | Киберпанк интерфейс |

---

## 📁 Структура проекта

```
ai-humaity/
├── core/                        # 🧠 Ядро AI (5 модулей)
│   ├── emotion_engine.py        # PAD модель эмоций
│   ├── cognitive_cycle.py       # Когнитивный цикл + GPT
│   ├── skill_system.py          # Система навыков
│   ├── safety_system.py         # Безопасность
│   └── autonomous_life.py       # Автономная жизнь
│   └── memory_manager.py  # Управление памятью и контекстом
│
├── modules/                     # 🔌 Расширения (5 модулей)
│   ├── desktop_avatar.py        # 3D аватар
│   ├── tts_engine.py            # Coqui XTTS v2
│   ├── telegram_integration.py  # Telegram бот
│   ├── face_emotion.py          # FER + OpenCV
│   └── calendar_integration.py  # Google Calendar
│
├── gui/                         # 🎨 Интерфейс (3 файла)
│   ├── main_window_scifi.py     # Главное окно
│   ├── styles_scifi.py          # Sci-Fi стили
│   └── skills_widget.py         # Виджет навыков
│
├── config/                      # ⚙️ Конфигурация
│   └── settings.py              # API ключи
│
├── main.py                      # 🚀 Точка входа
├── start.bat                    # 📦 Лаунчер Windows
├── requirements.txt             # Зависимости
└── README.md
├── utils.py            # 🛠️ Вспомогательные функции
```

---

## 🧠 Ядро (core/)

| Модуль | Описание | Ключевые функции |
|--------|----------|------------------|
| `emotion_engine.py` | PAD модель эмоций | 8 эмоций, decay, confidence |
| `cognitive_cycle.py` | Главный цикл | GPT интеграция, память, анализ |
| `skill_system.py` | Прокачка навыков | 5 уровней, XP формула |
| `safety_system.py` | Безопасность | regex фильтры, 3 режима |
| `autonomous_life.py` | Внутренняя жизнь | Случайные мысли, QTimer |

---

## 🔌 Модули (modules/)

| Модуль | Описание | Форматы/API |
|--------|----------|------------|
| `desktop_avatar.py` | 3D аватар на рабочем столе | VRM, GLB, OBJ |
| `tts_engine.py` | Синтез речи | Coqui XTTS v2, 15+ языков |
| `telegram_integration.py` | Telegram бот | asyncio, команды |
| `face_emotion.py` | Распознавание эмоций | FER, OpenCV, камера |
| `calendar_integration.py` | Google Calendar | OAuth 2.0 |

---

## 🎨 GUI (gui/)

| Файл | Описание |
|------|----------|
| `styles_scifi.py` | Sci-Fi тема с cyan неоном |
| `main_window_scifi.py` | 3-колоночный layout, чат, навыки |
| `skills_widget.py` | Карточки навыков с прогрессом |

---

## ⚙️ Настройка

### OpenAI API (опционально)
Редактируйте `config/settings.py`:
```python
OPENAI_API_KEY = "sk-..."
```

### Telegram Bot
1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Добавьте токен в `config/settings.py`:
```python
TELEGRAM_TOKEN = "123456:ABC..."
```

### Google Calendar
1. Создайте проект в [Google Cloud Console](https://console.cloud.google.com/)
2. Включите Calendar API
3. Скачайте `credentials.json` в `config/google_credentials.json`

### Клонирование голоса (TTS)
1. Запишите образец голоса (10-30 сек, WAV)
2. Загрузите через кнопку "🎤 ЗАГРУЗИТЬ ГОЛОС"

---

## 📝 Telegram команды

| Команда | Описание |
|---------|----------|
| `/start` | Начать общение |
| `/status` | Статус AI |
| `/emotion` | Текущая эмоция + PAD |
| `/skills` | Список навыков |
| `/reset` | Сброс контекста |
| `/help` | Справка |

---

## 🛠️ Требования

- Python 3.10+
- Windows / Linux / macOS
- GPU рекомендуется для TTS (CUDA)
- Веб-камера для Face Emotion

---

## 📦 Установка модулей

```bash
# Все зависимости
pip install -r requirements.txt

# Только базовые (без TTS/FaceEmotion)
pip install openai PyQt6 numpy pillow

# TTS (Coqui XTTS v2)
pip install TTS torch torchaudio pygame

# Telegram
pip install python-telegram-bot

# Face Emotion
pip install fer opencv-python tensorflow

# Google Calendar
pip install google-auth-oauthlib google-api-python-client
```

---

## 📄 Лицензия

MIT License

---

## 🙏 Благодарности

- [Coqui TTS](https://github.com/coqui-ai/TTS) — XTTS v2
- [FER](https://github.com/justinshenk/fer) — Face Emotion Recognition
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)

---

## 📦 Сборка EXE

### Используя start.bat:
```bash
# Запустите start.bat и выберите опцию [2]
start.bat
# Выберите: 2 - Собрать EXE
```

### Или вручную:
```bash
pip install pyinstaller
build.bat
# Или:
pyinstaller --onefile --windowed --icon=assets/icon.ico --name=AI_Humanity main.py
```

Собранный EXE будет в папке `dist/`

---

## 🔊 Дополнительный TTS модуль

Файл `tts_module.py` в корне проекта - альтернативный модуль TTS:

```python
from tts_module import TTSModule

tts = TTSModule()
tts.load_model()  # Загрузка XTTS v2
tts.speak("Привет, мир!")  # Синтез и воспроизведение
tts.cleanup()  # Очистка
```
