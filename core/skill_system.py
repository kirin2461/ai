"""Система навыков с прокачкой и фоновым развитием."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import math


class SkillLevel(Enum):
    NOVICE = "Новичок"
    BEGINNER = "Начинающий"
    INTERMEDIATE = "Средний"
    ADVANCED = "Продвинутый"
    EXPERT = "Эксперт"


@dataclass
class Skill:
    name: str
    category: str
    experience: float = 0.0
    level: SkillLevel = SkillLevel.NOVICE
    uses: int = 0
    tags: List[str] = field(default_factory=list)
    last_used_cycle: int = 0  # для «забывания»


class SkillSystem:
    XP_THRESHOLDS = {
        SkillLevel.NOVICE: 0,
        SkillLevel.BEGINNER: 100,
        SkillLevel.INTERMEDIATE: 500,
        SkillLevel.ADVANCED: 2000,
        SkillLevel.EXPERT: 10000,
    }

    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.total_experience = 0.0
        self.current_cycle = 0
        self._init_default_skills()

    def _init_default_skills(self):
        defaults = [
            ("приветствие", "общение", ["social"]),
            ("поиск_в_интернете", "технические", ["web", "research"]),
            ("эмпатия", "общение", ["emotional"]),
            ("анализ", "технические", ["logic"]),
            ("креативность", "творческие", ["creative"]),
        ]
        for name, cat, tags in defaults:
            self.skills[name] = Skill(name=name, category=cat, tags=tags)

    # =============== Активное использование ===============

    def use_skill(self, name: str, success: bool = True, cycle: Optional[int] = None) -> float:
        """Прокачка навыка при явном использовании."""
        if name not in self.skills:
            self.skills[name] = Skill(name=name, category="общение")

        skill = self.skills[name]
        base_xp = 10 if success else 3
        bonus = 1.0 + (skill.uses * 0.01)
        xp = base_xp * min(bonus, 2.0)

        skill.experience += xp
        skill.uses += 1
        skill.last_used_cycle = cycle if cycle is not None else self.current_cycle

        self.total_experience += xp
        self._update_level(skill)
        return xp

    def _update_level(self, skill: Skill) -> None:
        for level in reversed(list(SkillLevel)):
            if skill.experience >= self.XP_THRESHOLDS[level]:
                skill.level = level
                break

    # =============== Фоновое развитие/забывание ===============

    def tick(self, cycles: int = 1) -> None:
        """
        Фоновая эволюция навыков.
        - Небольшой пассивный опыт за сам факт существования диалога.
        - Слабое «забывание» давно не использованных навыков.
        """
        self.current_cycle += cycles

        # Пассивный опыт (за жизнь агента)
        passive_xp = 0.5 * cycles
        self.total_experience += passive_xp

        # Лёгкая коррекция навыков
        for skill in self.skills.values():
            # Чуть-чуть пассивного опыта всем
            skill.experience += passive_xp / max(len(self.skills), 1)

            # Если навык давно не использовали — немного «забывает»
            cycles_since_use = self.current_cycle - skill.last_used_cycle
            if cycles_since_use > 50 and skill.experience > 0:
                decay = skill.experience * 0.001 * cycles  # очень слабый распад
                skill.experience = max(0.0, skill.experience - decay)

            self._update_level(skill)

    # =============== Чтение состояния ===============

    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def get_level(self, name: str) -> int:
        """Вернуть численный уровень навыка (NOVICE=0 ... EXPERT=4)."""
        skill = self.skills.get(name)
        if not skill:
            return 0
        order = list(SkillLevel)
        return order.index(skill.level)

    def get_total_level(self) -> int:
        """Общий уровень развития системы навыков (для отображения LVL)."""
        return int(math.log10(self.total_experience + 1) * 2) + 1

    def get_skills_by_category(self, category: str) -> List[Skill]:
        return [s for s in self.skills.values() if s.category == category]
