"""Voice Dialog - Диалог управления голосами для клонирования TTS"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QLineEdit,
    QFileDialog, QMessageBox, QWidget, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
import sys
sys.path.append('..')
from modules.voice_manager import voice_manager


class VoiceItemWidget(QFrame):
    """Виджет элемента голоса"""
    
    def __init__(self, voice_data: dict, parent=None):
        super().__init__(parent)
        self.voice_id = voice_data['id']
        self.voice_data = voice_data
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        info = QVBoxLayout()
        self.name_label = QLabel(self.voice_data['name'])
        self.name_label.setStyleSheet("font-weight: bold; color: #00ffff;")
        desc = self.voice_data.get('description', '') or "Нет описания"
        self.desc_label = QLabel(desc)
        self.desc_label.setStyleSheet("color: #888; font-size: 11px;")
        info.addWidget(self.name_label)
        info.addWidget(self.desc_label)
        layout.addLayout(info, 1)
        
        if self.voice_data.get('is_default'):
            star = QLabel("★")
            star.setStyleSheet("color: #ffd700; font-size: 16px;")
            layout.addWidget(star)


class VoiceDialog(QDialog):
    """Диалог управления голосами"""
    
    voice_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎙️ Управление голосами")
        self.setMinimumSize(500, 400)
        self._setup_ui()
        self._load_voices()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        title = QLabel("🎙️ Библиотека голосов")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00ffff;")
        layout.addWidget(title)
        
        add_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Имя голоса...")
        add_layout.addWidget(self.name_input, 1)
        
        self.add_btn = QPushButton("➕ Добавить")
        self.add_btn.clicked.connect(self._add_voice)
        add_layout.addWidget(self.add_btn)
        layout.addLayout(add_layout)
        
        self.voice_list = QListWidget()
        layout.addWidget(self.voice_list, 1)
        
        btn_layout = QHBoxLayout()
        self.set_default_btn = QPushButton("★ По умолчанию")
        self.set_default_btn.clicked.connect(self._set_default)
        btn_layout.addWidget(self.set_default_btn)
        
        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.clicked.connect(self._delete_voice)
        btn_layout.addWidget(self.delete_btn)
        
        self.select_btn = QPushButton("✔️ Выбрать")
        self.select_btn.clicked.connect(self._select_voice)
        btn_layout.addWidget(self.select_btn)
        layout.addLayout(btn_layout)
        
    def _load_voices(self):
        self.voice_list.clear()
        for v in voice_manager.get_voices():
            item = QListWidgetItem()
            widget = VoiceItemWidget(v)
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, v['id'])
            self.voice_list.addItem(item)
            self.voice_list.setItemWidget(item, widget)
            
    def _add_voice(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите имя")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Выберите аудио", "", "Audio (*.wav *.mp3 *.ogg *.flac)")
        if path and voice_manager.add_voice(path, name):
            self.name_input.clear()
            self._load_voices()
            
    def _get_selected_id(self):
        item = self.voice_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None
        
    def _set_default(self):
        vid = self._get_selected_id()
        if vid:
            voice_manager.set_default(vid)
            self._load_voices()
            
    def _delete_voice(self):
        vid = self._get_selected_id()
        if vid:
            voice_manager.remove_voice(vid)
            self._load_voices()
            
    def _select_voice(self):
        vid = self._get_selected_id()
        if vid:
            self.voice_selected.emit(vid)
            self.accept()
