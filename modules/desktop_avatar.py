"""3D Аватар на рабочем столе"""
import sys
import math
import random
import time
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List

from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QTransform

def get_asset_path(relative_path: str) -> Path:
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent.parent
    return base / relative_path

class AvatarState(Enum):
    IDLE = "idle"
    WALKING_LEFT = "walking_left"
    WALKING_RIGHT = "walking_right"
    WAVING = "waving"
    HAPPY = "happy"
    SAD = "sad"
    TALKING = "talking"

@dataclass
class AvatarConfig:
    model_path: str = ""
    scale: float = 1.0
    speed: float = 100
    allow_drag: bool = True

class SpriteAvatar:
    def __init__(self):
        self.sprites: Dict[str, List[QPixmap]] = {}
        self.current_state = AvatarState.IDLE
        self.current_frame = 0
        self.flipped = False
        self._create_default_sprites()
    
    def _create_default_sprites(self):
        size = 64
        for state in AvatarState:
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QColor(255, 200, 150))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(16, 20, 32, 40)
            painter.drawEllipse(12, 2, 40, 35)
            painter.setBrush(QColor(50, 50, 50))
            painter.drawEllipse(22, 12, 6, 6)
            painter.drawEllipse(38, 12, 6, 6)
            painter.end()
            self.sprites[state.value] = [pixmap]
    
    def get_current_frame(self) -> QPixmap:
        state_sprites = self.sprites.get(self.current_state.value, [])
        if not state_sprites:
            return QPixmap()
        frame = state_sprites[self.current_frame % len(state_sprites)]
        if self.flipped:
            return frame.transformed(QTransform().scale(-1, 1))
        return frame

class DesktopAvatar(QWidget):
    clicked = pyqtSignal()
    
    def __init__(self, config: AvatarConfig = None, parent=None):
        super().__init__(parent)
        self.config = config or AvatarConfig()
        self.state = AvatarState.IDLE
        self.target_position = None
        self.is_dragging = False
        self.drag_offset = QPoint()
        self.sprite_avatar = SpriteAvatar()
        self.avatar_size = 128
        
        app = QApplication.instance()
        if app and app.primaryScreen():
            geom = app.primaryScreen().geometry()
            self.screen_width = geom.width()
            self.screen_height = geom.height()
        else:
            self.screen_width, self.screen_height = 1920, 1080
        
        self.avatar_x = float(self.screen_width // 2)
        self.avatar_y = float(self.screen_height - 80 - self.avatar_size)
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self.avatar_size, self.avatar_size)
        self.move(int(self.avatar_x), int(self.avatar_y))
        
        self.sprite_label = QLabel(self)
        self.sprite_label.setFixedSize(self.avatar_size, self.avatar_size)
        self._update_sprite()
        
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self._update_position)
        self.move_timer.start(16)
        
        self.behavior_timer = QTimer(self)
        self.behavior_timer.timeout.connect(self._decide_behavior)
        self.behavior_timer.start(3000)
    
    def _update_sprite(self):
        pixmap = self.sprite_avatar.get_current_frame()
        scaled = pixmap.scaled(self.avatar_size, self.avatar_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        self.sprite_label.setPixmap(scaled)
    
    def _update_position(self):
        if self.is_dragging or not self.target_position:
            return
        dx = self.target_position[0] - self.avatar_x
        distance = abs(dx)
        if distance < 5:
            self.target_position = None
            self.state = AvatarState.IDLE
            self._update_sprite()
        else:
            speed = self.config.speed / 60
            self.avatar_x += (1 if dx > 0 else -1) * speed
            self.sprite_avatar.flipped = dx < 0
            self._update_sprite()
        self.move(int(self.avatar_x), int(self.avatar_y))
    
    def _decide_behavior(self):
        if self.is_dragging or self.state != AvatarState.IDLE:
            return
        if random.random() < 0.4:
            new_x = random.randint(100, self.screen_width - 200)
            self.target_position = [float(new_x), self.avatar_y]
            self.state = AvatarState.WALKING_RIGHT if new_x > self.avatar_x else AvatarState.WALKING_LEFT
    
    def walk_to(self, x: int):
        self.target_position = [float(x), self.avatar_y]
    
    def wave(self):
        self.state = AvatarState.WAVING
        self._update_sprite()
        QTimer.singleShot(2000, lambda: setattr(self, 'state', AvatarState.IDLE) or self._update_sprite())
    
    def talk(self, duration: float = 3.0):
        self.state = AvatarState.TALKING
        self._update_sprite()
        QTimer.singleShot(int(duration * 1000), lambda: setattr(self, 'state', AvatarState.IDLE) or self._update_sprite())
    
    def set_emotion(self, emotion: str):
        emotion_map = {'радость': AvatarState.HAPPY, 'грусть': AvatarState.SAD}
        self.state = emotion_map.get(emotion, AvatarState.IDLE)
        self._update_sprite()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.config.allow_drag:
            self.is_dragging = True
            self.drag_offset = event.pos()
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            new_pos = self.mapToGlobal(event.pos()) - self.drag_offset
            self.avatar_x, self.avatar_y = float(new_pos.x()), float(new_pos.y())
            self.move(new_pos)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
        super().mouseReleaseEvent(event)

class AvatarManager:
    def __init__(self, cognitive_cycle=None):
        self.cognitive = cognitive_cycle
        self.avatar: Optional[DesktopAvatar] = None
    
    def create_avatar(self, model_path: str = None, scale: float = 1.0) -> DesktopAvatar:
        config = AvatarConfig(model_path=model_path or "", scale=scale)
        self.avatar = DesktopAvatar(config=config)
        return self.avatar
    
    def on_response(self, response: str):
        if self.avatar:
            self.avatar.talk(min(len(response) * 0.05, 5.0))
    
    def show(self):
        if self.avatar:
            self.avatar.show()
