from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ClarificationQuestion:
    key: str
    prompt: str
    reason: str


@dataclass(slots=True)
class GameSpec:
    title: str
    theme: str
    concept_summary: str
    objective: str
    perspective: str
    core_mechanic: str
    controls: dict[str, str]
    player_entity: str
    hazard_entity: str
    collectible_entity: str | None
    score_model: str
    score_target: int | None
    survival_seconds: int | None
    win_condition: str
    lose_condition: str
    rendering_approach: str
    file_structure: list[str]
    generation_notes: list[str] = field(default_factory=list)
    arena_width: int = 800
    arena_height: int = 600
    player_speed: int = 260
    hazard_count: int = 4
    collectible_count: int = 0
    score_per_collectible: int = 10
    difficulty: str = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "theme": self.theme,
            "concept_summary": self.concept_summary,
            "objective": self.objective,
            "perspective": self.perspective,
            "core_mechanic": self.core_mechanic,
            "controls": self.controls,
            "player_entity": self.player_entity,
            "hazard_entity": self.hazard_entity,
            "collectible_entity": self.collectible_entity,
            "score_model": self.score_model,
            "score_target": self.score_target,
            "survival_seconds": self.survival_seconds,
            "win_condition": self.win_condition,
            "lose_condition": self.lose_condition,
            "rendering_approach": self.rendering_approach,
            "file_structure": self.file_structure,
            "generation_notes": self.generation_notes,
            "arena_width": self.arena_width,
            "arena_height": self.arena_height,
            "player_speed": self.player_speed,
            "hazard_count": self.hazard_count,
            "collectible_count": self.collectible_count,
            "score_per_collectible": self.score_per_collectible,
            "difficulty": self.difficulty,
        }


@dataclass(slots=True)
class ValidationResult:
    passed: bool
    messages: list[str]
