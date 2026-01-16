"""TTS Engine - Multi-backend Text-to-Speech with fallback support

Supports:

- Coqui XTTS v2 (Python 3.9-3.11, with voice cloning)
- pyttsx3 (Python 3.12+, basic TTS)

"""

import os
import sys
import queue
import logging
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Configuration from environment
TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "ru")
TTS_SPEED = float(os.getenv("TTS_SPEED", "1.0"))


class TTSStatus(Enum):
    IDLE = "idle"
    LOADING = "loading"
    GENERATING = "generating"
    PLAYING = "playing"
    ERROR = "error"


class TTSBackend(Enum):
    COQUI = "coqui"      # Coqui XTTS v2 (Python 3.9-3.11)
    PYTTSX3 = "pyttsx3"  # Offline, system voices
    NONE = "none"        # No TTS available


@dataclass
class TTSConfig:
    """TTS Configuration"""

    language: str = field(default_factory=lambda: TTS_LANGUAGE)
    speed: float = field(default_factory=lambda: TTS_SPEED)
    speaker_wav: Optional[str] = None
    output_dir: str = "output"


class TTSEngine:
    """Multi-backend TTS Engine with automatic fallback"""

    def __init__(self, config: TTSConfig = None):
        self.config = config or TTSConfig()
        self._status = TTSStatus.IDLE
        self._backend = TTSBackend.NONE
        self._engine = None
        self._is_initialized = False
        self._status_callback: Optional[Callable[[TTSStatus], None]] = None
        self._audio_queue = queue.Queue()
        self._stop_playback = False

        os.makedirs(self.config.output_dir, exist_ok=True)

    def _update_status(self, status: TTSStatus):
        self._status = status
        if self._status_callback:
            self._status_callback(status)

    def set_status_callback(self, callback: Callable[[TTSStatus], None]):
        self._status_callback = callback

    @property
    def status(self) -> TTSStatus:
        return self._status

    @property
    def backend(self) -> TTSBackend:
        return self._backend

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

    def initialize(self) -> bool:
        """Initialize TTS with automatic backend selection"""
        self._update_status(TTSStatus.LOADING)

        # Try Coqui TTS first (best quality, voice cloning)
        if self._try_init_coqui():
            return True

        # Fallback to pyttsx3 (offline, works on most Python versions)
        if self._try_init_pyttsx3():
            return True

        logger.error("No TTS backend available!")
        self._update_status(TTSStatus.ERROR)
        return False

    def _try_init_coqui(self) -> bool:
        """Try to initialize Coqui TTS (requires Python 3.9-3.11)"""
        try:
            py_version = sys.version_info
            if py_version >= (3, 12):
                logger.info("Python 3.12+ detected, Coqui TTS not supported")
                return False

            from TTS.api import TTS
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Initializing Coqui TTS on {device}...")

            self._engine = TTS(
                "tts_models/multilingual/multi-dataset/xtts_v2"
            ).to(device)

            self._backend = TTSBackend.COQUI
            self._is_initialized = True
            self._update_status(TTSStatus.IDLE)
            logger.info("Coqui TTS initialized successfully")
            return True

        except ImportError:
            logger.info("Coqui TTS not installed")
        except Exception as e:
            logger.warning(f"Coqui TTS init failed: {e}")
        return False

    def _try_init_pyttsx3(self) -> bool:
        """Try to initialize pyttsx3 (offline)"""
        try:
            import pyttsx3

            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", int(150 * self.config.speed))

            # Try to set Russian voice if available
            voices = self._engine.getProperty("voices")
            for voice in voices:
                langs = getattr(voice, "languages", [])
                if any("ru" in str(lang).lower() for lang in langs) or "russian" in voice.name.lower():
                    self._engine.setProperty("voice", voice.id)
                    break

            self._backend = TTSBackend.PYTTSX3
            self._is_initialized = True
            self._update_status(TTSStatus.IDLE)
            logger.info("pyttsx3 initialized successfully")
            return True

        except ImportError:
            logger.info("pyttsx3 not installed")
        except Exception as e:
            logger.warning(f"pyttsx3 init failed: {e}")
        return False

    def synthesize(self, text: str, output_path: str = None) -> Optional[str]:
        """Synthesize speech from text"""
        if not self._is_initialized:
            if not self.initialize():
                return None

        self._update_status(TTSStatus.GENERATING)

        if output_path is None:
            output_path = os.path.join(self.config.output_dir, "speech.wav")

        try:
            if self._backend == TTSBackend.COQUI:
                return self._synth_coqui(text, output_path)
            elif self._backend == TTSBackend.PYTTSX3:
                return self._synth_pyttsx3(text, output_path)
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            self._update_status(TTSStatus.ERROR)
            return None

        return None

    def _synth_coqui(self, text: str, output_path: str) -> str:
        """Synthesize using Coqui TTS"""
        if self.config.speaker_wav and os.path.exists(self.config.speaker_wav):
            self._engine.tts_to_file(
                text=text,
                speaker_wav=self.config.speaker_wav,
                language=self.config.language,
                file_path=output_path,
            )
        else:
            self._engine.tts_to_file(
                text=text,
                language=self.config.language,
                file_path=output_path,
            )

        self._update_status(TTSStatus.IDLE)
        return output_path

    def _synth_pyttsx3(self, text: str, output_path: str) -> str:
        """Synthesize using pyttsx3"""
        self._engine.save_to_file(text, output_path)
        self._engine.runAndWait()
        self._update_status(TTSStatus.IDLE)
        return output_path

    def speak(self, text: str):
        """Synthesize and play speech (не влияет на чат при ошибке)"""
        audio_path = self.synthesize(text)
        if not audio_path:
            logger.error("Synthesis failed (no audio path)")
            return

        try:
            self.play_audio(audio_path)
        except Exception as e:
            logger.error(f"Playback failed: {e}")
            self._update_status(TTSStatus.ERROR)

    def play_audio(self, audio_path: str):
        """Play audio file"""
        if not os.path.exists(audio_path):
            return

        self._update_status(TTSStatus.PLAYING)

        try:
            import pygame

            pygame.mixer.init()
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
        except ImportError:
            # Fallback to system player
            import platform

            system = platform.system()
            if system == "Windows":
                os.startfile(audio_path)  # type: ignore
            elif system == "Darwin":
                os.system(f"afplay {audio_path}")
            else:
                os.system(f"aplay {audio_path}")
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
        finally:
            self._update_status(TTSStatus.IDLE)

    def set_speaker_voice(self, wav_path: str):
        """Set speaker voice for cloning (Coqui only)"""
        if os.path.exists(wav_path):
            self.config.speaker_wav = wav_path
            logger.info(f"Speaker voice set: {wav_path}")
        else:
            logger.warning(f"Voice file not found: {wav_path}")

    def set_language(self, language: str):
        """Set synthesis language"""
        self.config.language = language
        logger.info(f"Language set: {language}")

    def stop(self):
        """Stop playback"""
        self._stop_playback = True
        try:
            import pygame

            pygame.mixer.music.stop()
        except Exception:
            pass

    def get_backend_info(self) -> str:
        """Get information about current TTS backend"""
        info = {
            TTSBackend.COQUI: "Coqui XTTS v2 (voice cloning supported)",
            TTSBackend.PYTTSX3: "pyttsx3 (offline, system voices)",
            TTSBackend.NONE: "No TTS backend available",
        }
        return info.get(self._backend, "Unknown")


# Global instance
_tts_engine: Optional[TTSEngine] = None


def get_tts_engine() -> TTSEngine:
    """Get or create global TTS engine instance"""
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = TTSEngine()
    return _tts_engine
