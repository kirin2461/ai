"""Анализатор текста и генератор ответов без LLM."""

import re
import operator
from typing import Optional, List, Dict, Any


class TextAnalyzer:
    """Анализирует входной текст и извлекает структуру."""

    def __init__(self):
        # Паттерны для распознавания типов запросов
        self.patterns = {
            "math": r"(?:сколько|чему равно|посчитай)?\s*(\d+)\s*([+\-*/])\s*(\d+)",
            "definition": r"(?:что такое|что значит|объясни|расскажи про)\s+(.+)",
            "how_to": r"(?:как|каким образом)\s+(.+)",
            "why": r"(?:почему|зачем|отчего)\s+(.+)",
            "when": r"(?:когда)\s+(.+)",
            "where": r"(?:где|куда|откуда)\s+(.+)",
            "who": r"(?:кто такой|кто такая|кто такие|кто)\s+(.+)",
            "compare": r"(?:сравни|чем отличается|разница между)\s+(.+)",
            "list": r"(?:перечисли|назови|какие бывают)\s+(.+)",
        }

    def analyze(self, text: str) -> Dict[str, Any]:
        """Анализирует текст и возвращает структуру запроса."""
        text_lower = text.lower().strip()

        result = {
            "original": text,
            "type": "unknown",
            "subject": None,
            "keywords": self._extract_keywords(text_lower),
            "is_question": "?" in text or any(
                text_lower.startswith(w) for w in 
                ["что", "как", "где", "когда", "почему", "зачем", "кто", "сколько"]
            ),
        }

        # Проверяем паттерны
        for query_type, pattern in self.patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                result["type"] = query_type
                if query_type == "math":
                    result["operands"] = (int(match.group(1)), match.group(2), int(match.group(3)))
                else:
                    result["subject"] = match.group(1).strip()
                break

        return result

    def _extract_keywords(self, text: str) -> List[str]:
        """Извлекает ключевые слова из текста."""
        # Убираем стоп-слова
        stop_words = {
            "и", "в", "на", "с", "по", "для", "что", "как", "это", "то",
            "а", "но", "или", "если", "то", "же", "бы", "ли", "не", "ни",
            "я", "ты", "он", "она", "мы", "вы", "они", "мне", "тебе",
            "его", "её", "их", "нас", "вас", "у", "к", "от", "до", "из",
        }
        words = re.findall(r"[а-яёa-z]+", text.lower())
        return [w for w in words if w not in stop_words and len(w) > 2]


class ResponseGenerator:
    """Генерирует ответы на основе анализа и данных."""

    def __init__(self, online_brain=None):
        self.online_brain = online_brain
        self.analyzer = TextAnalyzer()

    def generate(self, text: str, context: List[Dict] = None) -> str:
        """Генерирует ответ на основе анализа текста."""
        analysis = self.analyzer.analyze(text)

        # Математика — решаем локально
        if analysis["type"] == "math":
            return self._solve_math(analysis["operands"])

        # Вопросы требующие информации — ищем онлайн
        if analysis["type"] in ["definition", "how_to", "why", "who", "compare", "list"]:
            return self._answer_with_search(analysis)

        # Простые вопросы без конкретной темы
        if analysis["is_question"] and not analysis["subject"]:
            return self._answer_generic_question(analysis, context)

        # Неизвестный тип — пытаемся понять по ключевым словам
        if analysis["keywords"]:
            return self._answer_by_keywords(analysis)

        return None  # Не смогли сгенерировать — передаём в fallback

    def _solve_math(self, operands) -> str:
        """Решает математическое выражение."""
        a, op, b = operands
        ops = {
            "+": operator.add,
            "-": operator.sub,
            "*": operator.mul,
            "/": operator.truediv,
        }
        try:
            result = ops[op](a, b)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return f"{a} {op} {b} = {result}"
        except ZeroDivisionError:
            return "На ноль делить нельзя!"
        except Exception:
            return "Не смог посчитать это выражение."

    def _answer_with_search(self, analysis: Dict) -> str:
        """Ищет ответ в интернете."""
        if not self.online_brain:
            return f"Чтобы ответить на вопрос про '{analysis['subject']}', мне нужен доступ к интернету."

        # Формируем поисковый запрос
        query = analysis["subject"]
        if analysis["type"] == "definition":
            query = f"что такое {query}"
        elif analysis["type"] == "how_to":
            query = f"как {query}"
        elif analysis["type"] == "who":
            query = f"кто такой {query}"

        return self.online_brain.answer(query)

    def _answer_generic_question(self, analysis: Dict, context: List[Dict]) -> str:
        """Отвечает на общий вопрос, используя контекст."""
        if context and len(context) > 0:
            last_topic = context[-1].get("input", "")
            return f"Ты спрашиваешь про то, что мы обсуждали ({last_topic})? Уточни, пожалуйста."
        return "Интересный вопрос! Можешь уточнить, что именно тебя интересует?"

    def _answer_by_keywords(self, analysis: Dict) -> str:
        """Пытается ответить по ключевым словам."""
        keywords = analysis["keywords"]

        # Проверяем известные темы
        tech_words = {"python", "код", "программ", "функци", "класс", "метод"}
        if any(kw in tech_words or any(tw in kw for tw in tech_words) for kw in keywords):
            if self.online_brain:
                return self.online_brain.answer(" ".join(keywords[:3]))
            return "Это похоже на вопрос про программирование. Могу поискать информацию, если уточнишь."

        return None
