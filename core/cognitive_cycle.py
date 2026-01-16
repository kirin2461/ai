"""Когнитивный цикл с планированием, эмоциями, навыками и онлайн-режимом."""

import re
import operator
from typing import Dict, Any, List, Tuple

from modules.online_brain import OnlineBrain
from .analyzer import TextAnalyzer, ResponseGenerator
from .emotion_engine import EmotionEngine, EmotionType
from .skill_system import SkillSystem
from .safety_system import SafetySystem


class CognitiveCycle:
    def __init__(self, api_key: str = None):
        self.api_key = api_key

        self.emotion = EmotionEngine()
        self.skills = SkillSystem()
        self.safety = SafetySystem()
        self.online_brain = OnlineBrain()
        self.response_generator = ResponseGenerator(self.online_brain)

        self.memory: List[Dict[str, Any]] = []
        self.working_memory: List[Dict[str, str]] = []
        self.cycle_count = 0
        self.client = None

        self.user_profile: Dict[str, Any] = {
            "name": None,
            "likes": set(),
            "dislikes": set(),
            "style": "friendly",
            "topics": {},
        }

        if api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key)
            except Exception:
                self.client = None

    def run_cycle(self, user_input: str) -> str:
        self.cycle_count += 1

        safe, msg = self._perceive(user_input)
        if not safe:
            return f"⚠️ {msg}"

        self._update_working_memory(user_input)
        context = self._apply_attention()
        retrieved = self._retrieve_memory(user_input)
        self._update_emotion(user_input)

        intent = self._infer_intent(user_input)
        goals = self._form_goals(intent)
        plan = self._make_plan(intent, goals, context, retrieved)
        response = self._run_plan(plan, user_input, context, retrieved)

        self._learn(user_input, response, context, retrieved, intent, goals)
        self._cleanup()

        return response

    def _perceive(self, user_input: str) -> Tuple[bool, str]:
        safe, msg = self.safety.check_input(user_input)
        return safe, msg

    def _update_working_memory(self, user_input: str) -> None:
        self.working_memory.append({"role": "user", "content": user_input})
        if len(self.working_memory) > 20:
            self.working_memory = self.working_memory[-20:]

    def _apply_attention(self) -> List[Dict[str, str]]:
        return self.working_memory[-10:]

    def _retrieve_memory(self, user_input: str) -> List[Dict[str, Any]]:
        return self.memory[-5:]

    def _update_emotion(self, text: str) -> None:
        t = text.lower()
        if any(w in t for w in ["привет", "здравствуй", "добрый"]):
            self.emotion.apply_stimulus(EmotionType.JOY, 0.3)
        elif any(w in t for w in ["грустно", "плохо", "печаль"]):
            self.emotion.apply_stimulus(EmotionType.SADNESS, 0.4)
        elif any(w in t for w in ["злюсь", "бесит", "раздражает"]):
            self.emotion.apply_stimulus(EmotionType.ANGER, 0.3)
        elif "?" in text:
            self.emotion.apply_stimulus(EmotionType.INTEREST, 0.2)

    def _infer_intent(self, text: str) -> str:
        t = text.lower()
        if t.startswith("/status"):
            return "status"
        if t.startswith("/reset"):
            return "reset"
        if any(w in t for w in ["что ты умеешь", "что ты можешь", "кто ты"]):
            return "ask_capabilities"
        if any(w in t for w in ["совет", "подскажи", "как мне", "что делать"]):
            return "ask_advice"
        if any(w in t for w in ["грустно", "плохо", "одиноко", "тяжело"]):
            return "seek_support"
        if "поиск_в_интернете" in t:
            return "search_skill"
        if any(w in t for w in ["игра", "играть", "скучно"]):
            return "want_fun"
        if "?" in t:
            return "generic_question"
        return "smalltalk"

    def _form_goals(self, intent: str) -> List[str]:
        goals_map = {
            "status": ["report_internal_state"],
            "reset": ["reset_memory"],
            "ask_capabilities": ["describe_capabilities"],
            "ask_advice": ["analyze_situation", "give_simple_advice"],
            "seek_support": ["comfort_user", "show_empathy"],
            "search_skill": ["ack_search_skill", "maybe_online_search"],
            "want_fun": ["offer_simple_game"],
            "generic_question": ["try_answer_question"],
        }
        return goals_map.get(intent, ["keep_conversation"])

    def _make_plan(self, intent: str, goals: List[str], context, retrieved) -> List[str]:
        plan: List[str] = []

        if "reset_memory" in goals:
            return ["do_reset_memory"]
        if "report_internal_state" in goals:
            return ["describe_state"]

        if "comfort_user" in goals:
            plan.extend(["check_recent_emotion", "generate_support_message"])
        if "show_empathy" in goals:
            plan.append("use_empathy_skill")
        if "describe_capabilities" in goals:
            plan.append("describe_capabilities")
        if "ack_search_skill" in goals:
            plan.append("ack_search_skill")
        if "maybe_online_search" in goals:
            plan.append("maybe_online_search")
        if "offer_simple_game" in goals:
            plan.append("offer_simple_game")
        if "try_answer_question" in goals:
            plan.append("query_llm" if self.client else "use_fallback_logic")
        if "keep_conversation" in goals:
            plan.append("keep_conversation")

        return plan or ["use_fallback_logic"]

    def _run_plan(self, plan: List[str], user_input: str, context, retrieved) -> str:
        if "do_reset_memory" in plan:
            self.working_memory.clear()
            self.memory.clear()
            return "Память очищена. Начинаем заново!"

        if "describe_state" in plan:
            state = self.get_state()
            return f"Цикл: {state['cycle']}, эмоция: {state['emotion']} ({state['confidence']:.0%}), настроение: {state['mood']}."

        if "generate_support_message" in plan:
            emotion, _ = self.emotion.get_dominant_emotion()
            return f"Слышу, что тебе непросто. Сейчас я ощущаю {emotion.value}. Хочешь рассказать подробнее?"

        if "describe_capabilities" in plan:
            return "Я ещё не полноценный ИИ, но уже умею: помнить контекст, реагировать эмоциями, прокачивать навыки и подстраиваться под тебя."

        if "use_empathy_skill" in plan:
            lvl = self.skills.get_level("эмпатия")
            return "Я с тобой. Попробую быть максимально внимательным." if lvl >= 3 else "Понимаю, что тебе непросто. Постараюсь поддержать."

        if "ack_search_skill" in plan:
            lvl = self.skills.get_level("поиск_в_интернете")
            return "Я пока только учусь поиску. Могу помочь сформулировать запрос." if lvl == 0 else "Навык поиска прокачан. Могу подсказать, как лучше искать."

        if "maybe_online_search" in plan:
            return self._online_search_response(user_input)

        if "offer_simple_game" in plan:
            return "Давай сыграем! Я загадаю число от 1 до 10, а ты угадай."

        if "query_llm" in plan and self.client:
            return self._generate_llm_response(user_input, context, retrieved)

        if "keep_conversation" in plan:
            last = self.memory[-1] if self.memory else None
            if last and len(last.get("input", "")) > 3:
                return f"Мы недавно обсуждали: \"{last['input']}\". Продолжим или сменим тему?"

        generated = self.response_generator.generate(user_input, context)
        if generated:
            return generated

        return self._fallback_response(user_input)

    def _online_search_response(self, text: str) -> str:
        query = text.strip()
        if not query:
            return "Нужно что-то для поиска. Попробуй сформулировать запрос."
        return self.online_brain.answer(query)

    def _generate_llm_response(self, user_input: str, context, retrieved) -> str:
        if not self.client:
            return self._fallback_response(user_input)
        try:
            emotion, conf = self.emotion.get_dominant_emotion()
            messages = [{"role": "system", "content": f"Ты AI-компаньон. Эмоция: {emotion.value} ({conf:.0%}). Отвечай кратко."}]
            messages.extend([{"role": m["role"], "content": m["content"]} for m in context])
            messages.append({"role": "user", "content": user_input})
            response = self.client.chat.completions.create(model="gpt-4o-mini", messages=messages, max_tokens=500)
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка API: {e}"

    def _fallback_response(self, text: str) -> str:
        t = text.lower().strip()

        if any(w in t for w in ["привет", "здравствуй", "добрый"]):
            return "Привет! Рад тебя видеть 🙂"

        if "как дела" in t:
            emotion, _ = self.emotion.get_dominant_emotion()
            return f"У меня всё неплохо, чувствую {emotion.value}. А у тебя как?"

        m = re.fullmatch(r"\s*(\d+)\s*([+\-*/])\s*(\d+)\s*", t)
        if m:
            a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
            ops = {"+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.truediv}
            try:
                res = ops[op](a, b)
                res = int(res) if isinstance(res, float) and res.is_integer() else res
                return f"{a} {op} {b} = {res}"
            except Exception:
                pass

        m2 = re.search(r"сколько\s+(?:будет\s+)?(\d+)\s*([+\-*/])\s*(\d+)", t)
        if m2:
            a, op, b = int(m2.group(1)), m2.group(2), int(m2.group(3))
            ops = {"+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.truediv}
            try:
                res = ops[op](a, b)
                res = int(res) if isinstance(res, float) and res.is_integer() else res
                return f"{a} {op} {b} = {res}"
            except Exception:
                pass

        if any(w in t for w in ["что ты умеешь", "что ты можешь"]):
            return "Я могу говорить, запоминать контекст, реагировать эмоциями и прокачивать навыки."

        if "кто ты" in t:
            return "Я экспериментальный ИИ-компаньон, который учится на общении с тобой."

        if "?" in text:
            return "Интересный вопрос. Как ты сам бы на него ответил?"

        return "Понял тебя. Можешь рассказать подробнее?"

    def _update_skills(self, text: str) -> None:
        t = text.lower()
        if any(w in t for w in ["привет", "пока", "спасибо"]):
            self.skills.use_skill("приветствие")
        if any(w in t for w in ["найди", "поищи", "загугли", "поиск_в_интернете"]):
            self.skills.use_skill("поиск_в_интернете")
        if any(w in t for w in ["грустно", "плохо", "расстроен", "одиноко"]):
            self.skills.use_skill("эмпатия")

    def _learn(self, user_input: str, response: str, context, retrieved, intent: str, goals: List[str]) -> None:
        episode = {
            "input": user_input,
            "output": response,
            "context": context,
            "retrieved": retrieved,
            "intent": intent,
            "goals": goals,
        }
        self.memory.append(episode)
        if len(self.memory) > 100:
            self.memory = self.memory[-100:]

        self._update_skills(user_input)

        t = user_input.lower()
        topics = self.user_profile["topics"]
        for word in ["игры", "работа", "учёба", "семья", "проект"]:
            if word in t:
                topics[word] = topics.get(word, 0) + 1

    def _cleanup(self) -> None:
        self.emotion.decay()
        if hasattr(self.skills, "tick"):
            self.skills.tick()

        def get_state(self) -> Dict[str, Any]:
        emotion, confidence = self.emotion.get_dominant_emotion()
        return {
            "cycle": self.cycle_count,
            "emotion": emotion.value,
            "confidence": confidence,
            "mood": self.emotion.get_mood_description(),
            "pad": {
                "pleasure": self.emotion.pad.pleasure,
                "arousal": self.emotion.pad.arousal,
                "dominance": self.emotion.pad.dominance,
            },
            "total_level": self.skills.get_total_level(),
            "safety_mode": self.safety.mode.value,
        }
