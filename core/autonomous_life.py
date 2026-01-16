"""Автономная жизнь"""
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
import random
from typing import Optional

class AutonomousLife(QObject):
    thought_changed = pyqtSignal(str)
    
    def __init__(self, cognitive_cycle):
        super().__init__()
        self.cognitive = cognitive_cycle
        self.current_thought = ""
        self._timer: Optional[QTimer] = None
        self.running = False
    
    def start(self):
        self.running = True
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(5000)
    
    def stop(self):
        self.running = False
        if self._timer:
            self._timer.stop()
    
    def _tick(self):
        if not self.running:
            return
        if random.random() < 0.3:
            thoughts = [
                "Интересно, что происходит в мире...",
                "Хочется узнать что-то новое",
                "Как там дела у пользователя?",
            ]
            self.current_thought = random.choice(thoughts)
            self.thought_changed.emit(self.current_thought)
