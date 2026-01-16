"""Voice Manager - Управление голосовыми семплами для клонирования TTS"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class VoiceManager:
    """Менеджер голосовых семплов для клонирования голоса"""
    
    SUPPORTED_FORMATS = ['.wav', '.mp3', '.ogg', '.flac', '.m4a']
    
    def __init__(self, voices_dir: str = "voices"):
        self.voices_dir = Path(voices_dir)
        self.metadata_file = self.voices_dir / "voices_metadata.json"
        self.current_voice: Optional[str] = None
        self._ensure_dirs()
        self._load_metadata()
        
    def _ensure_dirs(self):
        """Создание необходимых директорий"""
        self.voices_dir.mkdir(parents=True, exist_ok=True)
        
    def _load_metadata(self):
        """Загрузка метаданных голосов"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {"voices": {}, "default_voice": None}
            self._save_metadata()
            
    def _save_metadata(self):
        """Сохранение метаданных"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            
    def add_voice(self, audio_path: str, name: str, description: str = "") -> bool:
        """
        Добавление нового голоса
        
        Args:
            audio_path: Путь к аудиофайлу
            name: Имя голоса
            description: Описание
            
        Returns:
            True если успешно
        """
        src = Path(audio_path)
        
        if not src.exists():
            print(f"[ОШИБКА] Файл не найден: {audio_path}")
            return False
            
        if src.suffix.lower() not in self.SUPPORTED_FORMATS:
            print(f"[ОШИБКА] Неподдерживаемый формат: {src.suffix}")
            return False
            
        voice_id = self._generate_id(name)
        voice_dir = self.voices_dir / voice_id
        voice_dir.mkdir(exist_ok=True)
        
        dest = voice_dir / f"sample{src.suffix}"
        shutil.copy2(src, dest)
        
        self.metadata["voices"][voice_id] = {
            "name": name,
            "description": description,
            "file": str(dest),
            "format": src.suffix,
            "added_at": datetime.now().isoformat(),
            "is_default": len(self.metadata["voices"]) == 0
        }
        
        if self.metadata["voices"][voice_id]["is_default"]:
            self.metadata["default_voice"] = voice_id
            
        self._save_metadata()
        print(f"[УСПЕХ] Голос '{name}' добавлен")
        return True
        
    def _generate_id(self, name: str) -> str:
        """Генерация уникального ID"""
        base = name.lower().replace(' ', '_')
        base = ''.join(c for c in base if c.isalnum() or c == '_')
        
        if base in self.metadata["voices"]:
            i = 1
            while f"{base}_{i}" in self.metadata["voices"]:
                i += 1
            base = f"{base}_{i}"
        return base
        
    def remove_voice(self, voice_id: str) -> bool:
        """Удаление голоса"""
        if voice_id not in self.metadata["voices"]:
            return False
            
        voice_dir = self.voices_dir / voice_id
        if voice_dir.exists():
            shutil.rmtree(voice_dir)
            
        del self.metadata["voices"][voice_id]
        
        if self.metadata["default_voice"] == voice_id:
            voices = list(self.metadata["voices"].keys())
            self.metadata["default_voice"] = voices[0] if voices else None
            
        self._save_metadata()
        return True
        
    def get_voices(self) -> List[Dict]:
        """Получение списка всех голосов"""
        return [
            {"id": vid, **vdata}
            for vid, vdata in self.metadata["voices"].items()
        ]
        
    def get_voice_path(self, voice_id: str = None) -> Optional[str]:
        """Получение пути к файлу голоса"""
        vid = voice_id or self.metadata.get("default_voice")
        if vid and vid in self.metadata["voices"]:
            return self.metadata["voices"][vid]["file"]
        return None
        
    def set_default(self, voice_id: str) -> bool:
        """Установка голоса по умолчанию"""
        if voice_id not in self.metadata["voices"]:
            return False
            
        for vid in self.metadata["voices"]:
            self.metadata["voices"][vid]["is_default"] = (vid == voice_id)
            
        self.metadata["default_voice"] = voice_id
        self._save_metadata()
        return True
        
    def get_default_voice(self) -> Optional[Dict]:
        """Получение голоса по умолчанию"""
        vid = self.metadata.get("default_voice")
        if vid and vid in self.metadata["voices"]:
            return {"id": vid, **self.metadata["voices"][vid]}
        return None


voice_manager = VoiceManager()
