"""Система безопасности"""
from enum import Enum
from typing import Tuple
import re

class SafetyMode(Enum):
    STRICT = "strict"
    NORMAL = "normal"
    PERMISSIVE = "permissive"

class SafetySystem:
    BLOCKED_PATTERNS = [
        r"(взлом|хакер|ddos|exploit)",
        r"(бомб|оруж|убить|насилие)",
        r"(нарко|наркотик|героин|кокаин)",
    ]
    
    def __init__(self, mode: SafetyMode = SafetyMode.NORMAL):
        self.mode = mode
        self.violations = 0
    
    def check_input(self, text: str) -> Tuple[bool, str]:
        text_lower = text.lower()
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, text_lower):
                self.violations += 1
                return False, "Запрос содержит недопустимый контент"
        return True, "OK"
    
    def check_output(self, text: str) -> Tuple[bool, str]:
        if self.mode == SafetyMode.STRICT:
            if len(text) > 5000:
                return False, "Ответ слишком длинный"
        return True, "OK"
    
    def get_status(self) -> dict:
        return {"mode": self.mode.value, "violations": self.violations}
