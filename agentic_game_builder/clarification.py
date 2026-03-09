from __future__ import annotations

from .analysis import analyze_prompt
from .models import ClarificationQuestion


class ClarificationManager:
    MAX_QUESTIONS = 5

    def build_questions(self, prompt: str) -> list[ClarificationQuestion]:
        signals = analyze_prompt(prompt)
        questions: list[ClarificationQuestion] = []

        if not signals.theme:
            questions.append(
                ClarificationQuestion(
                    key="theme",
                    prompt="What theme or setting should the game use?",
                    reason="Theme is missing and affects naming and visuals.",
                )
            )

        if not signals.core_mechanic:
            questions.append(
                ClarificationQuestion(
                    key="objective",
                    prompt="What should the player mainly do: collect, dodge, survive, or some combination?",
                    reason="The core loop is ambiguous.",
                )
            )

        if not signals.perspective:
            questions.append(
                ClarificationQuestion(
                    key="perspective",
                    prompt="Should the game be top-down, side-view, or static-screen?",
                    reason="Perspective influences the generated layout and motion.",
                )
            )

        if not signals.controls:
            questions.append(
                ClarificationQuestion(
                    key="controls",
                    prompt="What controls should the player use? For example: arrow keys, WASD, or mouse.",
                    reason="Controls are required for the generated instructions and input handling.",
                )
            )

        if not signals.lose_condition:
            questions.append(
                ClarificationQuestion(
                    key="lose_condition",
                    prompt="What should cause the player to lose or fail?",
                    reason="A clear lose condition is needed before code generation.",
                )
            )

        return questions[: self.MAX_QUESTIONS]
