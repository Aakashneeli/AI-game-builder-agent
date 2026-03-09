from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .clarification import ClarificationManager
from .generator import CodeGenerator
from .llm import MockLLMClient, resolve_llm_client
from .output import OutputManager
from .planner import Planner
from .validator import Validator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Agentic Game Builder MVP")
    parser.add_argument("--prompt", help="Initial game idea prompt.")
    parser.add_argument("--output-dir", help="Directory where generated files will be written.")
    parser.add_argument("--answers-file", help="Optional JSON file containing clarification answers.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    prompt = args.prompt or input("Enter a vague game idea: ").strip()
    if not prompt:
        print("A prompt is required.")
        return 1

    try:
        llm_client, llm_note = resolve_llm_client()
    except RuntimeError as error:
        print(f"LLM configuration issue: {error}")
        print("Falling back to deterministic mock LLM client.")
        llm_client = MockLLMClient()
        llm_note = "Using deterministic mock LLM client."

    print("== Agentic Game Builder MVP ==")
    print(llm_note)
    print("\n[Phase 1/4] Clarify")

    clarification_manager = ClarificationManager()
    questions = clarification_manager.build_questions(prompt)
    try:
        provided_answers = _load_answers_file(args.answers_file)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Unable to read answers file: {error}")
        return 1
    answers: dict[str, str] = {}

    if not questions:
        print("No additional clarification needed. The prompt already contains the minimum implementation details.")
    for question in questions:
        print(f"- {question.reason}")
        answer = provided_answers.get(question.key)
        if answer is None:
            answer = input(f"{question.prompt} ").strip()
        else:
            print(f"{question.prompt} {answer}")
        if answer:
            answers[question.key] = answer

    print("\n[Phase 2/4] Plan")
    planner = Planner(llm_client=llm_client)
    spec = planner.build_spec(prompt, answers)
    print(planner.render_plan(spec))

    print("\n[Phase 3/4] Generate")
    generator = CodeGenerator()
    artifacts = generator.generate(spec)
    validator = Validator()
    artifact_validation = validator.validate_artifacts(artifacts)
    for message in artifact_validation.messages:
        print(f"- {message}")
    if not artifact_validation.passed:
        return 1

    output_manager = OutputManager()
    target_dir = output_manager.resolve_target_dir(args.output_dir, spec.title)
    output_manager.write_artifacts(target_dir, artifacts)

    print("\n[Phase 4/4] Validate")
    directory_validation = validator.validate_directory(target_dir)
    for message in directory_validation.messages:
        print(f"- {message}")
    if not directory_validation.passed:
        return 1

    print(f"\nGenerated game saved to: {target_dir}")
    print("Open index.html in a browser to play the game locally.")
    return 0


def _load_answers_file(path: str | None) -> dict[str, str]:
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("answers file must contain a JSON object.")
    return {str(key): str(value) for key, value in payload.items()}


if __name__ == "__main__":
    raise SystemExit(main())
