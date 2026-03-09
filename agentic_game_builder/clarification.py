from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .analysis import (
    PromptSignals,
    analyze_prompt,
    extract_focus_terms,
    extract_location_phrase,
    extract_object_after_keywords,
    prettify_theme,
)
from .llm import LLMRequestError
from .models import ClarificationQuestion


@dataclass(slots=True)
class ClarificationContext:
    prompt_lower: str
    idea_label: str
    theme_label: str
    player_label: str
    hazard_label: str
    collectible_label: str
    prompt_focus: str | None
    location_hint: str | None
    role_hint: str | None
    threat_hint: str | None
    reward_hint: str | None
    motion_hint: str


class ClarificationManager:
    MAX_QUESTIONS = 7
    ALLOWED_KEYS = {
        "theme",
        "objective",
        "perspective",
        "controls",
        "lose_condition",
        "player_identity",
        "signature_mechanic",
        "progression_style",
        "visual_tone",
        "arena_detail",
    }

    def __init__(self, llm_client: Any | None = None) -> None:
        self.llm_client = llm_client

    def build_questions(self, prompt: str) -> list[ClarificationQuestion]:
        signals = analyze_prompt(prompt)
        context = self._build_context(prompt, signals)
        heuristic_questions = self._build_heuristic_questions(prompt, signals, context)
        llm_questions = self._build_llm_questions(prompt, signals, context)
        if llm_questions is not None and (llm_questions or not heuristic_questions):
            return llm_questions
        return heuristic_questions

    def _build_llm_questions(
        self,
        prompt: str,
        signals: PromptSignals,
        context: ClarificationContext,
    ) -> list[ClarificationQuestion] | None:
        if self.llm_client is None:
            return None
        try:
            payload = self.llm_client.create_clarification_questions(prompt, max_questions=self.MAX_QUESTIONS)
        except (AttributeError, LLMRequestError, TypeError, ValueError):
            return None
        raw_questions = payload.get("questions")
        if not isinstance(raw_questions, list):
            return None
        questions: list[ClarificationQuestion] = []
        seen: set[str] = set()
        for item in raw_questions:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key", "")).strip()
            prompt_text = str(item.get("prompt", "")).strip()
            reason = str(item.get("reason", "")).strip() or "This answer will make the generated game more specific."
            if key not in self.ALLOWED_KEYS or key in seen or not prompt_text:
                continue
            if not self._should_ask_key(key, signals, context):
                continue
            seen.add(key)
            questions.append(ClarificationQuestion(key=key, prompt=prompt_text, reason=reason))
            if len(questions) >= self.MAX_QUESTIONS:
                break
        return questions

    def _build_heuristic_questions(
        self,
        prompt: str,
        signals: PromptSignals,
        context: ClarificationContext,
    ) -> list[ClarificationQuestion]:
        questions: list[ClarificationQuestion] = []

        if not signals.theme:
            questions.append(
                ClarificationQuestion(
                    key="theme",
                    prompt=self._build_theme_prompt(context),
                    reason="Theme is missing and affects naming, visuals, and entity choices.",
                )
            )

        if not signals.core_mechanic:
            questions.append(
                ClarificationQuestion(
                    key="objective",
                    prompt=self._build_objective_prompt(context, signals.unsupported_features),
                    reason="The core loop is still too ambiguous for a personalized game plan.",
                )
            )

        if not signals.perspective:
            questions.append(
                ClarificationQuestion(
                    key="perspective",
                    prompt=self._build_perspective_prompt(context),
                    reason="Perspective changes layout, movement, and framework choice.",
                )
            )

        if not signals.controls:
            questions.append(
                ClarificationQuestion(
                    key="controls",
                    prompt=self._build_controls_prompt(context),
                    reason="Controls affect generated instructions and the runtime input model.",
                )
            )

        if not signals.lose_condition:
            questions.append(
                ClarificationQuestion(
                    key="lose_condition",
                    prompt=self._build_lose_condition_prompt(context),
                    reason="A clear fail state is needed before code generation.",
                )
            )

        if not signals.player_role:
            questions.append(
                ClarificationQuestion(
                    key="player_identity",
                    prompt=self._build_player_identity_prompt(context),
                    reason="The player fantasy should feel specific instead of generic.",
                )
            )

        if not signals.special_mechanic:
            questions.append(
                ClarificationQuestion(
                    key="signature_mechanic",
                    prompt=self._build_signature_mechanic_prompt(context),
                    reason="A signature hook helps the generated game feel less template-like.",
                )
            )

        if not signals.progression_hint:
            questions.append(
                ClarificationQuestion(
                    key="progression_style",
                    prompt=self._build_progression_prompt(context),
                    reason="Pacing and escalation should match the idea, not just a default loop.",
                )
            )

        if not signals.tone:
            questions.append(
                ClarificationQuestion(
                    key="visual_tone",
                    prompt=self._build_tone_prompt(context),
                    reason="Tone helps the game feel closer to the requested mood.",
                )
            )

        if self._needs_arena_detail(context):
            questions.append(
                ClarificationQuestion(
                    key="arena_detail",
                    prompt=self._build_arena_prompt(context),
                    reason="A specific stage or location helps the output feel more custom.",
                )
            )

        return questions[: self.MAX_QUESTIONS]

    def _should_ask_key(
        self,
        key: str,
        signals: PromptSignals,
        context: ClarificationContext,
    ) -> bool:
        if key == "theme":
            return not signals.theme
        if key == "objective":
            return not signals.core_mechanic
        if key == "perspective":
            return not signals.perspective
        if key == "controls":
            return not signals.controls
        if key == "lose_condition":
            return not signals.lose_condition
        if key == "player_identity":
            return not signals.player_role
        if key == "signature_mechanic":
            return not signals.special_mechanic
        if key == "progression_style":
            return not signals.progression_hint
        if key == "visual_tone":
            return not signals.tone
        if key == "arena_detail":
            return self._needs_arena_detail(context)
        return False

    def _build_context(self, prompt: str, signals: PromptSignals) -> ClarificationContext:
        theme_label = prettify_theme(signals.theme)
        player_label, hazard_label, collectible_label = self._theme_entities(signals.theme)
        mechanic_label = self._mechanic_phrase(signals.core_mechanic)
        focus_terms = extract_focus_terms(prompt, limit=4)
        prompt_focus = " ".join(focus_terms) if focus_terms else None

        if signals.theme and mechanic_label:
            idea_label = f"{theme_label} {mechanic_label} game"
        elif signals.theme:
            idea_label = f"{theme_label} game"
        elif mechanic_label:
            idea_label = f"{mechanic_label} game"
        elif prompt_focus:
            idea_label = f"game idea about {prompt_focus}"
        else:
            idea_label = "game idea"

        role_hint = signals.player_role or player_label
        threat_hint = extract_object_after_keywords(prompt, ("avoid", "dodge", "escape from", "outrun"))
        reward_hint = extract_object_after_keywords(prompt, ("collect", "grab", "steal", "retrieve", "gather"))
        return ClarificationContext(
            prompt_lower=prompt.lower(),
            idea_label=idea_label,
            theme_label=theme_label,
            player_label=player_label,
            hazard_label=threat_hint or hazard_label,
            collectible_label=reward_hint or collectible_label,
            prompt_focus=prompt_focus,
            location_hint=extract_location_phrase(prompt),
            role_hint=role_hint,
            threat_hint=threat_hint or hazard_label,
            reward_hint=reward_hint or collectible_label,
            motion_hint=self._motion_hint(prompt.lower(), signals.perspective),
        )

    def _build_theme_prompt(self, context: ClarificationContext) -> str:
        if context.prompt_focus:
            return (
                f'I can shape this around "{context.prompt_focus}", but what overall setting should it actually use so the player, threats, and rewards feel coherent?'
            )
        return "What setting should this game lean into so the world, threats, and rewards all belong to the same place?"

    def _build_objective_prompt(self, context: ClarificationContext, unsupported_features: list[str]) -> str:
        prefix = ""
        if unsupported_features:
            prefix = (
                f"I’m simplifying the {', '.join(unsupported_features)} parts into a compact browser game. "
            )
        if self._is_heist_prompt(context):
            return (
                prefix
                + f"Should this run mainly be about stealing {context.reward_hint}, slipping past {context.threat_hint} to marked vault points, or stealing first and escaping after?"
            )
        if self._is_lane_prompt(context):
            return (
                prefix
                + f"Is the main loop here crossing to safe markers, dodging {context.threat_hint} for a timer, or weaving in pickups between crossings?"
            )
        if self._is_runner_prompt(context):
            return (
                prefix
                + f"Should this course focus on chaining jumps through {context.threat_hint}, collecting {context.reward_hint} on the route, or doing both in one run?"
            )
        return (
            prefix
            + f"What should the player mainly be doing in this {context.idea_label}: dodging {context.threat_hint}, collecting {context.reward_hint}, surviving a timer, or mixing those together?"
        )

    def _build_perspective_prompt(self, context: ClarificationContext) -> str:
        if self._is_runner_prompt(context):
            return (
                f"I’m reading this as movement-heavy course play. Should it stay side-view, or do you actually want a top-down or static-screen take on this {context.idea_label}?"
            )
        if self._is_lane_prompt(context):
            return (
                f"For this {context.idea_label}, do you want the crossings seen top-down, side-view, or as a single fixed-screen road?"
            )
        return f"For this {context.idea_label}, should the action read as top-down, side-view, or static-screen?"

    def _build_controls_prompt(self, context: ClarificationContext) -> str:
        if self._is_runner_prompt(context):
            return (
                f"How should the {context.role_hint} move through the course: A/D plus jump, full WASD, or arrows plus jump?"
            )
        if self._is_lane_prompt(context):
            return (
                f"How should lane changes feel for the {context.role_hint}: arrow keys, WASD, or mouse steering?"
            )
        return f"How should the {context.role_hint} move in this {context.idea_label}: arrow keys, WASD, or mouse?"

    def _build_lose_condition_prompt(self, context: ClarificationContext) -> str:
        if self._is_heist_prompt(context):
            return (
                f"What should count as failure here: getting tagged by {context.threat_hint}, running out of time mid-heist, or blowing too many chances?"
            )
        if self._is_lane_prompt(context):
            return (
                f"What should end the run: one hit from {context.threat_hint}, a missed crossing window, or the timer expiring?"
            )
        return (
            f"What should make the player fail in this {context.idea_label}: touching {context.threat_hint}, running out of time, missing too many targets, or something else?"
        )

    def _build_player_identity_prompt(self, context: ClarificationContext) -> str:
        if self._is_heist_prompt(context):
            return (
                f"Who should the player actually be in this run: a courier, infiltrator, drone pilot, or some other specific role?"
            )
        return (
            f"Who or what should the player control in this {context.idea_label}: a nimble {context.player_label}, a named hero, a vehicle, or something more specific?"
        )

    def _build_signature_mechanic_prompt(self, context: ClarificationContext) -> str:
        if self._is_runner_prompt(context):
            return (
                f"What single movement twist should define this version: a double jump, a short air dash, a burst sprint, or another clean one-button trick?"
            )
        if self._is_heist_prompt(context):
            return (
                f"What single hook should make this heist feel like yours: a short dash, a burst sprint, a double jump, or another clean movement trick?"
            )
        return (
            f"What single twist should make this {context.idea_label} feel like your version: a short dash, double jump, burst sprint, or another clean hook?"
        )

    def _build_progression_prompt(self, context: ClarificationContext) -> str:
        if self._is_heist_prompt(context):
            return (
                f"How should pressure build here: patrol waves, steadily rising alarm pressure, or a last escape push near the end?"
            )
        if self._is_runner_prompt(context):
            return (
                f"How should the course build difficulty: steady escalation, short obstacle bursts, or a final stretch that gets nastier at the end?"
            )
        if self._is_lane_prompt(context):
            return (
                f"How should traffic pressure build: readable waves, a steady speed-up, or a final rush before the finish?"
            )
        return (
            f"How should challenge build in this {context.idea_label}: steady pressure, faster waves, a chase phase, a countdown finish, or a small finale?"
        )

    def _build_tone_prompt(self, context: ClarificationContext) -> str:
        if self._is_heist_prompt(context):
            return (
                "What mood should the game lean into: sleek, tense, mysterious, chaotic, or something else?"
            )
        if self._is_runner_prompt(context):
            return "What mood should the run lean into: playful, tense, adventurous, chaotic, or something else?"
        return (
            f"What mood should this {context.idea_label} lean into: cozy, tense, mysterious, playful, chaotic, or something else?"
        )

    def _build_arena_prompt(self, context: ClarificationContext) -> str:
        if self._is_heist_prompt(context):
            return (
                "What exact location should the action use: a neon archive vault, rooftop relay, server corridor, or another secured site?"
            )
        if self._is_lane_prompt(context):
            return (
                "What street setup fits best: busy city lanes, a night expressway, a school crossing, or another road scene?"
            )
        if self._is_runner_prompt(context):
            return (
                "What specific course or stretch should the run happen in: a temple courtyard, cliffside trail, rooftop route, or somewhere else?"
            )
        return (
            f"What specific location should the action happen in for this {context.idea_label}: an asteroid belt, temple courtyard, neon lab, traffic lanes, ruined arena, or something else?"
        )

    def _theme_entities(self, theme_key: str | None) -> tuple[str, str, str]:
        mapping = {
            "space": ("pilot", "asteroids", "fuel cells"),
            "zombie": ("survivor", "zombies", "supply crates"),
            "dungeon": ("adventurer", "traps", "runes"),
            "ocean": ("diver", "mines", "pearls"),
            "jungle": ("explorer", "traps", "relics"),
            "cyber": ("runner", "security drones", "data cores"),
            "sports": ("captain", "defenders", "boost tokens"),
            "traffic": ("courier", "cars", "bonus tokens"),
        }
        return mapping.get(theme_key or "", ("player", "hazards", "pickups"))

    def _mechanic_phrase(self, mechanic_key: str | None) -> str | None:
        mapping = {
            "collect": "collection",
            "dodge": "dodging",
            "survive": "survival",
            "hybrid": "arcade",
        }
        return mapping.get(mechanic_key)

    def _needs_arena_detail(self, context: ClarificationContext) -> bool:
        if context.location_hint:
            return False
        location_words = {
            "arena",
            "belt",
            "bridge",
            "cave",
            "city",
            "courtyard",
            "dungeon",
            "field",
            "forest",
            "highway",
            "lab",
            "lane",
            "lanes",
            "road",
            "route",
            "ruins",
            "server",
            "station",
            "temple",
            "tower",
            "trail",
            "vault",
            "yard",
        }
        prompt_words = {word.lower() for word in re.findall(r"[A-Za-z]+", context.prompt_lower)}
        return not bool(prompt_words & location_words)

    def _motion_hint(self, lower_prompt: str, detected_perspective: str | None) -> str:
        if detected_perspective == "side-view" or any(word in lower_prompt for word in ("jump", "runner", "platform", "course")):
            return "runner"
        if any(word in lower_prompt for word in ("traffic", "lane", "crossing", "highway", "road")):
            return "lanes"
        if any(word in lower_prompt for word in ("heist", "vault", "steal", "data", "drone")):
            return "heist"
        return "free"

    def _is_heist_prompt(self, context: ClarificationContext) -> bool:
        return context.motion_hint == "heist" or any(
            word in context.prompt_lower for word in ("heist", "vault", "data", "security drone", "archive")
        )

    def _is_lane_prompt(self, context: ClarificationContext) -> bool:
        return context.motion_hint == "lanes"

    def _is_runner_prompt(self, context: ClarificationContext) -> bool:
        return context.motion_hint == "runner"
