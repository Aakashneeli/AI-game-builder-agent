from __future__ import annotations

import re
from dataclasses import dataclass

from .analysis import PromptSignals, analyze_prompt, prettify_theme
from .models import ClarificationQuestion


@dataclass(slots=True)
class ClarificationContext:
    idea_label: str
    theme_label: str
    player_label: str
    hazard_label: str
    collectible_label: str
    prompt_focus: str | None


class ClarificationManager:
    MAX_QUESTIONS = 7

    def build_questions(self, prompt: str) -> list[ClarificationQuestion]:
        signals = analyze_prompt(prompt)
        context = self._build_context(prompt, signals)
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

        if self._needs_arena_detail(prompt):
            questions.append(
                ClarificationQuestion(
                    key="arena_detail",
                    prompt=self._build_arena_prompt(context),
                    reason="A specific stage or location helps the output feel more custom.",
                )
            )

        return questions[: self.MAX_QUESTIONS]

    def _build_context(self, prompt: str, signals: PromptSignals) -> ClarificationContext:
        theme_label = prettify_theme(signals.theme)
        player_label, hazard_label, collectible_label = self._theme_entities(signals.theme)
        mechanic_label = self._mechanic_phrase(signals.core_mechanic)
        prompt_focus = self._prompt_focus(prompt)

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

        return ClarificationContext(
            idea_label=idea_label,
            theme_label=theme_label,
            player_label=player_label,
            hazard_label=hazard_label,
            collectible_label=collectible_label,
            prompt_focus=prompt_focus,
        )

    def _build_theme_prompt(self, context: ClarificationContext) -> str:
        if context.prompt_focus:
            return (
                f'What setting should this "{context.prompt_focus}" game lean into so the player, obstacles, and pickups feel coherent?'
            )
        return "What theme or setting should the game use so the world and entities feel coherent?"

    def _build_objective_prompt(self, context: ClarificationContext, unsupported_features: list[str]) -> str:
        if unsupported_features:
            return (
                f"Your prompt includes {', '.join(unsupported_features)} ideas. For the small browser version, "
                f"what should the player mainly do in this {context.idea_label}: dodge {context.hazard_label}, "
                f"collect {context.collectible_label}, survive a timer, or combine a few of those?"
            )
        return (
            f"What should the player mainly do in this {context.idea_label}: dodge {context.hazard_label}, "
            f"collect {context.collectible_label}, survive a timer, or combine a few of those?"
        )

    def _build_perspective_prompt(self, context: ClarificationContext) -> str:
        return f"For this {context.idea_label}, should the action be top-down, side-view, or static-screen?"

    def _build_controls_prompt(self, context: ClarificationContext) -> str:
        return f"How should the {context.player_label} move in this {context.idea_label}: arrow keys, WASD, or mouse?"

    def _build_lose_condition_prompt(self, context: ClarificationContext) -> str:
        return (
            f"What should make the player fail in this {context.idea_label}: touching {context.hazard_label}, "
            "running out of time, missing too many targets, or something else?"
        )

    def _build_player_identity_prompt(self, context: ClarificationContext) -> str:
        return (
            f"Who or what should the player control in this {context.idea_label}: a nimble {context.player_label}, "
            "a custom hero, a vehicle, or something else?"
        )

    def _build_signature_mechanic_prompt(self, context: ClarificationContext) -> str:
        return (
            f"What single twist should make this {context.idea_label} feel like your version: a short dash, shield, "
            "magnet-style pickup pull, double jump, teleport, or another hook?"
        )

    def _build_progression_prompt(self, context: ClarificationContext) -> str:
        return (
            f"How should the challenge build in this {context.idea_label}: steady pressure, faster waves, a chase "
            "phase, a countdown finish, or a small finale?"
        )

    def _build_tone_prompt(self, context: ClarificationContext) -> str:
        return (
            f"What mood should this {context.idea_label} lean into: cozy, tense, mysterious, playful, chaotic, "
            "or something else?"
        )

    def _build_arena_prompt(self, context: ClarificationContext) -> str:
        return (
            f"What specific location should the action happen in for this {context.idea_label}: an asteroid belt, "
            "temple courtyard, neon lab, traffic lanes, ruined arena, or something else?"
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

    def _needs_arena_detail(self, prompt: str) -> bool:
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
            "ruins",
            "station",
            "temple",
            "tower",
            "yard",
        }
        prompt_words = {word.lower() for word in re.findall(r"[A-Za-z]+", prompt)}
        return not bool(prompt_words & location_words)

    def _prompt_focus(self, prompt: str) -> str | None:
        stopwords = {
            "a",
            "an",
            "and",
            "browser",
            "build",
            "create",
            "for",
            "game",
            "idea",
            "make",
            "me",
            "simple",
            "small",
            "the",
        }
        words = [word.lower() for word in re.findall(r"[A-Za-z]+", prompt)]
        filtered = [word for word in words if word not in stopwords and len(word) > 2]
        if not filtered:
            return None
        return " ".join(filtered[:4])
