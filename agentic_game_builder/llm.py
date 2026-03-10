from __future__ import annotations

import json
import os
import textwrap
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class LLMClient(Protocol):
    def create_clarification_questions(self, prompt: str, max_questions: int = 7) -> dict[str, Any]:
        """Return structured clarification questions for the user's prompt."""

    def create_game_plan(
        self,
        prompt: str,
        answers: dict[str, str],
        framework: str,
        planning_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Return structured planning fields for the requested game."""

    def create_game_bundle(
        self,
        prompt: str,
        game_spec: dict[str, Any],
        generation_context: dict[str, Any],
        repair_feedback: list[str] | None = None,
    ) -> dict[str, str]:
        """Return complete index.html, style.css, and game.js contents."""

    def create_plan_copy(self, prompt: str, normalized_spec: dict[str, Any]) -> dict[str, Any]:
        """Return lightweight copy fields derived from the normalized spec."""


class LLMRequestError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, retriable: bool = False) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retriable = retriable


@dataclass(slots=True)
class ResolvedLLMClients:
    clarification_client: LLMClient
    planning_client: LLMClient
    code_generation_client: LLMClient
    notes: list[str]


@dataclass(slots=True)
class MultiLLMClient:
    clients: list[tuple[str, LLMClient]]
    last_success_label: str | None = None

    def create_game_plan(
        self,
        prompt: str,
        answers: dict[str, str],
        framework: str,
        planning_context: dict[str, Any],
    ) -> dict[str, Any]:
        failures: list[str] = []
        for label, client in self.clients:
            try:
                response = client.create_game_plan(
                    prompt,
                    answers,
                    framework,
                    planning_context,
                )
                self.last_success_label = label
                return response
            except (AttributeError, LLMRequestError) as error:
                failures.append(f"{label}: {error}")
                continue
        raise LLMRequestError(
            "All configured live LLM providers failed. " + " | ".join(failures),
            retriable=True,
        )

    def create_clarification_questions(self, prompt: str, max_questions: int = 7) -> dict[str, Any]:
        failures: list[str] = []
        for label, client in self.clients:
            try:
                response = client.create_clarification_questions(prompt, max_questions=max_questions)
                self.last_success_label = label
                return response
            except LLMRequestError as error:
                failures.append(f"{label}: {error}")
                continue
        raise LLMRequestError(
            "All configured live LLM providers failed. " + " | ".join(failures),
            retriable=True,
        )

    def create_game_bundle(
        self,
        prompt: str,
        game_spec: dict[str, Any],
        generation_context: dict[str, Any],
        repair_feedback: list[str] | None = None,
    ) -> dict[str, str]:
        failures: list[str] = []
        for label, client in self.clients:
            try:
                response = client.create_game_bundle(
                    prompt,
                    game_spec,
                    generation_context,
                    repair_feedback=repair_feedback,
                )
                self.last_success_label = label
                return response
            except LLMRequestError as error:
                failures.append(f"{label}: {error}")
                continue
        raise LLMRequestError(
            "All configured live LLM providers failed. " + " | ".join(failures),
            retriable=True,
        )

    def create_plan_copy(self, prompt: str, normalized_spec: dict[str, Any]) -> dict[str, Any]:
        failures: list[str] = []
        for label, client in self.clients:
            try:
                response = client.create_plan_copy(prompt, normalized_spec)
                self.last_success_label = label
                return response
            except LLMRequestError as error:
                failures.append(f"{label}: {error}")
                continue
        raise LLMRequestError(
            "All configured live LLM providers failed. " + " | ".join(failures),
            retriable=True,
        )


@dataclass(slots=True)
class MockLLMClient:
    def create_game_plan(
        self,
        prompt: str,
        answers: dict[str, str],
        framework: str,
        planning_context: dict[str, Any],
    ) -> dict[str, Any]:
        return {}

    def create_clarification_questions(self, prompt: str, max_questions: int = 7) -> dict[str, Any]:
        raise LLMRequestError("Mock LLM clarification is intentionally disabled so the heuristic fallback can run.")

    def create_game_bundle(
        self,
        prompt: str,
        game_spec: dict[str, Any],
        generation_context: dict[str, Any],
        repair_feedback: list[str] | None = None,
    ) -> dict[str, str]:
        raise LLMRequestError("Mock LLM code generation is intentionally disabled so the template fallback can run.")

    def create_plan_copy(self, prompt: str, normalized_spec: dict[str, Any]) -> dict[str, Any]:
        theme = normalized_spec.get("theme", "Arcade").title()
        mechanic = normalized_spec.get("core_mechanic", "arcade")
        mechanic_noun = {
            "collect": "Collection",
            "dodge": "Dodge",
            "survive": "Survival",
            "hybrid": "Arcade",
        }.get(mechanic, "Arcade")
        objective = str(normalized_spec.get("objective", "survive the round")).strip()
        if objective:
            objective = objective.rstrip(".")
            objective = objective[0].lower() + objective[1:]
        player_identity = str(normalized_spec.get("player_identity", "player")).strip()
        arena_detail = str(normalized_spec.get("arena_detail", "a compact arena")).strip()
        tone = str(normalized_spec.get("visual_tone", "tense")).strip()
        signature = str(normalized_spec.get("signature_mechanic", "")).strip().rstrip(".")
        ability = str(normalized_spec.get("player_ability") or "").replace("_", " ").strip()
        title = f"{theme} {mechanic_noun} Challenge"
        summary = (
            f"A {tone} {normalized_spec.get('perspective', 'top-down')} browser game set in {arena_detail}, where "
            f"the {player_identity} must {objective}."
        )
        if signature:
            summary += f" Signature hook: {signature}."
        elif ability:
            summary += f" Signature hook: Use a {ability} to create openings."
        notes = list(normalized_spec.get("generation_notes", []))
        notes.append("Generated with the offline mock LLM client for deterministic local runs.")
        return {
            "title": title,
            "concept_summary": summary,
            "generation_notes": notes,
        }


@dataclass(slots=True)
class OpenAICompatibleLLMClient:
    api_key: str
    model: str
    base_url: str
    referer: str | None = None
    title: str | None = None

    def create_game_plan(
        self,
        prompt: str,
        answers: dict[str, str],
        framework: str,
        planning_context: dict[str, Any],
    ) -> dict[str, Any]:
        system_prompt = textwrap.dedent(
            """
            You are the design-planning model for Agentic Game Builder MVP.
            Analyze the user's vague browser-game idea and produce a concrete, implementation-ready game plan.

            Return valid JSON with these keys:
            - theme
            - title
            - concept_summary
            - objective
            - perspective
            - core_mechanic
            - controls
            - player_identity
            - player_entity
            - hazard_entity
            - collectible_entity
            - signature_mechanic
            - progression_style
            - visual_tone
            - arena_detail
            - win_condition
            - lose_condition
            - score_target
            - survival_seconds
            - generation_notes

            Rules:
            - keep the design within a small 2D browser game scope
            - ask yourself what the actual minute-to-minute gameplay should be
            - use the user's answers as authoritative when they exist
            - make the plan specific to the prompt instead of defaulting to a generic arcade layout
            - keep controls as an object with up, down, left, right string fields when keyboard or mouse movement is relevant
            - set score_target or survival_seconds to null if not applicable
            - generation_notes must be a short array of strings
            """
        ).strip()
        user_prompt = json.dumps(
            {
                "original_prompt": prompt,
                "user_answers": answers,
                "framework": framework,
                "planning_context": planning_context,
            },
            indent=2,
        )
        payload = self._chat_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            invalid_json_message="LLM returned invalid JSON for structured plan generation.",
        )
        payload["generation_notes"] = list(payload.get("generation_notes", []))
        return payload

    def create_clarification_questions(self, prompt: str, max_questions: int = 7) -> dict[str, Any]:
        system_prompt = textwrap.dedent(
            """
            You create targeted clarification questions for a browser game generator.
            Return valid JSON with keys:
            - questions: array of objects with keys key, prompt, reason
            - assumptions: short array of strings
            Ask only the highest-value questions still missing from the user's prompt.
            Make each question specific to the prompt's setting and likely gameplay.
            Use only these keys:
            theme, objective, perspective, controls, lose_condition, player_identity,
            signature_mechanic, progression_style, visual_tone, arena_detail.
            If the prompt is already specific enough, return an empty questions array.
            """
        ).strip()
        user_prompt = json.dumps(
            {
                "prompt": prompt,
                "max_questions": max_questions,
            },
            indent=2,
        )
        payload = self._chat_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            invalid_json_message="LLM returned invalid JSON for clarification generation.",
        )
        payload["questions"] = list(payload.get("questions", []))
        payload["assumptions"] = list(payload.get("assumptions", []))
        return payload

    def create_game_bundle(
        self,
        prompt: str,
        game_spec: dict[str, Any],
        generation_context: dict[str, Any],
        repair_feedback: list[str] | None = None,
    ) -> dict[str, str]:
        system_prompt = textwrap.dedent(
            """
            You generate the final browser game bundle for Agentic Game Builder MVP.
            Return valid JSON with exactly these keys:
            - index_html
            - style_css
            - game_js

            Product constraints:
            - generate a small 2D browser game only
            - output must run locally with no backend services
            - write complete contents for index.html, style.css, and game.js
            - do not include TODOs, placeholders, markdown fences, or commentary
            - preserve the user's theme, player fantasy, arena, pacing, and signature mechanic
            - keep the implementation inspectable and bounded for assignment review

            Technical requirements:
            - index_html must reference style.css and game.js
            - game_js must include restart capability via a resetGame function
            - vanilla_js builds must use requestAnimationFrame
            - phaser builds must bootstrap with new Phaser.Game
            - use Phaser only when framework is phaser
            - if framework is phaser, load Phaser 3.80.1 from jsDelivr in index_html
            - support the controls, win condition, lose condition, and score/timer model from the spec

            This is not a generic reskin task.
            The planning context was produced upstream by a separate design model.
            Treat that design brief as authoritative and implement gameplay logic that matches it.
            Do not mirror a fixed house template unless the plan itself calls for something simple.
            """
        ).strip()
        user_prompt = json.dumps(
            {
                "original_prompt": prompt,
                "game_spec": game_spec,
                "generation_context": generation_context,
                "repair_feedback": repair_feedback or [],
            },
            indent=2,
        )
        payload = self._chat_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            invalid_json_message="LLM returned invalid JSON for game bundle generation.",
        )
        try:
            return {
                "index.html": str(payload["index_html"]),
                "style.css": str(payload["style_css"]),
                "game.js": str(payload["game_js"]),
            }
        except KeyError as error:
            raise LLMRequestError("LLM game bundle response was missing one or more required file keys.") from error

    def create_plan_copy(self, prompt: str, normalized_spec: dict[str, Any]) -> dict[str, Any]:
        system_prompt = textwrap.dedent(
            """
            You create concise game-plan copy for an MVP browser game generator.
            Return valid JSON with keys: title, concept_summary, generation_notes.
            generation_notes must be a short array of strings.
            Do not invent unsupported features or extra files.
            """
        ).strip()
        user_prompt = json.dumps(
            {
                "original_prompt": prompt,
                "normalized_spec": normalized_spec,
            },
            indent=2,
        )
        payload = self._chat_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            invalid_json_message="LLM returned invalid JSON for plan copy generation.",
        )
        payload["generation_notes"] = list(payload.get("generation_notes", []))
        return payload

    def _chat_json(self, system_prompt: str, user_prompt: str, invalid_json_message: str) -> dict[str, Any]:
        raw = self._chat_completion(system_prompt, user_prompt)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as error:
            try:
                payload = json.loads(self._recover_json_text(raw))
            except json.JSONDecodeError:
                raise LLMRequestError(invalid_json_message) from error
        if not isinstance(payload, dict):
            raise LLMRequestError(invalid_json_message)
        return payload

    def _recover_json_text(self, raw: str) -> str:
        stripped = raw.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if len(lines) >= 3:
                stripped = "\n".join(lines[1:-1]).strip()
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            return stripped[start : end + 1]
        return stripped

    def _chat_completion(self, system_prompt: str, user_prompt: str) -> str:
        max_attempts = max(1, int(os.getenv("AIGB_LLM_MAX_ATTEMPTS", "2")))
        for attempt in range(1, max_attempts + 1):
            body = json.dumps(
                {
                    "model": self.model,
                    "temperature": 0.2,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "response_format": {"type": "json_object"},
                }
            ).encode("utf-8")
            request = urllib.request.Request(
                self.base_url,
                data=body,
                headers=self._headers(),
            )
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    payload = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as error:
                failure = self._build_http_error(error)
                if failure.retriable and attempt < max_attempts:
                    time.sleep(self._backoff_seconds(attempt))
                    continue
                raise failure from error
            except urllib.error.URLError as error:
                failure = LLMRequestError(
                    f"LLM request failed: {error}",
                    retriable=True,
                )
                if attempt < max_attempts:
                    time.sleep(self._backoff_seconds(attempt))
                    continue
                raise failure from error
            try:
                return payload["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as error:
                raise LLMRequestError(f"Unexpected LLM response payload: {payload}") from error
        raise LLMRequestError("LLM request failed after retry attempts were exhausted.")

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "agentic-game-builder/0.1",
        }
        if self.referer:
            headers["HTTP-Referer"] = self.referer
        if self.title:
            headers["X-Title"] = self.title
        return headers

    def _build_http_error(self, error: urllib.error.HTTPError) -> LLMRequestError:
        status_code = getattr(error, "code", None)
        raw_body = ""
        try:
            raw_body = error.read().decode("utf-8", errors="replace")
        except Exception:
            raw_body = ""
        detail = self._extract_error_detail(raw_body)
        message = f"LLM request failed with HTTP {status_code}: {error.reason}"
        if detail:
            message = f"{message}. {detail}"
        return LLMRequestError(
            message,
            status_code=status_code,
            retriable=bool(status_code == 429 or (status_code and status_code >= 500)),
        )

    def _extract_error_detail(self, raw_body: str) -> str:
        if not raw_body:
            return ""
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            return raw_body.strip()
        if isinstance(payload, dict):
            error_value = payload.get("error")
            if isinstance(error_value, dict):
                message = error_value.get("message")
                if isinstance(message, str):
                    return message.strip()
            message = payload.get("message")
            if isinstance(message, str):
                return message.strip()
        return raw_body.strip()

    def _backoff_seconds(self, attempt: int) -> float:
        return min(5.0, float(2 ** (attempt - 1)))


def load_dotenv(dotenv_path: str | os.PathLike[str] = ".env") -> None:
    path = Path(dotenv_path)
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def resolve_role_llm_clients() -> ResolvedLLMClients:
    load_dotenv()
    if os.getenv("AIGB_PROVIDER", "").strip().lower() == "mock":
        mock_client = MockLLMClient()
        return ResolvedLLMClients(
            clarification_client=mock_client,
            planning_client=mock_client,
            code_generation_client=mock_client,
            notes=["Using deterministic mock LLM client for clarification, planning, and code generation."],
        )

    design_client, design_note = _resolve_design_client()
    code_generation_client, code_generation_note = _resolve_code_generation_client()
    return ResolvedLLMClients(
        clarification_client=design_client,
        planning_client=design_client,
        code_generation_client=code_generation_client,
        notes=[design_note, code_generation_note],
    )


def resolve_llm_client() -> tuple[LLMClient, str]:
    load_dotenv()
    provider = os.getenv("AIGB_PROVIDER", "provider_chain").strip().lower() or "provider_chain"
    if provider == "mock":
        return MockLLMClient(), "Using deterministic mock LLM client."
    if provider in {"provider_chain", "groq_chain", "multi"}:
        client_chain, chain_note = _resolve_provider_chain()
        return client_chain, chain_note
    if provider == "openai_compatible":
        api_key = os.getenv("AIGB_API_KEY")
        model = os.getenv("AIGB_MODEL", "qwen/qwen3-coder:free")
        base_url = os.getenv("AIGB_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
        referer = os.getenv("AIGB_SITE_URL")
        title = os.getenv("AIGB_APP_NAME", "Agentic Game Builder MVP")
        if not api_key:
            raise RuntimeError("AIGB_API_KEY is required when AIGB_PROVIDER=openai_compatible.")
        return (
            OpenAICompatibleLLMClient(
                api_key=api_key,
                model=model,
                base_url=base_url,
                referer=referer,
                title=title,
            ),
            f"Using OpenAI-compatible provider at {base_url} with model {model}.",
        )
    raise RuntimeError(
        f"Unsupported provider '{provider}'. Use 'provider_chain', 'mock', or 'openai_compatible'."
    )


def _resolve_provider_chain() -> tuple[LLMClient, str]:
    site_url = os.getenv("AIGB_SITE_URL")
    app_name = os.getenv("AIGB_APP_NAME", "Agentic Game Builder MVP")
    groq_api_key = os.getenv("AIGB_GROQ_API_KEY")
    groq_base_url = os.getenv("AIGB_GROQ_BASE_URL", "https://api.groq.com/openai/v1/chat/completions")
    groq_primary_model = os.getenv("AIGB_GROQ_PRIMARY_MODEL", "openai/gpt-oss-120b")
    groq_fallback_model = os.getenv("AIGB_GROQ_FALLBACK_MODEL", "qwen/qwen3-32b")
    openrouter_api_key = os.getenv("AIGB_OPENROUTER_API_KEY") or os.getenv("AIGB_API_KEY")
    openrouter_base_url = os.getenv("AIGB_OPENROUTER_BASE_URL") or os.getenv(
        "AIGB_BASE_URL",
        "https://openrouter.ai/api/v1/chat/completions",
    )
    openrouter_model = os.getenv("AIGB_OPENROUTER_MODEL") or os.getenv("AIGB_MODEL", "qwen/qwen3-coder:free")

    clients: list[tuple[str, LLMClient]] = []
    labels: list[str] = []

    if groq_api_key:
        clients.append(
            (
                f"Groq {groq_primary_model}",
                OpenAICompatibleLLMClient(
                    api_key=groq_api_key,
                    model=groq_primary_model,
                    base_url=groq_base_url,
                    referer=site_url,
                    title=app_name,
                ),
            )
        )
        labels.append(f"Groq {groq_primary_model}")
        clients.append(
            (
                f"Groq {groq_fallback_model}",
                OpenAICompatibleLLMClient(
                    api_key=groq_api_key,
                    model=groq_fallback_model,
                    base_url=groq_base_url,
                    referer=site_url,
                    title=app_name,
                ),
            )
        )
        labels.append(f"Groq {groq_fallback_model}")

    if openrouter_api_key:
        clients.append(
            (
                f"OpenRouter {openrouter_model}",
                OpenAICompatibleLLMClient(
                    api_key=openrouter_api_key,
                    model=openrouter_model,
                    base_url=openrouter_base_url,
                    referer=site_url,
                    title=app_name,
                ),
            )
        )
        labels.append(f"OpenRouter {openrouter_model}")

    if not clients:
        raise RuntimeError(
            "No live LLM credentials configured for provider_chain. Set AIGB_GROQ_API_KEY and/or AIGB_OPENROUTER_API_KEY."
        )

    return MultiLLMClient(clients), "Using provider chain: " + " -> ".join(labels) + "."


def _resolve_design_client() -> tuple[LLMClient, str]:
    provider = os.getenv("AIGB_DESIGN_PROVIDER", "groq").strip().lower() or "groq"
    metadata = _client_metadata()
    if provider == "mock":
        return MockLLMClient(), "Clarification and planning model: mock fallback."
    if provider == "groq":
        api_key = os.getenv("AIGB_GROQ_API_KEY")
        model = os.getenv("AIGB_DESIGN_MODEL") or os.getenv("AIGB_GROQ_PRIMARY_MODEL", "openai/gpt-oss-120b")
        base_url = os.getenv("AIGB_DESIGN_BASE_URL") or os.getenv(
            "AIGB_GROQ_BASE_URL",
            "https://api.groq.com/openai/v1/chat/completions",
        )
        if not api_key:
            raise RuntimeError("AIGB_GROQ_API_KEY is required for clarification and planning.")
        return (
            OpenAICompatibleLLMClient(
                api_key=api_key,
                model=model,
                base_url=base_url,
                referer=metadata["referer"],
                title=metadata["title"],
            ),
            f"Clarification and planning model: Groq {model}.",
        )
    if provider == "openai_compatible":
        api_key = os.getenv("AIGB_DESIGN_API_KEY") or os.getenv("AIGB_API_KEY")
        model = os.getenv("AIGB_DESIGN_MODEL") or os.getenv("AIGB_MODEL", "openai/gpt-oss-120b")
        base_url = os.getenv("AIGB_DESIGN_BASE_URL") or os.getenv(
            "AIGB_BASE_URL",
            "https://api.groq.com/openai/v1/chat/completions",
        )
        if not api_key:
            raise RuntimeError("AIGB_DESIGN_API_KEY or AIGB_API_KEY is required for design openai_compatible mode.")
        return (
            OpenAICompatibleLLMClient(
                api_key=api_key,
                model=model,
                base_url=base_url,
                referer=metadata["referer"],
                title=metadata["title"],
            ),
            f"Clarification and planning model: {model} via {base_url}.",
        )
    raise RuntimeError(
        f"Unsupported AIGB_DESIGN_PROVIDER '{provider}'. Use 'groq', 'openai_compatible', or 'mock'."
    )


def _resolve_code_generation_client() -> tuple[LLMClient, str]:
    provider = os.getenv("AIGB_CODEGEN_PROVIDER", "openrouter").strip().lower() or "openrouter"
    metadata = _client_metadata()
    if provider == "mock":
        return MockLLMClient(), "Code generation model: mock fallback."
    if provider == "openrouter":
        api_key = os.getenv("AIGB_OPENROUTER_API_KEY") or os.getenv("AIGB_API_KEY")
        model = os.getenv("AIGB_CODEGEN_MODEL") or os.getenv("AIGB_OPENROUTER_MODEL", "qwen/qwen3-coder:free")
        base_url = os.getenv("AIGB_CODEGEN_BASE_URL") or os.getenv("AIGB_OPENROUTER_BASE_URL") or os.getenv(
            "AIGB_BASE_URL",
            "https://openrouter.ai/api/v1/chat/completions",
        )
        if not api_key:
            raise RuntimeError("AIGB_OPENROUTER_API_KEY or AIGB_API_KEY is required for code generation.")
        return (
            OpenAICompatibleLLMClient(
                api_key=api_key,
                model=model,
                base_url=base_url,
                referer=metadata["referer"],
                title=metadata["title"],
            ),
            f"Code generation model: OpenRouter {model}.",
        )
    if provider == "openai_compatible":
        api_key = os.getenv("AIGB_CODEGEN_API_KEY") or os.getenv("AIGB_API_KEY")
        model = os.getenv("AIGB_CODEGEN_MODEL") or os.getenv("AIGB_MODEL", "qwen/qwen3-coder:free")
        base_url = os.getenv("AIGB_CODEGEN_BASE_URL") or os.getenv(
            "AIGB_BASE_URL",
            "https://openrouter.ai/api/v1/chat/completions",
        )
        if not api_key:
            raise RuntimeError("AIGB_CODEGEN_API_KEY or AIGB_API_KEY is required for code-generation openai_compatible mode.")
        return (
            OpenAICompatibleLLMClient(
                api_key=api_key,
                model=model,
                base_url=base_url,
                referer=metadata["referer"],
                title=metadata["title"],
            ),
            f"Code generation model: {model} via {base_url}.",
        )
    raise RuntimeError(
        f"Unsupported AIGB_CODEGEN_PROVIDER '{provider}'. Use 'openrouter', 'openai_compatible', or 'mock'."
    )


def _client_metadata() -> dict[str, str | None]:
    return {
        "referer": os.getenv("AIGB_SITE_URL"),
        "title": os.getenv("AIGB_APP_NAME", "Agentic Game Builder MVP"),
    }
