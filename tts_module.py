"""TTS Module - Coqui XTTS v2 интеграция для AI Humanity"""

import os
import torch
import pygame
from TTS.api import TTS
from config import Config


class TTSModule:
    """Модуль синтеза речи на базе Coqui XTTS v2"""
    
    def __init__(self):
        self.config = Config()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tts = None
        self.output_path = "output/speech.wav"
        self._init_pygame()
        
    def _init_pygame(self):
        """Инициализация pygame для воспроизведения аудио"""
        pygame.mixer.init()
        
    def load_model(self, model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"):
        """Загрузка модели XTTS v2"""
        try:
            print(f"[ЗАГРУЗКА] Инициализация TTS модели на {self.device}...")
            self.tts = TTS(model_name).to(self.device)
            print("[УСПЕХ] TTS модель загружена")
            return True
        except Exception as e:
            print(f"[ОШИБКА] Не удалось загрузить TTS: {e}")
            return False
            
    def synthesize(self, text: str, speaker_wav: str = None, language: str = "ru") -> str:
        """
        Синтез речи из текста
        
        Args:
            text: Текст для синтеза
            speaker_wav: Путь к референсному аудио для клонирования голоса
            language: Язык (по умолчанию русский)
            
        Returns:
            Путь к сгенерированному аудиофайлу
        """
        if not self.tts:
            self.load_model()
            
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        
        try:
            if speaker_wav:
                self.tts.tts_to_file(
                    text=text,
                    speaker_wav=speaker_wav,
                    language=language,
                    file_path=self.output_path
                )
            else:
                self.tts.tts_to_file(
                    text=text,
                    language=language,
                    file_path=self.output_path
                )
            return self.output_path
        except Exception as e:
            print(f"[ОШИБКА] Синтез не удался: {e}")
            return None
            
    def play_audio(self, audio_path: str = None):
        """Воспроизведение аудиофайла"""
        path = audio_path or self.output_path
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
                
    def speak(self, text: str, speaker_wav: str = None):
        """Синтез и воспроизведение речи"""
        audio = self.synthesize(text, speaker_wav)
        if audio:
            self.play_audio(audio)
            
    def cleanup(self):
        """Очистка ресурсов"""
        pygame.mixer.quit()
        if os.path.exists(self.output_path):
            os.remove(self.output_path)


if __name__ == "__main__":
    tts = TTSModule()
    tts.load_model()
    tts.speak("Привет! Я AI Humanity - ваш интеллектуальный помощник.")
    tts.cleanup()
