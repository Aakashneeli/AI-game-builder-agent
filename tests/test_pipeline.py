from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentic_game_builder.clarification import ClarificationManager
from agentic_game_builder.generator import CodeGenerator
from agentic_game_builder.llm import MockLLMClient
from agentic_game_builder.output import OutputManager
from agentic_game_builder.planner import Planner
from agentic_game_builder.validator import Validator


class ClarificationManagerTests(unittest.TestCase):
    def test_build_questions_is_bounded_and_relevant(self) -> None:
        manager = ClarificationManager()
        questions = manager.build_questions("Make me a simple space survival game.")

        self.assertLessEqual(len(questions), 5)
        self.assertTrue(any(question.key == "perspective" for question in questions))
        self.assertTrue(any(question.key == "controls" for question in questions))


class PlannerTests(unittest.TestCase):
    def test_planner_normalizes_space_survival_prompt(self) -> None:
        planner = Planner(llm_client=MockLLMClient())
        spec = planner.build_spec(
            "Make me a simple space survival game.",
            {
                "perspective": "top-down",
                "controls": "arrow keys",
                "lose_condition": "Lose if an asteroid hits the player.",
            },
        )

        self.assertEqual(spec.core_mechanic, "survive")
        self.assertEqual(spec.perspective, "top-down")
        self.assertEqual(spec.hazard_entity, "asteroid")
        self.assertEqual(spec.survival_seconds, 30)
        self.assertIsNone(spec.score_target)


class GenerationPipelineTests(unittest.TestCase):
    def test_generation_writes_required_files_and_passes_validation(self) -> None:
        planner = Planner(llm_client=MockLLMClient())
        spec = planner.build_spec(
            "Create a jungle game where the player collects relics and dodges traps.",
            {
                "perspective": "top-down",
                "controls": "WASD",
                "lose_condition": "Lose immediately if a trap orb touches the player.",
            },
        )

        generator = CodeGenerator()
        artifacts = generator.generate(spec)
        validator = Validator()
        content_result = validator.validate_artifacts(artifacts)

        self.assertTrue(content_result.passed, content_result.messages)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "game-output"
            OutputManager().write_artifacts(output_dir, artifacts)
            disk_result = validator.validate_directory(output_dir)
            self.assertTrue(disk_result.passed, disk_result.messages)
            self.assertTrue((output_dir / "index.html").exists())
            self.assertTrue((output_dir / "style.css").exists())
            self.assertTrue((output_dir / "game.js").exists())


if __name__ == "__main__":
    unittest.main()
