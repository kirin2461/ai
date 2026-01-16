"""Распознавание эмоций по лицу"""
import threading
import queue
from typing import Optional, Callable, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
import time


class FaceEmotionType(Enum):
    """Типы эмоций, распознаваемые FER"""
    ANGRY = "angry"
    DISGUST = "disgust"
    FEAR = "fear"
    HAPPY = "happy"
    SAD = "sad"
    SURPRISE = "surprise"
    NEUTRAL = "neutral"


# Маппинг FER эмоций на PAD модель (pleasure, arousal, dominance)
FER_TO_PAD = {
    FaceEmotionType.HAPPY: (0.8, 0.5, 0.6),
    FaceEmotionType.SAD: (-0.7, -0.4, -0.5),
    FaceEmotionType.ANGRY: (-0.6, 0.8, 0.7),
    FaceEmotionType.FEAR: (-0.7, 0.7, -0.6),
    FaceEmotionType.SURPRISE: (0.3, 0.8, 0.0),
    FaceEmotionType.DISGUST: (-0.6, 0.2, 0.3),
    FaceEmotionType.NEUTRAL: (0.0, 0.0, 0.0),
}


@dataclass
class FaceEmotionConfig:
    """Конфигурация распознавания эмоций"""
    camera_index: int = 0
    detection_interval: float = 0.5  # Секунды между детекциями
    min_confidence: float = 0.3
    mirror: bool = True
    show_preview: bool = False
    face_cascade_path: str = None  # None = использовать дефолтный


@dataclass
class EmotionResult:
    """Результат распознавания эмоции"""
    emotion: FaceEmotionType
    confidence: float
    all_emotions: Dict[str, float]
    face_box: Tuple[int, int, int, int]  # x, y, w, h
    timestamp: float


class FaceEmotionDetector:
    """Детектор эмоций по лицу на базе FER и OpenCV"""
    
    def __init__(self, config: FaceEmotionConfig = None):
        self.config = config or FaceEmotionConfig()
        self.fer_detector = None
        self.cap = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._result_queue = queue.Queue(maxsize=10)
        self._on_emotion_callback: Optional[Callable[[EmotionResult], None]] = None
        self._last_result: Optional[EmotionResult] = None
        self._is_initialized = False
    
    def set_emotion_callback(self, callback: Callable[[EmotionResult], None]):
        """Установить callback для получения эмоций"""
        self._on_emotion_callback = callback
    
    def initialize(self) -> bool:
        """Инициализация FER и OpenCV"""
        if self._is_initialized:
            return True
        
        try:
            from fer import FER
            import cv2
            
            print("[FaceEmotion] Инициализация детектора...")
            
            # Инициализируем FER
            self.fer_detector = FER(mtcnn=True)
            
            # Проверяем камеру
            self.cap = cv2.VideoCapture(self.config.camera_index)
            if not self.cap.isOpened():
                print(f"[FaceEmotion] Не удалось открыть камеру {self.config.camera_index}")
                return False
            
            self._is_initialized = True
            print("[FaceEmotion] Инициализация успешна!")
            return True
            
        except ImportError as e:
            print(f"[FaceEmotion] Не установлены зависимости: {e}")
            print("[FaceEmotion] Выполните: pip install fer opencv-python tensorflow")
            return False
        except Exception as e:
            print(f"[FaceEmotion] Ошибка инициализации: {e}")
            return False
    
    def start(self) -> bool:
        """Запустить распознавание в фоновом потоке"""
        if not self._is_initialized:
            if not self.initialize():
                return False
        
        if self._running:
            return True
        
        self._running = True
        self._thread = threading.Thread(target=self._detection_loop, daemon=True)
        self._thread.start()
        print("[FaceEmotion] Распознавание запущено")
        return True
    
    def stop(self):
        """Остановить распознавание"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self.cap:
            self.cap.release()
        print("[FaceEmotion] Распознавание остановлено")
    
    def _detection_loop(self):
        """Цикл распознавания эмоций"""
        import cv2
        
        while self._running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                # Зеркалирование
                if self.config.mirror:
                    frame = cv2.flip(frame, 1)
                
                # Распознавание эмоций
                result = self.fer_detector.detect_emotions(frame)
                
                if result and len(result) > 0:
                    # Берём первое обнаруженное лицо
                    face_data = result[0]
                    emotions = face_data['emotions']
                    box = face_data['box']
                    
                    # Находим доминирующую эмоцию
                    dominant = max(emotions, key=emotions.get)
                    confidence = emotions[dominant]
                    
                    if confidence >= self.config.min_confidence:
                        emotion_type = FaceEmotionType(dominant)
                        
                        emotion_result = EmotionResult(
                            emotion=emotion_type,
                            confidence=confidence,
                            all_emotions=emotions,
                            face_box=tuple(box),
                            timestamp=time.time()
                        )
                        
                        self._last_result = emotion_result
                        
                        # Отправляем в очередь
                        try:
                            self._result_queue.put_nowait(emotion_result)
                        except queue.Full:
                            pass
                        
                        # Вызываем callback
                        if self._on_emotion_callback:
                            self._on_emotion_callback(emotion_result)
                
                # Показываем превью если включено
                if self.config.show_preview:
                    self._draw_preview(frame, result)
                    cv2.imshow('Face Emotion', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                time.sleep(self.config.detection_interval)
                
            except Exception as e:
                print(f"[FaceEmotion] Ошибка в цикле: {e}")
                time.sleep(1.0)
        
        if self.config.show_preview:
            cv2.destroyAllWindows()
    
    def _draw_preview(self, frame, results):
        """Отрисовка превью с распознанными эмоциями"""
        import cv2
        
        if not results:
            return
        
        for face in results:
            box = face['box']
            emotions = face['emotions']
            dominant = max(emotions, key=emotions.get)
            confidence = emotions[dominant]
            
            # Рисуем рамку вокруг лица
            x, y, w, h = box
            color = (0, 255, 0) if confidence > 0.5 else (0, 255, 255)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            
            # Подпись с эмоцией
            label = f"{dominant}: {confidence:.0%}"
            cv2.putText(frame, label, (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    def get_latest_emotion(self) -> Optional[EmotionResult]:
        """Получить последнюю распознанную эмоцию"""
        return self._last_result
    
    def get_emotion_as_pad(self) -> Optional[Tuple[float, float, float]]:
        """Получить эмоцию в формате PAD"""
        if self._last_result:
            return FER_TO_PAD.get(self._last_result.emotion, (0, 0, 0))
        return None


class FaceEmotionManager:
    """Менеджер распознавания эмоций для AI Humanity"""
    
    def __init__(self, cognitive_cycle=None):
        self.cognitive = cognitive_cycle
        self.detector: Optional[FaceEmotionDetector] = None
        self.enabled = False
        self._sync_to_ai = True
    
    def initialize(self, config: FaceEmotionConfig = None) -> bool:
        """Инициализировать детектор"""
        self.detector = FaceEmotionDetector(config)
        success = self.detector.initialize()
        if success:
            self.detector.set_emotion_callback(self._on_emotion_detected)
        return success
    
    def start(self) -> bool:
        """Запустить распознавание"""
        if self.detector:
            self.enabled = self.detector.start()
            return self.enabled
        return False
    
    def stop(self):
        """Остановить распознавание"""
        if self.detector:
            self.detector.stop()
        self.enabled = False
    
    def _on_emotion_detected(self, result: EmotionResult):
        """Callback при распознавании эмоции"""
        if self._sync_to_ai and self.cognitive:
            # Синхронизируем эмоцию пользователя с AI
            # AI может "зеркалить" или реагировать на эмоции пользователя
            pad = FER_TO_PAD.get(result.emotion, (0, 0, 0))
            # Применяем с небольшой интенсивностью
            self.cognitive.emotion.update_pad(
                pleasure=self.cognitive.emotion.pad.pleasure + pad[0] * 0.1,
                arousal=self.cognitive.emotion.pad.arousal + pad[1] * 0.1,
                dominance=self.cognitive.emotion.pad.dominance + pad[2] * 0.1
            )
    
    def toggle_sync(self) -> bool:
        """Переключить синхронизацию эмоций с AI"""
        self._sync_to_ai = not self._sync_to_ai
        return self._sync_to_ai
    
    def get_user_emotion(self) -> Optional[str]:
        """Получить текущую эмоцию пользователя"""
        if self.detector and self.detector.get_latest_emotion():
            return self.detector.get_latest_emotion().emotion.value
        return None
