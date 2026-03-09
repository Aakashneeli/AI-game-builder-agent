from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentic_game_builder.cli import build_spec_with_fallback
from agentic_game_builder.clarification import ClarificationManager
from agentic_game_builder.framework_selector import FrameworkSelector
from agentic_game_builder.generator import CodeGenerator
from agentic_game_builder.llm import LLMRequestError, MockLLMClient, MultiLLMClient
from agentic_game_builder.output import OutputManager
from agentic_game_builder.planner import Planner
from agentic_game_builder.validator import Validator


class ClarificationManagerTests(unittest.TestCase):
    def test_build_questions_is_bounded_and_relevant(self) -> None:
        manager = ClarificationManager()
        questions = manager.build_questions("Make me a simple space survival game.")

        self.assertLessEqual(len(questions), 7)
        self.assertTrue(any(question.key == "perspective" for question in questions))
        self.assertTrue(any(question.key == "controls" for question in questions))
        self.assertTrue(any(question.key == "player_identity" for question in questions))
        self.assertTrue(any(question.key == "signature_mechanic" for question in questions))
        perspective_question = next(question for question in questions if question.key == "perspective")
        controls_question = next(question for question in questions if question.key == "controls")
        self.assertIn("space survival game", perspective_question.prompt.lower())
        self.assertIn("pilot", controls_question.prompt.lower())

    def test_build_questions_uses_prompt_context_for_collection_game(self) -> None:
        manager = ClarificationManager()
        questions = manager.build_questions("Create a jungle relic collection game.")

        lose_question = next(question for question in questions if question.key == "lose_condition")
        self.assertIn("jungle collection game", lose_question.prompt.lower())
        self.assertTrue(
            "traps" in lose_question.prompt.lower() or "relics" in lose_question.prompt.lower()
        )

    def test_explicit_lose_if_prompt_does_not_reask_lose_condition(self) -> None:
        manager = ClarificationManager()
        questions = manager.build_questions("Make a simple zombie game where you lose if a zombie grabs you.")

        self.assertFalse(any(question.key == "lose_condition" for question in questions))

    def test_llm_selected_questions_are_used_when_valid(self) -> None:
        class ClarifyingLLMClient:
            def create_clarification_questions(self, prompt: str, max_questions: int = 7) -> dict[str, object]:
                return {
                    "questions": [
                        {
                            "key": "objective",
                            "prompt": "Should the heist focus on stealing data cores, hitting marked vault nodes, or escaping with loot?",
                            "reason": "The main loop is still ambiguous.",
                        },
                        {
                            "key": "theme",
                            "prompt": "This redundant question should be filtered.",
                            "reason": "Filtered because theme is already obvious.",
                        },
                    ]
                }

            def create_plan_copy(self, prompt: str, normalized_spec: dict[str, str]) -> dict[str, str]:
                return MockLLMClient().create_plan_copy(prompt, normalized_spec)

        manager = ClarificationManager(llm_client=ClarifyingLLMClient())
        questions = manager.build_questions("Make a cyber neon vault game.")

        self.assertEqual([question.key for question in questions], ["objective"])
        self.assertIn("vault", questions[0].prompt.lower())

    def test_llm_clarification_falls_back_to_heuristics_on_failure(self) -> None:
        class FailingLLMClient:
            def create_clarification_questions(self, prompt: str, max_questions: int = 7) -> dict[str, object]:
                raise LLMRequestError("provider failed")

            def create_plan_copy(self, prompt: str, normalized_spec: dict[str, str]) -> dict[str, str]:
                return MockLLMClient().create_plan_copy(prompt, normalized_spec)

        manager = ClarificationManager(llm_client=FailingLLMClient())
        questions = manager.build_questions("Make me a simple space survival game.")

        self.assertTrue(any(question.key == "perspective" for question in questions))
        self.assertTrue(any("pilot" in question.prompt.lower() for question in questions))


class FrameworkSelectorTests(unittest.TestCase):
    def test_selects_phaser_for_side_view_runner_ideas(self) -> None:
        decision = FrameworkSelector().select(
            "Make a side-view jungle runner where the player jumps over traps.",
            {"perspective": "side-view"},
        )
        self.assertEqual(decision.framework, "phaser")

    def test_selects_vanilla_for_simple_top_down_survival(self) -> None:
        decision = FrameworkSelector().select(
            "Make me a simple space survival game.",
            {"perspective": "top-down"},
        )
        self.assertEqual(decision.framework, "vanilla_js")


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
        self.assertEqual(spec.play_variant, "arena_survival")
        self.assertEqual(spec.player_identity, "pilot")

    def test_planner_chooses_different_variants_for_different_prompt_shapes(self) -> None:
        planner = Planner(llm_client=MockLLMClient())

        lane_spec = planner.build_spec(
            "Make a traffic dodging game where the player crosses busy lanes.",
            {
                "controls": "arrow keys",
                "lose_condition": "Lose if a car hits the player.",
            },
        )
        side_spec = planner.build_spec(
            "Make a side-view jungle runner where the player jumps over traps.",
            {
                "controls": "WASD",
                "lose_condition": "Lose if a trap hits the player.",
            },
        )
        collect_spec = planner.build_spec(
            "Create a dungeon relic collection game.",
            {
                "perspective": "top-down",
                "controls": "WASD",
                "lose_condition": "Lose if a trap orb touches the player.",
            },
        )

        self.assertEqual(lane_spec.core_mechanic, "dodge")
        self.assertEqual(lane_spec.play_variant, "lane_dodger")
        self.assertEqual(side_spec.play_variant, "side_runner")
        self.assertEqual(collect_spec.play_variant, "collector_rush")

    def test_planner_preserves_personalization_answers(self) -> None:
        planner = Planner(llm_client=MockLLMClient())
        spec = planner.build_spec(
            "Make a cyber collection game about stealing data.",
            {
                "perspective": "top-down",
                "controls": "WASD",
                "lose_condition": "Lose if security drones corner the player.",
                "player_identity": "freelance courier",
                "signature_mechanic": "Use a short dash burst to steal data caches.",
                "progression_style": "faster waves",
                "visual_tone": "mysterious",
                "arena_detail": "a neon archive vault",
            },
        )

        self.assertEqual(spec.player_identity, "freelance courier")
        self.assertEqual(spec.player_ability, "dash")
        self.assertEqual(spec.pressure_curve, "waves")
        self.assertEqual(spec.visual_tone, "mysterious")
        self.assertEqual(spec.arena_detail, "a neon archive vault")
        self.assertEqual(spec.hazard_pattern, "burst")

    def test_planner_treats_heist_language_as_collection_or_hybrid(self) -> None:
        planner = Planner(llm_client=MockLLMClient())
        spec = planner.build_spec(
            "Make a cyber heist game about stealing data while dodging drones.",
            {
                "perspective": "top-down",
                "controls": "WASD",
                "lose_condition": "Lose if a security drone tags the player.",
            },
        )

        self.assertEqual(spec.core_mechanic, "hybrid")
        self.assertEqual(spec.play_variant, "collector_escape")
        self.assertEqual(spec.collectible_entity, "data core")

    def test_cli_falls_back_to_mock_when_live_llm_fails(self) -> None:
        class FailingLLMClient:
            def create_plan_copy(self, prompt: str, normalized_spec: dict[str, str]) -> dict[str, str]:
                raise LLMRequestError("HTTP 429 from provider", status_code=429, retriable=True)

        spec, messages = build_spec_with_fallback(
            "Make me a simple space survival game.",
            {
                "perspective": "top-down",
                "controls": "arrow keys",
                "lose_condition": "Lose if an asteroid hits the player.",
            },
            "vanilla_js",
            FailingLLMClient(),
        )

        self.assertEqual(spec.core_mechanic, "survive")
        self.assertEqual(spec.hazard_entity, "asteroid")
        self.assertEqual(len(messages), 2)
        self.assertIn("failed", messages[0].lower())
        self.assertIn("falling back", messages[1].lower())

    def test_multi_llm_client_uses_second_provider_after_first_fails(self) -> None:
        class FailingLLMClient:
            def create_clarification_questions(self, prompt: str, max_questions: int = 7) -> dict[str, object]:
                raise LLMRequestError("HTTP 429 from primary provider", status_code=429, retriable=True)

            def create_plan_copy(self, prompt: str, normalized_spec: dict[str, str]) -> dict[str, str]:
                raise LLMRequestError("HTTP 429 from primary provider", status_code=429, retriable=True)

        multi_client = MultiLLMClient(
            [
                ("Primary", FailingLLMClient()),
                ("Secondary", MockLLMClient()),
            ]
        )

        planner = Planner(llm_client=multi_client)
        spec = planner.build_spec(
            "Make me a simple space survival game.",
            {
                "perspective": "top-down",
                "controls": "arrow keys",
                "lose_condition": "Lose if an asteroid hits the player.",
            },
        )

        self.assertEqual(spec.title, "Space Survival Challenge")
        self.assertEqual(spec.hazard_entity, "asteroid")
        self.assertEqual(multi_client.last_success_label, "Secondary")


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

    def test_generation_embeds_variant_specific_runtime_config(self) -> None:
        planner = Planner(llm_client=MockLLMClient())
        lane_spec = planner.build_spec(
            "Make a traffic dodging game where the player crosses busy lanes.",
            {
                "controls": "arrow keys",
                "lose_condition": "Lose if a car hits the player.",
            },
        )
        side_spec = planner.build_spec(
            "Make a side-view jungle runner where the player jumps over traps.",
            {
                "controls": "WASD",
                "lose_condition": "Lose if a trap hits the player.",
            },
        )

        generator = CodeGenerator()
        lane_artifacts = generator.generate(lane_spec)
        side_artifacts = generator.generate(side_spec)

        self.assertIn('"variant": "lane_dodger"', lane_artifacts["game.js"])
        self.assertIn('"movementModel": "lane_runner"', lane_artifacts["game.js"])
        self.assertIn('"variant": "side_runner"', side_artifacts["game.js"])
        self.assertIn('"movementModel": "side_runner"', side_artifacts["game.js"])

    def test_generation_embeds_personalization_runtime_config(self) -> None:
        planner = Planner(llm_client=MockLLMClient())
        spec = planner.build_spec(
            "Make a cyber collection game about stealing data.",
            {
                "perspective": "top-down",
                "controls": "WASD",
                "lose_condition": "Lose if security drones corner the player.",
                "player_identity": "freelance courier",
                "signature_mechanic": "Use a short dash burst to steal data caches.",
                "progression_style": "faster waves",
                "visual_tone": "mysterious",
                "arena_detail": "a neon archive vault",
            },
        )

        artifacts = CodeGenerator().generate(spec)

        self.assertIn('"playerIdentity": "freelance courier"', artifacts["game.js"])
        self.assertIn('"playerAbility": "dash"', artifacts["game.js"])
        self.assertIn('"pressureCurve": "waves"', artifacts["game.js"])
        self.assertIn('"hazardPattern": "burst"', artifacts["game.js"])
        self.assertIn("Press Shift or E to dash", artifacts["index.html"])
        self.assertIn("You play as freelance courier", artifacts["index.html"])
        self.assertNotIn("pressureFactor(", artifacts["game.js"])
        self.assertNotIn("shieldActive(", artifacts["game.js"])

    def test_generation_uses_phaser_runtime_when_framework_selected(self) -> None:
        planner = Planner(llm_client=MockLLMClient())
        spec = planner.build_spec(
            "Make a side-view jungle runner where the player jumps over traps.",
            {
                "controls": "WASD",
                "lose_condition": "Lose if a trap hits the player.",
            },
            framework="phaser",
        )

        generator = CodeGenerator()
        artifacts = generator.generate(spec)

        self.assertIn("cdn.jsdelivr.net/npm/phaser", artifacts["index.html"])
        self.assertIn("new Phaser.Game", artifacts["game.js"])
        self.assertIn('"framework": "phaser"', artifacts["game.js"])


if __name__ == "__main__":
    unittest.main()
