from __future__ import annotations

from pathlib import Path

from .analysis import slugify


class OutputManager:
    def resolve_target_dir(self, output_dir: str | None, title: str) -> Path:
        if output_dir:
            return Path(output_dir).expanduser().resolve()

        base_dir = Path.cwd() / "generated_games"
        candidate = base_dir / slugify(title)
        if not candidate.exists():
            return candidate

        suffix = 2
        while True:
            numbered = base_dir / f"{slugify(title)}-{suffix}"
            if not numbered.exists():
                return numbered
            suffix += 1

    def write_artifacts(self, target_dir: Path, artifacts: dict[str, str]) -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        for name, contents in artifacts.items():
            (target_dir / name).write_text(contents, encoding="utf-8")
