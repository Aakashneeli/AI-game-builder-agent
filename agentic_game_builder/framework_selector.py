from __future__ import annotations

from .models import FrameworkDecision


class FrameworkSelector:
    def select(self, prompt: str, answers: dict[str, str]) -> FrameworkDecision:
        combined = f"{prompt} {' '.join(answers.values())}".lower()

        if "phaser" in combined:
            return FrameworkDecision(
                framework="phaser",
                reason="The prompt explicitly asks for Phaser.",
            )

        if any(phrase in combined for phrase in ("vanilla js", "vanilla javascript", "plain javascript", "no framework")):
            return FrameworkDecision(
                framework="vanilla_js",
                reason="The prompt explicitly asks for a vanilla JavaScript implementation.",
            )

        phaser_triggers = (
            "side-view",
            "side view",
            "platformer",
            "platform",
            "jump",
            "jumping",
            "runner",
            "side-scroller",
            "side scroller",
            "gravity",
            "physics",
            "flappy",
        )
        if any(trigger in combined for trigger in phaser_triggers):
            return FrameworkDecision(
                framework="phaser",
                reason="The game idea leans on side-view movement, jumping, or physics-style motion, which Phaser handles more naturally.",
            )

        return FrameworkDecision(
            framework="vanilla_js",
            reason="A small 2D browser game without strong physics needs is simpler and more inspectable in vanilla JavaScript.",
        )
