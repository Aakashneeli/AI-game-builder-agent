from __future__ import annotations

from pathlib import Path

from .models import ValidationResult


class Validator:
    REQUIRED_FILES = ("index.html", "style.css", "game.js")

    def validate_artifacts(self, artifacts: dict[str, str]) -> ValidationResult:
        messages: list[str] = []
        missing = [name for name in self.REQUIRED_FILES if name not in artifacts]
        if missing:
            messages.append(f"Missing generated files: {', '.join(missing)}.")
        html = artifacts.get("index.html", "")
        js = artifacts.get("game.js", "")
        if 'href="style.css"' not in html:
            messages.append("index.html does not reference style.css.")
        if 'src="game.js"' not in html:
            messages.append("index.html does not reference game.js.")
        if "requestAnimationFrame" not in js:
            messages.append("game.js does not contain a requestAnimationFrame loop.")
        if "resetGame" not in js:
            messages.append("game.js does not include restart capability.")
        return ValidationResult(passed=not messages, messages=messages or ["Generated artifacts passed content validation."])

    def validate_directory(self, target_dir: Path) -> ValidationResult:
        messages: list[str] = []
        for name in self.REQUIRED_FILES:
            if not (target_dir / name).exists():
                messages.append(f"{name} was not written to {target_dir}.")
        return ValidationResult(passed=not messages, messages=messages or [f"Output directory ready at {target_dir}."])
