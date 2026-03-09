from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .analysis import analyze_prompt, prettify_theme
from .llm import LLMClient
from .models import GameSpec


@dataclass(slots=True)
class Planner:
    llm_client: LLMClient

    def build_spec(self, prompt: str, answers: dict[str, str]) -> GameSpec:
        signals = analyze_prompt(prompt)
        merged = self._merge_inputs(prompt, signals, answers)
        llm_copy = self.llm_client.create_plan_copy(prompt, merged)

        return GameSpec(
            title=llm_copy["title"],
            theme=merged["theme"],
            concept_summary=llm_copy["concept_summary"],
            objective=merged["objective"],
            perspective=merged["perspective"],
            core_mechanic=merged["core_mechanic"],
            controls=merged["controls"],
            player_entity=merged["player_entity"],
            hazard_entity=merged["hazard_entity"],
            collectible_entity=merged["collectible_entity"],
            score_model=merged["score_model"],
            score_target=merged["score_target"],
            survival_seconds=merged["survival_seconds"],
            win_condition=merged["win_condition"],
            lose_condition=merged["lose_condition"],
            rendering_approach="HTML5 Canvas with a single requestAnimationFrame update/render loop.",
            file_structure=["index.html", "style.css", "game.js"],
            generation_notes=llm_copy["generation_notes"],
            arena_width=800,
            arena_height=600,
            player_speed=merged["player_speed"],
            hazard_count=merged["hazard_count"],
            collectible_count=merged["collectible_count"],
            score_per_collectible=merged["score_per_collectible"],
            difficulty=merged["difficulty"],
        )

    def render_plan(self, spec: GameSpec) -> str:
        return json.dumps(spec.to_dict(), indent=2)

    def _merge_inputs(self, prompt: str, signals: Any, answers: dict[str, str]) -> dict[str, Any]:
        theme = self._resolve_theme(signals.theme, answers.get("theme"), prompt)
        mechanic = self._resolve_mechanic(signals.core_mechanic, answers.get("objective"), prompt)
        perspective = self._resolve_perspective(signals.perspective, answers.get("perspective"))
        controls = self._resolve_controls(signals.controls, answers.get("controls"))
        difficulty = signals.difficulty
        score_target = self._resolve_score_target(mechanic, signals.score_target, prompt, answers)
        survival_seconds = self._resolve_survival_seconds(mechanic, signals.duration_seconds, prompt, answers)
        collectible_entity = self._resolve_collectible_entity(theme, mechanic)
        lose_condition = answers.get("lose_condition") or signals.lose_condition or "Lose on contact with a hazard."
        win_condition = self._resolve_win_condition(mechanic, score_target, survival_seconds, collectible_entity)
        hazard_entity = self._resolve_hazard_entity(theme)
        unsupported_notes = [
            f"Simplified unsupported request area '{feature}' into a small 2D single-player browser game."
            for feature in signals.unsupported_features
        ]
        objective = self._resolve_objective_sentence(mechanic, score_target, survival_seconds, collectible_entity, hazard_entity)

        hazard_count = {"easy": 3, "medium": 4, "hard": 5}[difficulty]
        if mechanic == "hybrid":
            hazard_count += 1
        collectible_count = 0 if collectible_entity is None else 5
        player_speed = {"easy": 280, "medium": 260, "hard": 245}[difficulty]
        score_per_collectible = 10

        merged = {
            "theme": theme,
            "core_mechanic": mechanic,
            "perspective": perspective,
            "controls": controls,
            "difficulty": difficulty,
            "score_target": score_target,
            "survival_seconds": survival_seconds,
            "collectible_entity": collectible_entity,
            "lose_condition": lose_condition,
            "win_condition": win_condition,
            "hazard_entity": hazard_entity,
            "player_entity": self._resolve_player_entity(theme),
            "score_model": self._resolve_score_model(mechanic, score_target, survival_seconds),
            "generation_notes": unsupported_notes,
            "objective": objective,
            "hazard_count": hazard_count,
            "collectible_count": collectible_count,
            "player_speed": player_speed,
            "score_per_collectible": score_per_collectible,
        }
        return merged

    def _resolve_theme(self, detected: str | None, answer: str | None, prompt: str) -> str:
        if answer:
            return answer.strip()
        if detected:
            return prettify_theme(detected)
        words = [word for word in re.findall(r"[a-zA-Z]+", prompt) if len(word) > 3]
        return words[0].lower() if words else "arcade"

    def _resolve_mechanic(self, detected: str | None, answer: str | None, prompt: str) -> str:
        text = f"{answer or ''} {prompt}".lower()
        has_collect = any(word in text for word in ("collect", "gather", "pickup", "pick up", "grab"))
        has_dodge = any(word in text for word in ("dodge", "avoid", "evade", "escape"))
        has_survive = any(word in text for word in ("survive", "survival", "endure", "last"))
        if (has_collect and has_dodge) or (has_collect and has_survive):
            return "hybrid"
        if has_collect:
            return "collect"
        if has_dodge:
            return "dodge"
        if has_survive:
            return "survive"
        if any(word in text for word in ("mix", "combination", "hybrid", "collect and dodge")):
            return "hybrid"
        return detected or "survive"

    def _resolve_perspective(self, detected: str | None, answer: str | None) -> str:
        answer_text = (answer or "").lower()
        if "side" in answer_text:
            return "side-view"
        if "static" in answer_text or "single screen" in answer_text:
            return "static-screen"
        if "top" in answer_text or "overhead" in answer_text:
            return "top-down"
        return detected or "top-down"

    def _resolve_controls(self, detected: dict[str, str] | None, answer: str | None) -> dict[str, str]:
        answer_text = (answer or "").lower()
        if "wasd" in answer_text:
            return {"up": "W", "down": "S", "left": "A", "right": "D"}
        if "mouse" in answer_text:
            return {
                "up": "Move mouse up",
                "down": "Move mouse down",
                "left": "Move mouse left",
                "right": "Move mouse right",
            }
        if "arrow" in answer_text:
            return {"up": "ArrowUp", "down": "ArrowDown", "left": "ArrowLeft", "right": "ArrowRight"}
        return detected or {"up": "ArrowUp/W", "down": "ArrowDown/S", "left": "ArrowLeft/A", "right": "ArrowRight/D"}

    def _resolve_score_target(
        self,
        mechanic: str,
        detected_score_target: int | None,
        prompt: str,
        answers: dict[str, str],
    ) -> int | None:
        if detected_score_target:
            return detected_score_target
        combined = " ".join(answers.values()) + " " + prompt
        match = re.search(r"(\d+)\s*(points?|stars?|coins?|items?)", combined.lower())
        if match:
            return int(match.group(1))
        if mechanic == "collect":
            return 100
        if mechanic == "hybrid":
            return 60
        return None

    def _resolve_survival_seconds(
        self,
        mechanic: str,
        detected_duration: int | None,
        prompt: str,
        answers: dict[str, str],
    ) -> int | None:
        if detected_duration:
            return detected_duration
        combined = " ".join(answers.values()) + " " + prompt
        second_match = re.search(r"(\d+)\s*seconds?", combined.lower())
        if second_match:
            return int(second_match.group(1))
        if mechanic == "survive":
            return 30
        if mechanic == "dodge":
            return 25
        return None

    def _resolve_collectible_entity(self, theme: str, mechanic: str) -> str | None:
        if mechanic not in {"collect", "hybrid"}:
            return None
        theme_text = theme.lower()
        if "space" in theme_text:
            return "star shard"
        if "zombie" in theme_text:
            return "supply crate"
        if "ocean" in theme_text:
            return "pearl"
        if "dungeon" in theme_text:
            return "rune"
        return "energy orb"

    def _resolve_hazard_entity(self, theme: str) -> str:
        theme_text = theme.lower()
        if "space" in theme_text:
            return "asteroid"
        if "zombie" in theme_text:
            return "zombie"
        if "ocean" in theme_text:
            return "mine"
        if "dungeon" in theme_text:
            return "trap orb"
        return "hazard drone"

    def _resolve_player_entity(self, theme: str) -> str:
        theme_text = theme.lower()
        if "space" in theme_text:
            return "pilot"
        if "zombie" in theme_text:
            return "survivor"
        if "ocean" in theme_text:
            return "diver"
        if "dungeon" in theme_text:
            return "adventurer"
        return "runner"

    def _resolve_score_model(self, mechanic: str, score_target: int | None, survival_seconds: int | None) -> str:
        if mechanic == "collect" and score_target:
            return f"Gain 10 points per collectible and reach {score_target} points."
        if mechanic == "hybrid" and score_target:
            return f"Gain 10 points per collectible while avoiding hazards until {score_target} points."
        if survival_seconds:
            return f"Stay alive until the timer reaches {survival_seconds} seconds."
        return "Score increases only when the main objective is met."

    def _resolve_win_condition(
        self,
        mechanic: str,
        score_target: int | None,
        survival_seconds: int | None,
        collectible_entity: str | None,
    ) -> str:
        if score_target and collectible_entity:
            return f"Win by collecting enough {collectible_entity}s to reach {score_target} points."
        if survival_seconds:
            return f"Win by surviving for {survival_seconds} seconds."
        if mechanic == "dodge":
            return "Win by lasting until the timer expires."
        return "Win when the main objective is complete."

    def _resolve_objective_sentence(
        self,
        mechanic: str,
        score_target: int | None,
        survival_seconds: int | None,
        collectible_entity: str | None,
        hazard_entity: str,
    ) -> str:
        if mechanic == "collect" and collectible_entity and score_target:
            return f"Collect {collectible_entity}s while avoiding {hazard_entity}s until you reach {score_target} points."
        if mechanic == "hybrid" and collectible_entity and score_target:
            return f"Collect {collectible_entity}s and dodge {hazard_entity}s until you reach {score_target} points."
        if survival_seconds:
            return f"Survive against {hazard_entity}s for {survival_seconds} seconds."
        return f"Avoid {hazard_entity}s and stay alive."
