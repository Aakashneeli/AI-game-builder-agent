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
    def create_plan_copy(self, prompt: str, normalized_spec: dict[str, Any]) -> dict[str, Any]:
        """Return lightweight copy fields derived from the normalized spec."""


class LLMRequestError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, retriable: bool = False) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retriable = retriable


@dataclass(slots=True)
class MultiLLMClient:
    clients: list[tuple[str, LLMClient]]
    last_success_label: str | None = None

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
        raw = self._chat_completion(system_prompt, user_prompt)
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as error:
            raise LLMRequestError("LLM returned invalid JSON for plan copy generation.") from error
        payload["generation_notes"] = list(payload.get("generation_notes", []))
        return payload

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
