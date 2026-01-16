"""PAD модель эмоций"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Tuple
import math

class EmotionType(Enum):
    NEUTRAL = "нейтрально"
    JOY = "радость"
    SADNESS = "грусть"
    ANGER = "гнев"
    FEAR = "страх"
    SURPRISE = "удивление"
    DISGUST = "отвращение"
    INTEREST = "интерес"

@dataclass
class PADState:
    pleasure: float = 0.0
    arousal: float = 0.0
    dominance: float = 0.0

class EmotionEngine:
    EMOTION_MAP = {
        EmotionType.JOY: (0.8, 0.5, 0.6),
        EmotionType.SADNESS: (-0.7, -0.4, -0.5),
        EmotionType.ANGER: (-0.6, 0.8, 0.7),
        EmotionType.FEAR: (-0.7, 0.7, -0.6),
        EmotionType.SURPRISE: (0.3, 0.8, 0.0),
        EmotionType.DISGUST: (-0.6, 0.2, 0.3),
        EmotionType.INTEREST: (0.5, 0.6, 0.3),
        EmotionType.NEUTRAL: (0.0, 0.0, 0.0),
    }
    
    def __init__(self):
        self.pad = PADState()
        self.history = []
        self.decay_rate = 0.95
    
    def update_pad(self, pleasure=None, arousal=None, dominance=None):
        if pleasure is not None:
            self.pad.pleasure = max(-1, min(1, pleasure))
        if arousal is not None:
            self.pad.arousal = max(-1, min(1, arousal))
        if dominance is not None:
            self.pad.dominance = max(-1, min(1, dominance))
    
    def apply_stimulus(self, emotion: EmotionType, intensity: float = 0.5):
        target = self.EMOTION_MAP.get(emotion, (0, 0, 0))
        self.pad.pleasure += target[0] * intensity * 0.3
        self.pad.arousal += target[1] * intensity * 0.3
        self.pad.dominance += target[2] * intensity * 0.3
        self.pad.pleasure = max(-1, min(1, self.pad.pleasure))
        self.pad.arousal = max(-1, min(1, self.pad.arousal))
        self.pad.dominance = max(-1, min(1, self.pad.dominance))
    
    def decay(self):
        self.pad.pleasure *= self.decay_rate
        self.pad.arousal *= self.decay_rate
        self.pad.dominance *= self.decay_rate
    
    def get_dominant_emotion(self) -> Tuple[EmotionType, float]:
        current = (self.pad.pleasure, self.pad.arousal, self.pad.dominance)
        best_emotion = EmotionType.NEUTRAL
        best_dist = float('inf')
        for emotion, target in self.EMOTION_MAP.items():
            dist = math.sqrt(sum((a-b)**2 for a,b in zip(current, target)))
            if dist < best_dist:
                best_dist = dist
                best_emotion = emotion
        confidence = max(0, 1 - best_dist/2)
        return best_emotion, confidence
    
    def get_mood_description(self) -> str:
        p, a, d = self.pad.pleasure, self.pad.arousal, self.pad.dominance
        if p > 0.3 and a > 0.3:
            return "Энергичное и позитивное настроение"
        elif p > 0.3 and a < -0.3:
            return "Спокойное и довольное состояние"
        elif p < -0.3 and a > 0.3:
            return "Напряжённое состояние"
        elif p < -0.3 and a < -0.3:
            return "Подавленное настроение"
        return "Нейтральное состояние"
