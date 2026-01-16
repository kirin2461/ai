"""Виджет навыков"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QFrame
from PyQt6.QtCore import Qt

class SkillsWidget(QWidget):
    def __init__(self, skill_system, parent=None):
        super().__init__(parent)
        self.skill_system = skill_system
        self._setup_ui()
    
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.refresh()
    
    def refresh(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for skill in list(self.skill_system.skills.values())[:5]:
            card = QFrame()
            card.setStyleSheet("background: rgba(0,40,60,0.5); border-radius: 5px; padding: 5px;")
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(4)
            
            name = QLabel(f"{skill.name} - {skill.level.value}")
            name.setStyleSheet("color: #00d4ff; font-size: 11px;")
            card_layout.addWidget(name)
            
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(min(int(skill.experience), 100))
            bar.setFixedHeight(6)
            bar.setTextVisible(False)
            card_layout.addWidget(bar)
            
            self.layout.addWidget(card)
