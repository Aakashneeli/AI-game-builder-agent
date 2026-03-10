from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentic_game_builder.cli import build_spec_with_fallback
from agentic_game_builder.clarification import ClarificationManager
from agentic_game_builder.framework_selector import FrameworkSelector
from agentic_game_builder.generator import CodeGenerator
from agentic_game_builder.llm import (
    LLMRequestError,
    MockLLMClient,
    MultiLLMClient,
    OpenAICompatibleLLMClient,
    resolve_role_llm_clients,
)
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


class LLMResolutionTests(unittest.TestCase):
    def test_role_resolution_uses_groq_for_design_and_openrouter_for_codegen(self) -> None:
        with patch.dict(
            os.environ,
            {
                "AIGB_GROQ_API_KEY": "groq-test-key",
                "AIGB_GROQ_PRIMARY_MODEL": "openai/gpt-oss-120b",
                "AIGB_OPENROUTER_API_KEY": "openrouter-test-key",
                "AIGB_OPENROUTER_MODEL": "qwen/qwen3-coder:free",
            },
            clear=True,
        ):
            clients = resolve_role_llm_clients()

        self.assertIs(clients.clarification_client, clients.planning_client)
        self.assertIsInstance(clients.clarification_client, OpenAICompatibleLLMClient)
        self.assertIsInstance(clients.code_generation_client, OpenAICompatibleLLMClient)
        self.assertEqual(clients.clarification_client.model, "openai/gpt-oss-120b")
        self.assertEqual(clients.code_generation_client.model, "qwen/qwen3-coder:free")
        self.assertTrue(any("Groq openai/gpt-oss-120b" in note for note in clients.notes))
        self.assertTrue(any("OpenRouter qwen/qwen3-coder:free" in note for note in clients.notes))

    def test_role_resolution_uses_mock_clients_when_mock_provider_is_forced(self) -> None:
        with patch.dict(os.environ, {"AIGB_PROVIDER": "mock"}, clear=True):
            clients = resolve_role_llm_clients()

        self.assertIsInstance(clients.clarification_client, MockLLMClient)
        self.assertIsInstance(clients.planning_client, MockLLMClient)
        self.assertIsInstance(clients.code_generation_client, MockLLMClient)


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

    def test_planner_uses_structured_llm_plan_when_available(self) -> None:
        class StructuredPlanningLLMClient:
            def create_game_plan(
                self,
                prompt: str,
                answers: dict[str, str],
                framework: str,
                planning_context: dict[str, object],
            ) -> dict[str, object]:
                return {
                    "title": "Archive Breach",
                    "concept_summary": "Slip through a sealed archive and steal marked cores before the alarm locks the exits.",
                    "theme": "cyber archive",
                    "objective": "Steal marked data cores and escape before the lockdown seals the vault.",
                    "perspective": "top-down",
                    "core_mechanic": "hybrid",
                    "controls": {"up": "W", "down": "S", "left": "A", "right": "D"},
                    "player_identity": "vault infiltrator",
                    "player_entity": "infiltrator",
                    "hazard_entity": "security sentinel",
                    "collectible_entity": "data core",
                    "signature_mechanic": "Use a short dash burst to cut through scanner gaps.",
                    "progression_style": "rising alarm pressure",
                    "visual_tone": "mysterious",
                    "arena_detail": "a sealed neon archive vault",
                    "win_condition": "Win by stealing every marked data core and reaching the extraction pad.",
                    "lose_condition": "Lose if the alarm fully locks the vault or a sentinel tags the player.",
                    "score_target": 80,
                    "survival_seconds": None,
                    "generation_notes": ["The run should feel like a focused infiltration instead of open survival."],
                }

            def create_plan_copy(self, prompt: str, normalized_spec: dict[str, str]) -> dict[str, object]:
                return {
                    "title": "Fallback Title",
                    "concept_summary": "Fallback summary.",
                    "generation_notes": ["Fallback plan note."],
                }

        planner = Planner(llm_client=StructuredPlanningLLMClient())
        spec = planner.build_spec(
            "Make a cyber heist game about stealing data.",
            {
                "controls": "WASD",
                "player_identity": "vault infiltrator",
            },
        )

        self.assertEqual(spec.title, "Archive Breach")
        self.assertEqual(spec.concept_summary, "Slip through a sealed archive and steal marked cores before the alarm locks the exits.")
        self.assertEqual(spec.objective, "Steal marked data cores and escape before the lockdown seals the vault.")
        self.assertEqual(spec.player_identity, "vault infiltrator")
        self.assertEqual(spec.hazard_entity, "security sentinel")
        self.assertEqual(spec.collectible_entity, "data core")
        self.assertEqual(spec.score_target, 80)
        self.assertEqual(spec.win_condition, "Win by stealing every marked data core and reaching the extraction pad.")
        self.assertIn("focused infiltration", " ".join(spec.generation_notes))

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
    def test_generation_uses_llm_bundle_when_available(self) -> None:
        planner = Planner(llm_client=MockLLMClient())
        spec = planner.build_spec(
            "Make a simple space survival game.",
            {
                "perspective": "top-down",
                "controls": "arrow keys",
                "lose_condition": "Lose if an asteroid hits the player.",
            },
        )

        class BundleLLMClient:
            def create_game_bundle(
                self,
                prompt: str,
                game_spec: dict[str, object],
                generation_context: dict[str, object],
                repair_feedback: list[str] | None = None,
            ) -> dict[str, str]:
                self.repair_feedback = repair_feedback or []
                return {
                    "index.html": '<!DOCTYPE html><html><head><link rel="stylesheet" href="style.css"></head><body><button id="restartButton"></button><canvas id="gameCanvas"></canvas><script src="game.js"></script></body></html>',
                    "style.css": "body { margin: 0; }",
                    "game.js": 'function resetGame() {} function frame() { window.requestAnimationFrame(frame); } window.requestAnimationFrame(frame);',
                }

        generator = CodeGenerator(llm_client=BundleLLMClient(), validator=Validator())
        artifacts = generator.generate(spec)

        self.assertIn("requestAnimationFrame", artifacts["game.js"])
        self.assertTrue(any("Live LLM code generation succeeded" in message for message in generator.last_messages))

    def test_generation_falls_back_to_template_when_llm_bundle_is_invalid(self) -> None:
        planner = Planner(llm_client=MockLLMClient())
        spec = planner.build_spec(
            "Make a traffic dodging game where the player crosses busy lanes.",
            {
                "controls": "arrow keys",
                "lose_condition": "Lose if a car hits the player.",
            },
        )

        class InvalidBundleLLMClient:
            def create_game_bundle(
                self,
                prompt: str,
                game_spec: dict[str, object],
                generation_context: dict[str, object],
                repair_feedback: list[str] | None = None,
            ) -> dict[str, str]:
                return {
                    "index.html": "<html></html>",
                    "style.css": "body {}",
                    "game.js": "console.log('broken');",
                }

        generator = CodeGenerator(llm_client=InvalidBundleLLMClient(), validator=Validator())
        artifacts = generator.generate(spec)

        self.assertIn('"variant": "lane_dodger"', artifacts["game.js"])
        self.assertTrue(any("Falling back" in message for message in generator.last_messages))

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
