from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .analysis import PromptSignals, analyze_prompt, prettify_theme
from .llm import LLMClient
from .models import GameSpec


@dataclass(slots=True)
class Planner:
    llm_client: LLMClient

    def build_spec(self, prompt: str, answers: dict[str, str], framework: str = "vanilla_js") -> GameSpec:
        signals = analyze_prompt(prompt)
        llm_plan = self._build_llm_plan(prompt, answers, framework, signals)
        merged = self._merge_inputs(prompt, signals, answers, llm_plan)
        llm_copy = self.llm_client.create_plan_copy(prompt, merged)
        title = self._plan_text(llm_plan, "title") or llm_copy["title"]
        concept_summary = self._plan_text(llm_plan, "concept_summary") or llm_copy["concept_summary"]
        generation_notes = merged["generation_notes"] + [
            note for note in llm_copy["generation_notes"] if note not in merged["generation_notes"]
        ]

        return GameSpec(
            title=title,
            source_prompt=prompt,
            theme=merged["theme"],
            concept_summary=concept_summary,
            framework=framework,
            objective=merged["objective"],
            perspective=merged["perspective"],
            core_mechanic=merged["core_mechanic"],
            play_variant=merged["play_variant"],
            movement_model=merged["movement_model"],
            hazard_behavior=merged["hazard_behavior"],
            collectible_behavior=merged["collectible_behavior"],
            arena_layout=merged["arena_layout"],
            controls=merged["controls"],
            player_identity=merged["player_identity"],
            player_entity=merged["player_entity"],
            hazard_entity=merged["hazard_entity"],
            collectible_entity=merged["collectible_entity"],
            signature_mechanic=merged["signature_mechanic"],
            progression_style=merged["progression_style"],
            visual_tone=merged["visual_tone"],
            arena_detail=merged["arena_detail"],
            player_ability=merged["player_ability"],
            pressure_curve=merged["pressure_curve"],
            hazard_pattern=merged["hazard_pattern"],
            score_model=merged["score_model"],
            score_target=merged["score_target"],
            survival_seconds=merged["survival_seconds"],
            win_condition=merged["win_condition"],
            lose_condition=merged["lose_condition"],
            rendering_approach=self._resolve_rendering_approach(framework),
            file_structure=["index.html", "style.css", "game.js"],
            generation_notes=generation_notes,
            arena_width=merged["arena_width"],
            arena_height=merged["arena_height"],
            player_speed=merged["player_speed"],
            hazard_count=merged["hazard_count"],
            collectible_count=merged["collectible_count"],
            score_per_collectible=merged["score_per_collectible"],
            difficulty=merged["difficulty"],
        )

    def render_plan(self, spec: GameSpec) -> str:
        return json.dumps(spec.to_dict(), indent=2)

    def _build_llm_plan(
        self,
        prompt: str,
        answers: dict[str, str],
        framework: str,
        signals: PromptSignals,
    ) -> dict[str, Any]:
        create_game_plan = getattr(self.llm_client, "create_game_plan", None)
        if not callable(create_game_plan):
            return {}
        payload = create_game_plan(
            prompt,
            answers,
            framework,
            self._build_planning_context(prompt, answers, framework, signals),
        )
        return payload if isinstance(payload, dict) else {}

    def _build_planning_context(
        self,
        prompt: str,
        answers: dict[str, str],
        framework: str,
        signals: PromptSignals,
    ) -> dict[str, Any]:
        return {
            "prompt": prompt,
            "user_answers": answers,
            "requested_framework": framework,
            "prompt_signals": {
                "theme": signals.theme,
                "core_mechanic": signals.core_mechanic,
                "perspective": signals.perspective,
                "controls": signals.controls,
                "difficulty": signals.difficulty,
                "duration_seconds": signals.duration_seconds,
                "score_target": signals.score_target,
                "lose_condition": signals.lose_condition,
                "unsupported_features": signals.unsupported_features,
                "tone": signals.tone,
                "player_role": signals.player_role,
                "special_mechanic": signals.special_mechanic,
                "progression_hint": signals.progression_hint,
            },
            "constraints": [
                "small 2D browser game only",
                "single local bundle with index.html, style.css, and game.js",
                "no backend services",
                "design should be specific to the prompt and user answers",
            ],
        }

    def _merge_inputs(
        self,
        prompt: str,
        signals: PromptSignals,
        answers: dict[str, str],
        llm_plan: dict[str, Any],
    ) -> dict[str, Any]:
        theme = self._resolve_theme(self._plan_text(llm_plan, "theme") or signals.theme, answers.get("theme"), prompt)
        objective_answer = answers.get("objective") or self._plan_text(llm_plan, "objective")
        mechanic = self._resolve_mechanic(self._plan_text(llm_plan, "core_mechanic") or signals.core_mechanic, objective_answer, prompt)
        perspective = self._resolve_perspective(self._plan_text(llm_plan, "perspective") or signals.perspective, answers.get("perspective"))
        controls = self._resolve_controls(self._plan_controls(llm_plan) or signals.controls, answers.get("controls"))
        difficulty = signals.difficulty
        player_entity = self._plan_text(llm_plan, "player_entity") or self._resolve_player_entity(theme)
        player_identity = self._resolve_player_identity(
            player_entity,
            self._plan_text(llm_plan, "player_identity") or signals.player_role,
            answers.get("player_identity"),
        )
        play_variant = self._resolve_play_variant(prompt, answers, mechanic, perspective, theme)
        movement_model = self._resolve_movement_model(play_variant)
        collectible_entity = self._plan_text(llm_plan, "collectible_entity") or self._resolve_collectible_entity(theme, mechanic)
        hazard_entity = self._plan_text(llm_plan, "hazard_entity") or self._resolve_hazard_entity(theme)
        signature_mechanic = self._resolve_signature_mechanic(
            answers.get("signature_mechanic") or self._plan_text(llm_plan, "signature_mechanic"),
            signals.special_mechanic,
            play_variant,
        )
        progression_style = self._resolve_progression_style(
            answers.get("progression_style") or self._plan_text(llm_plan, "progression_style"),
            signals.progression_hint,
            play_variant,
            mechanic,
        )
        visual_tone = self._resolve_visual_tone(
            answers.get("visual_tone") or self._plan_text(llm_plan, "visual_tone"),
            signals.tone,
            theme,
            difficulty,
        )
        arena_detail = self._resolve_arena_detail(
            answers.get("arena_detail") or self._plan_text(llm_plan, "arena_detail"),
            prompt,
            theme,
            play_variant,
        )
        player_ability = self._resolve_player_ability(signature_mechanic, prompt, answers, movement_model)
        pressure_curve = self._resolve_pressure_curve(progression_style, play_variant, difficulty)
        hazard_pattern = self._resolve_hazard_pattern(progression_style, signature_mechanic, play_variant)
        hazard_behavior = self._resolve_hazard_behavior(play_variant, hazard_pattern)
        collectible_behavior = self._resolve_collectible_behavior(play_variant, collectible_entity, signature_mechanic)
        arena_layout = self._resolve_arena_layout(play_variant)
        score_target = self._plan_int(llm_plan, "score_target")
        if score_target is None:
            score_target = self._resolve_score_target(mechanic, signals.score_target, prompt, answers)
        survival_seconds = self._plan_int(llm_plan, "survival_seconds")
        if survival_seconds is None:
            survival_seconds = self._resolve_survival_seconds(mechanic, signals.duration_seconds, prompt, answers)
        lose_condition = self._resolve_lose_condition(
            answers.get("lose_condition") or self._plan_text(llm_plan, "lose_condition"),
            signals.lose_condition,
            hazard_entity,
        )
        objective = self._resolve_objective_sentence(
            objective_answer,
            mechanic,
            score_target,
            survival_seconds,
            collectible_entity,
            hazard_entity,
            player_identity,
            signature_mechanic,
        )
        win_condition = self._plan_text(llm_plan, "win_condition") or self._resolve_win_condition(
            mechanic,
            score_target,
            survival_seconds,
            collectible_entity,
            progression_style,
        )
        unsupported_notes = [
            f"Simplified unsupported request area '{feature}' into a small 2D single-player browser game."
            for feature in signals.unsupported_features
        ]
        unsupported_notes.extend(self._plan_notes(llm_plan))
        unsupported_notes.extend(
            [
                f"Personalized around controlling {player_identity} in {arena_detail}.",
                f"Signature hook: {signature_mechanic.rstrip('.!?')}.",
                f"Challenge pacing leans {progression_style} with a {visual_tone} presentation.",
            ]
        )
        tuning = self._resolve_variant_tuning(
            play_variant,
            difficulty,
            collectible_entity is not None,
            pressure_curve,
            visual_tone,
            player_ability,
        )

        return {
            "theme": theme,
            "core_mechanic": mechanic,
            "perspective": perspective,
            "play_variant": play_variant,
            "movement_model": movement_model,
            "hazard_behavior": hazard_behavior,
            "collectible_behavior": collectible_behavior,
            "arena_layout": arena_layout,
            "controls": controls,
            "player_identity": player_identity,
            "player_entity": player_entity,
            "hazard_entity": hazard_entity,
            "collectible_entity": collectible_entity,
            "signature_mechanic": signature_mechanic,
            "progression_style": progression_style,
            "visual_tone": visual_tone,
            "arena_detail": arena_detail,
            "player_ability": player_ability,
            "pressure_curve": pressure_curve,
            "hazard_pattern": hazard_pattern,
            "difficulty": difficulty,
            "score_target": score_target,
            "survival_seconds": survival_seconds,
            "lose_condition": lose_condition,
            "win_condition": win_condition,
            "score_model": self._resolve_score_model(
                mechanic,
                score_target,
                survival_seconds,
                player_ability,
                progression_style,
            ),
            "generation_notes": unsupported_notes,
            "objective": objective,
            "hazard_count": tuning["hazard_count"],
            "collectible_count": tuning["collectible_count"],
            "player_speed": tuning["player_speed"],
            "score_per_collectible": tuning["score_per_collectible"],
            "arena_width": tuning["arena_width"],
            "arena_height": tuning["arena_height"],
        }

    def _plan_text(self, plan: dict[str, Any], key: str) -> str | None:
        value = plan.get(key)
        if not isinstance(value, str):
            return None
        cleaned = " ".join(value.strip().split())
        return cleaned or None

    def _plan_int(self, plan: dict[str, Any], key: str) -> int | None:
        value = plan.get(key)
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value if value >= 0 else None
        if isinstance(value, str) and value.strip().isdigit():
            parsed = int(value.strip())
            return parsed if parsed >= 0 else None
        return None

    def _plan_controls(self, plan: dict[str, Any]) -> dict[str, str] | None:
        value = plan.get("controls")
        if not isinstance(value, dict):
            return None
        resolved: dict[str, str] = {}
        for direction in ("up", "down", "left", "right"):
            raw = value.get(direction)
            if not isinstance(raw, str):
                return None
            cleaned = " ".join(raw.strip().split())
            if not cleaned:
                return None
            resolved[direction] = cleaned
        return resolved

    def _plan_notes(self, plan: dict[str, Any]) -> list[str]:
        raw_notes = plan.get("generation_notes")
        if not isinstance(raw_notes, list):
            return []
        notes: list[str] = []
        for item in raw_notes:
            if not isinstance(item, str):
                continue
            cleaned = " ".join(item.strip().split())
            if cleaned:
                notes.append(cleaned)
        return notes

    def _resolve_rendering_approach(self, framework: str) -> str:
        if framework == "phaser":
            return "Phaser scene with arcade-style physics, framework-managed rendering, and DOM HUD wiring."
        return "HTML5 Canvas with a single requestAnimationFrame update/render loop."

    def _resolve_theme(self, detected: str | None, answer: str | None, prompt: str) -> str:
        if answer:
            return answer.strip()
        if detected:
            return prettify_theme(detected)
        words = [word for word in re.findall(r"[a-zA-Z]+", prompt) if len(word) > 3]
        return words[0].lower() if words else "arcade"

    def _resolve_mechanic(self, detected: str | None, answer: str | None, prompt: str) -> str:
        text = f"{answer or ''} {prompt}".lower()
        has_collect = any(
            word in text for word in ("collect", "collecting", "gather", "pickup", "pick up", "grab", "steal", "retrieve")
        )
        has_dodge = any(
            word in text for word in ("dodge", "dodging", "avoid", "avoiding", "evade", "escape", "outrun")
        )
        has_survive = any(word in text for word in ("survive", "surviving", "survival", "endure", "last"))
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

    def _resolve_player_identity(self, player_entity: str, detected_role: str | None, answer: str | None) -> str:
        if answer:
            return self._normalize_fragment(answer)
        if detected_role:
            return self._normalize_fragment(detected_role)
        return player_entity

    def _resolve_signature_mechanic(
        self,
        answer: str | None,
        detected_special: str | None,
        play_variant: str,
    ) -> str:
        if answer:
            return self._normalize_sentence(answer)
        if detected_special == "dash":
            return "Use short dash bursts to slip through danger."
        if detected_special == "shield":
            return "Manage a timed shield to survive mistakes."
        if detected_special == "magnet":
            return "Use a pickup magnet effect to vacuum rewards into your path."
        if detected_special == "blink":
            return "Blink through tight gaps to keep momentum."
        if detected_special == "double jump":
            return "Chain a double jump to recover from risky jumps."
        defaults = {
            "arena_survival": "Rely on last-second dodges and route changes.",
            "collector_rush": "Plan tight pickup routes before the arena closes in.",
            "collector_escape": "Grab rewards while threading through active danger zones.",
            "chase_escape": "Bait pursuers into bad angles while staying mobile.",
            "lane_dodger": "Snap between lanes to read openings early.",
            "side_runner": "Time jumps cleanly and keep your landing rhythm.",
        }
        return defaults.get(play_variant, "React quickly and make tight movement decisions.")

    def _resolve_progression_style(
        self,
        answer: str | None,
        detected_progression: str | None,
        play_variant: str,
        mechanic: str,
    ) -> str:
        if answer:
            return self._normalize_fragment(answer)
        if detected_progression == "waves":
            return "faster waves"
        if detected_progression == "finale":
            return "a small finale"
        if detected_progression == "ramp":
            return "a steady ramp"
        if detected_progression == "steady":
            return "steady pressure"
        if play_variant == "lane_dodger":
            return "faster traffic waves"
        if play_variant == "side_runner":
            return "escalating obstacle bursts"
        if play_variant in {"collector_escape", "chase_escape"}:
            return "mounting chase pressure"
        if mechanic == "collect":
            return "a route-planning rush"
        return "steady pressure"

    def _resolve_visual_tone(
        self,
        answer: str | None,
        detected_tone: str | None,
        theme: str,
        difficulty: str,
    ) -> str:
        if answer:
            return self._normalize_fragment(answer)
        if detected_tone:
            return detected_tone
        theme_text = theme.lower()
        if "zombie" in theme_text:
            return "tense"
        if "dungeon" in theme_text or "ocean" in theme_text:
            return "mysterious"
        if "sports" in theme_text:
            return "playful"
        if difficulty == "hard":
            return "chaotic"
        return "tense"

    def _resolve_arena_detail(self, answer: str | None, prompt: str, theme: str, play_variant: str) -> str:
        if answer:
            return self._normalize_fragment(answer)
        lower_prompt = prompt.lower()
        location_match = re.search(
            r"(?:in|inside|through|across|around)\s+(?:a|an|the)?\s*([a-z][a-z\s-]+?)(?:[,.]|$)",
            lower_prompt,
        )
        if location_match:
            return self._normalize_fragment(location_match.group(1))
        theme_text = theme.lower()
        if play_variant == "lane_dodger":
            return "busy traffic lanes"
        if play_variant == "side_runner":
            return "a side-scrolling obstacle course"
        if "space" in theme_text:
            return "a drifting asteroid belt"
        if "jungle" in theme_text:
            return "an overgrown temple courtyard"
        if "dungeon" in theme_text:
            return "a trap-filled chamber"
        if "cyber" in theme_text:
            return "a neon security grid"
        if "zombie" in theme_text:
            return "a collapsing safe zone"
        return "a compact arcade arena"

    def _resolve_player_ability(
        self,
        signature_mechanic: str,
        prompt: str,
        answers: dict[str, str],
        movement_model: str,
    ) -> str | None:
        text = f"{signature_mechanic} {prompt} {' '.join(answers.values())}".lower()
        if "double jump" in text or ("extra jump" in text and movement_model == "side_runner"):
            return "double_jump" if movement_model == "side_runner" else None
        if any(word in text for word in ("dash", "boost", "burst", "sprint", "blink", "teleport", "warp")):
            if movement_model in {"top_down_free", "lane_runner"}:
                return "dash"
            return None
        if any(word in text for word in ("shield", "barrier", "magnet", "tractor beam", "vacuum")):
            return None
        return None

    def _resolve_pressure_curve(self, progression_style: str, play_variant: str, difficulty: str) -> str:
        text = progression_style.lower()
        if any(word in text for word in ("wave", "waves", "burst")):
            return "waves"
        if any(word in text for word in ("finale", "boss", "countdown", "final")):
            return "finale"
        if any(word in text for word in ("ramp", "escalat", "mounting", "faster", "intense", "chase")):
            return "ramp"
        if "steady" in text or "calm" in text:
            return "steady"
        if play_variant in {"lane_dodger", "side_runner"}:
            return "waves"
        if difficulty == "hard":
            return "ramp"
        return "steady"

    def _resolve_hazard_pattern(self, progression_style: str, signature_mechanic: str, play_variant: str) -> str:
        text = f"{progression_style} {signature_mechanic}".lower()
        if any(word in text for word in ("zigzag", "weave")):
            return "zigzag"
        if any(word in text for word in ("pulse", "rhythm")):
            return "pulse"
        if any(word in text for word in ("ambush", "burst", "rush")):
            return "burst"
        if any(word in text for word in ("homing", "chase", "hunt")):
            return "homing"
        defaults = {
            "lane_dodger": "zigzag",
            "side_runner": "burst",
            "collector_rush": "pulse",
            "collector_escape": "burst",
            "chase_escape": "homing",
        }
        return defaults.get(play_variant, "direct")

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
        if "cyber" in theme_text:
            return "data core"
        if "zombie" in theme_text:
            return "supply crate"
        if "ocean" in theme_text:
            return "pearl"
        if "dungeon" in theme_text:
            return "rune"
        if "jungle" in theme_text:
            return "relic"
        if "sports" in theme_text:
            return "energy token"
        if "traffic" in theme_text:
            return "bonus token"
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
        if "jungle" in theme_text:
            return "swinging trap"
        if "sports" in theme_text:
            return "defender"
        if "traffic" in theme_text:
            return "car"
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
        if "jungle" in theme_text:
            return "explorer"
        if "sports" in theme_text:
            return "captain"
        if "traffic" in theme_text:
            return "courier"
        return "runner"

    def _resolve_score_model(
        self,
        mechanic: str,
        score_target: int | None,
        survival_seconds: int | None,
        player_ability: str | None,
        progression_style: str,
    ) -> str:
        ability_clause = ""
        if player_ability == "dash":
            ability_clause = " Use the dash to cut through tight gaps."
        elif player_ability == "double_jump":
            ability_clause = " Use the second jump to recover from risky jumps."

        if mechanic == "collect" and score_target:
            return f"Gain 10 points per collectible and reach {score_target} points.{ability_clause}"
        if mechanic == "hybrid" and score_target:
            return f"Gain 10 points per collectible while avoiding hazards until {score_target} points.{ability_clause}"
        if survival_seconds:
            return f"Stay alive until the timer reaches {survival_seconds} seconds while the game leans into {progression_style}.{ability_clause}"
        return f"Score increases only when the main objective is met.{ability_clause}"

    def _resolve_win_condition(
        self,
        mechanic: str,
        score_target: int | None,
        survival_seconds: int | None,
        collectible_entity: str | None,
        progression_style: str,
    ) -> str:
        if score_target and collectible_entity:
            return f"Win by collecting enough {collectible_entity}s to reach {score_target} points."
        if survival_seconds:
            return f"Win by surviving for {survival_seconds} seconds through {progression_style}."
        if mechanic == "dodge":
            return "Win by lasting until the timer expires."
        return "Win when the main objective is complete."

    def _resolve_lose_condition(
        self,
        answer: str | None,
        detected_lose_condition: str | None,
        hazard_entity: str,
    ) -> str:
        if answer:
            return self._normalize_sentence(answer)
        if detected_lose_condition:
            return self._normalize_sentence(detected_lose_condition)
        return f"Lose on contact with a {hazard_entity}."

    def _resolve_objective_sentence(
        self,
        objective_answer: str | None,
        mechanic: str,
        score_target: int | None,
        survival_seconds: int | None,
        collectible_entity: str | None,
        hazard_entity: str,
        player_identity: str,
        signature_mechanic: str,
    ) -> str:
        if objective_answer:
            return self._normalize_sentence(objective_answer)
        identity_fragment = self._normalize_fragment(player_identity)
        if mechanic == "collect" and collectible_entity and score_target:
            return (
                f"Guide the {identity_fragment} through danger, collect {collectible_entity}s, and reach "
                f"{score_target} points. {signature_mechanic}"
            )
        if mechanic == "hybrid" and collectible_entity and score_target:
            return (
                f"Keep the {identity_fragment} moving, grab {collectible_entity}s, dodge {hazard_entity}s, "
                f"and reach {score_target} points. {signature_mechanic}"
            )
        if survival_seconds:
            return (
                f"Help the {identity_fragment} survive against {hazard_entity}s for {survival_seconds} seconds. "
                f"{signature_mechanic}"
            )
        return f"Keep the {identity_fragment} alive while avoiding {hazard_entity}s. {signature_mechanic}"

    def _resolve_play_variant(
        self,
        prompt: str,
        answers: dict[str, str],
        mechanic: str,
        perspective: str,
        theme: str,
    ) -> str:
        combined = f"{prompt} {' '.join(answers.values())}".lower()
        if perspective == "side-view" or any(
            word in combined for word in ("jump", "platform", "platformer", "runner", "side-scrolling", "flappy")
        ):
            return "side_runner"
        if any(word in combined for word in ("traffic", "road", "lane", "highway", "car", "crossy", "crossing")):
            return "lane_dodger"
        if any(word in combined for word in ("escape", "chase", "hunter", "pursuit", "maze")):
            return "chase_escape"
        if theme.lower().startswith("zombie"):
            return "chase_escape"
        if mechanic == "collect":
            return "collector_rush"
        if mechanic == "hybrid":
            return "collector_escape"
        return "arena_survival"

    def _resolve_movement_model(self, play_variant: str) -> str:
        mapping = {
            "arena_survival": "top_down_free",
            "collector_rush": "top_down_free",
            "collector_escape": "top_down_free",
            "chase_escape": "top_down_free",
            "lane_dodger": "lane_runner",
            "side_runner": "side_runner",
        }
        return mapping.get(play_variant, "top_down_free")

    def _resolve_hazard_behavior(self, play_variant: str, hazard_pattern: str) -> str:
        if hazard_pattern == "homing":
            return "seek"
        mapping = {
            "arena_survival": "bounce",
            "collector_rush": "wander",
            "collector_escape": "seek",
            "chase_escape": "seek",
            "lane_dodger": "fall",
            "side_runner": "sweep",
        }
        return mapping.get(play_variant, "bounce")

    def _resolve_collectible_behavior(
        self,
        play_variant: str,
        collectible_entity: str | None,
        signature_mechanic: str,
    ) -> str | None:
        if collectible_entity is None:
            return None
        signature_text = signature_mechanic.lower()
        if "hover" in signature_text or "air" in signature_text:
            return "hover"
        if "magnet" in signature_text or "pulse" in signature_text:
            return "pulse"
        mapping = {
            "collector_rush": "drift",
            "collector_escape": "pulse",
            "lane_dodger": "fall",
            "side_runner": "hover",
        }
        return mapping.get(play_variant, "static")

    def _resolve_arena_layout(self, play_variant: str) -> str:
        mapping = {
            "lane_dodger": "lanes",
            "side_runner": "ground_strip",
        }
        return mapping.get(play_variant, "open_field")

    def _resolve_variant_tuning(
        self,
        play_variant: str,
        difficulty: str,
        has_collectibles: bool,
        pressure_curve: str,
        visual_tone: str,
        player_ability: str | None,
    ) -> dict[str, int]:
        difficulty_index = {"easy": 0, "medium": 1, "hard": 2}[difficulty]

        if play_variant == "lane_dodger":
            tuning = {
                "hazard_count": 5 + difficulty_index,
                "collectible_count": 3 if has_collectibles else 0,
                "player_speed": 320,
                "score_per_collectible": 15,
                "arena_width": 720,
                "arena_height": 640,
            }
        elif play_variant == "side_runner":
            tuning = {
                "hazard_count": 4 + difficulty_index,
                "collectible_count": 4 if has_collectibles else 0,
                "player_speed": 300,
                "score_per_collectible": 20,
                "arena_width": 960,
                "arena_height": 540,
            }
        elif play_variant == "collector_rush":
            tuning = {
                "hazard_count": 2 + difficulty_index,
                "collectible_count": 7,
                "player_speed": 290,
                "score_per_collectible": 15,
                "arena_width": 860,
                "arena_height": 620,
            }
        elif play_variant in {"collector_escape", "chase_escape"}:
            tuning = {
                "hazard_count": 3 + difficulty_index,
                "collectible_count": 5 if has_collectibles else 0,
                "player_speed": 275,
                "score_per_collectible": 15,
                "arena_width": 840,
                "arena_height": 620,
            }
        else:
            tuning = {
                "hazard_count": 3 + difficulty_index,
                "collectible_count": 5 if has_collectibles else 0,
                "player_speed": {"easy": 280, "medium": 260, "hard": 245}[difficulty],
                "score_per_collectible": 10,
                "arena_width": 800,
                "arena_height": 600,
            }

        if pressure_curve in {"ramp", "waves"}:
            tuning["hazard_count"] += 1
        if pressure_curve == "finale":
            tuning["score_per_collectible"] += 5
        if any(word in visual_tone.lower() for word in ("chaotic", "tense")):
            tuning["player_speed"] += 10
        if player_ability in {"dash", "blink"}:
            tuning["player_speed"] += 15
        return tuning

    def _normalize_sentence(self, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            return cleaned
        if cleaned[-1] not in ".!?":
            cleaned += "."
        return cleaned[0].upper() + cleaned[1:]

    def _normalize_fragment(self, value: str) -> str:
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            return cleaned
        return cleaned.rstrip(".")
