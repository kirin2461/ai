"""Главное окно"""
import html
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel,
    QProgressBar, QFrame, QFileDialog, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QColor

from .styles_scifi import SCIFI_STYLE
from .skills_widget import SkillsWidget
from .voice_dialog import VoiceDialog

from modules.desktop_avatar import AvatarManager
from modules.tts_engine import TTSEngine, TTSConfig


class AIWorker(QThread):
    response_ready = pyqtSignal(str)

    def __init__(self, cognitive, text):
        super().__init__()
        self.cognitive = cognitive
        self.text = text

    def run(self):
        self.response_ready.emit(self.cognitive.run_cycle(self.text))


class MainWindowSciFi(QMainWindow):
    def __init__(self, cognitive):
        super().__init__()
        self.cognitive = cognitive

        self.avatar_manager = AvatarManager(cognitive)
        # Инициализируем TTS-движок
        self.tts_engine = TTSEngine(TTSConfig())

        self.setWindowTitle("◆ AI HUMANITY ◆")
        self.setMinimumSize(1000, 700)

        self._setup_ui()
        self.setStyleSheet(SCIFI_STYLE)

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(100)

        self.avatar = self.avatar_manager.create_avatar()
        self.avatar.show()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main = QHBoxLayout(central)
        main.setSpacing(15)
        main.setContentsMargins(20, 20, 20, 20)

        # Left panel
        left = QFrame()
        left.setObjectName("scifiPanel")
        left.setFixedWidth(250)
        left_layout = QVBoxLayout(left)

        self.emotion_label = QLabel("НЕЙТРАЛЬНО")
        self.emotion_label.setObjectName("headerLabel")
        left_layout.addWidget(self.emotion_label)

        self.mood_label = QLabel("Нейтральное состояние")
        self.mood_label.setStyleSheet("color: rgba(255,255,255,0.6);")
        left_layout.addWidget(self.mood_label)

        for name, attr in [("P", "p_bar"), ("A", "a_bar"), ("D", "d_bar")]:
            lbl = QLabel(name)
            lbl.setStyleSheet("color: #00d4ff;")
            left_layout.addWidget(lbl)

            bar = QProgressBar()
            bar.setRange(-100, 100)
            bar.setValue(0)
            setattr(self, attr, bar)
            left_layout.addWidget(bar)

        left_layout.addStretch()

        # TTS Toggle
        self.tts_checkbox = QCheckBox("🔊 Озвучка (XTTS v2)")
        self.tts_checkbox.setStyleSheet("color: #00d4ff; font-size: 12px;")
        self.tts_checkbox.stateChanged.connect(self._toggle_tts)
        left_layout.addWidget(self.tts_checkbox)

        self.tts_status = QLabel("TTS: Выключен")
        self.tts_status.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 10px;")
        left_layout.addWidget(self.tts_status)

        # Voice sample button
        voice_btn = QPushButton("🎤 ЗАГРУЗИТЬ ГОЛОС")
        voice_btn.clicked.connect(self._select_voice)
        voice_btn.setStyleSheet("font-size: 11px; padding: 8px;")
        left_layout.addWidget(voice_btn)

        # Voice Library button
        voice_library_btn = QPushButton("🎙️ БИБЛИОТЕКА ГОЛОСОВ")
        voice_library_btn.clicked.connect(self._open_voice_library)
        voice_library_btn.setStyleSheet("font-size: 11px; padding: 8px;")
        left_layout.addWidget(voice_library_btn)

        upload_btn = QPushButton("⬆ ЗАГРУЗИТЬ МОДЕЛЬ")
        upload_btn.clicked.connect(self._select_model)
        left_layout.addWidget(upload_btn)

        main.addWidget(left)

        # Center - chat
        center = QFrame()
        center.setObjectName("scifiPanel")
        center_layout = QVBoxLayout(center)

        self.chat = QTextEdit()
        self.chat.setObjectName("chatArea")
        self.chat.setReadOnly(True)
        center_layout.addWidget(self.chat)

        input_row = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Введи сообщение...")
        self.input_field.returnPressed.connect(self._send)
        input_row.addWidget(self.input_field)

        send_btn = QPushButton("▶")
        send_btn.clicked.connect(self._send)
        input_row.addWidget(send_btn)

        center_layout.addLayout(input_row)

        main.addWidget(center, stretch=1)

        # Right - skills
        right = QFrame()
        right.setObjectName("scifiPanel")
        right.setFixedWidth(220)
        right_layout = QVBoxLayout(right)

        self.level_label = QLabel("LVL 1")
        self.level_label.setStyleSheet(
            "color: #00d4ff; font-size: 24px; font-weight: bold;"
        )
        right_layout.addWidget(self.level_label)

        self.skills_widget = SkillsWidget(self.cognitive.skills)
        right_layout.addWidget(self.skills_widget)

        right_layout.addStretch()
        main.addWidget(right)

    def _toggle_tts(self, state):
        """Включить/выключить TTS"""
        if state == Qt.CheckState.Checked.value:
            self.tts_status.setText("TTS: Загрузка модели...")
            self.tts_status.setStyleSheet("color: #ffaa00; font-size: 10px;")
            self._init_tts_async()
        else:
            self.tts_status.setText("TTS: Выключен")
            self.tts_status.setStyleSheet(
                "color: rgba(255,255,255,0.5); font-size: 10px;"
            )

    def _init_tts_async(self):
        """Асинхронная инициализация TTS"""
        import threading

        def init():
            success = self.tts_engine.initialize()
            QTimer.singleShot(0, lambda: self._on_tts_init(success))

        threading.Thread(target=init, daemon=True).start()

    def _on_tts_init(self, success: bool):
        """Callback после инициализации TTS"""
        if success:
            self.tts_status.setText("TTS: Активен ✓")
            self.tts_status.setStyleSheet("color: #4ecca3; font-size: 10px;")
        else:
            self.tts_checkbox.setChecked(False)
            self.tts_status.setText("TTS: Ошибка загрузки")
            self.tts_status.setStyleSheet("color: #ff006e; font-size: 10px;")
            self._add_message(
                "SYSTEM",
                "Не удалось загрузить TTS. Установите: pip install TTS torch",
                "#ff006e",
            )

    def _select_voice(self):
        """Выбрать образец голоса для клонирования"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать образец голоса",
            "",
            "Audio (*.wav *.mp3 *.ogg *.flac)",
        )
        if path:
            # Устанавливаем образец в движок
            self.tts_engine.set_speaker_voice(path)
            self._add_message(
                "SYSTEM",
                f"Загружен образец голоса: {Path(path).name}",
                "#4ecca3",
            )

    def _open_voice_library(self):
        """Открыть диалог библиотеки голосов"""
        dialog = VoiceDialog(self)
        dialog.voice_selected.connect(self._on_voice_selected)
        dialog.exec()

    def _on_voice_selected(self, voice_id: str):
        """Обработка выбора голоса из библиотеки"""
        from modules.voice_manager import voice_manager

        voice_path = voice_manager.get_voice_path(voice_id)
        if voice_path:
            self.tts_engine.set_speaker_voice(voice_path)
            voice_data = voice_manager.metadata["voices"].get(voice_id, {})
            name = voice_data.get("name", voice_id)
            self._add_message(
                "SYSTEM",
                f"Голос '{name}' установлен",
                "#4ecca3",
            )

    def _select_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать модель",
            "",
            "3D (*.vrm *.glb *.obj)",
        )
        if path:
            self.avatar.hide()
            self.avatar = self.avatar_manager.create_avatar(model_path=path)
            self.avatar.show()
            self._add_message(
                "SYSTEM",
                f"Загружена модель: {Path(path).name}",
                "#4ecca3",
            )

    def _send(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self._add_message("USER", text, "#00d4ff")
        self.worker = AIWorker(self.cognitive, text)
        self.worker.response_ready.connect(self._on_response)
        self.worker.start()

    def _on_response(self, response: str):
        self._add_message("AI", response, "#ff006e")
        self.skills_widget.refresh()
        self.avatar_manager.on_response(response)

        # Если TTS инициализирован – пытаемся озвучить ответ
        try:
            self.tts_engine.speak(response)
        except Exception:
            pass

        self.worker.deleteLater()

    def _add_message(self, sender: str, text: str, color: str):
        safe = html.escape(text)
        self.chat.append(
            f'<div><span style="color:{color}">▸ {sender}</span><br>{safe}</div>'
        )

    def _update_display(self):
        state = self.cognitive.get_state()
        self.emotion_label.setText(state["emotion"].upper())
        self.mood_label.setText(state["mood"])
        self.p_bar.setValue(int(state["pad"]["pleasure"] * 100))
        self.a_bar.setValue(int(state["pad"]["arousal"] * 100))
        self.d_bar.setValue(int(state["pad"]["dominance"] * 100))
        self.level_label.setText(f"LVL {state['total_level']}")

    def closeEvent(self, event):
        """Очистка при закрытии"""
        self.tts_engine.stop()
        super().closeEvent(event)
