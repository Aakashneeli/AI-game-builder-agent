from __future__ import annotations

import json
import os
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class LLMClient(Protocol):
    def create_plan_copy(self, prompt: str, normalized_spec: dict[str, Any]) -> dict[str, Any]:
        """Return lightweight copy fields derived from the normalized spec."""


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
        title = f"{theme} {mechanic_noun} Challenge"
        summary = (
            f"A small {normalized_spec.get('perspective', 'top-down')} browser game where the player must "
            f"{objective}."
        )
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
        payload = json.loads(raw)
        payload["generation_notes"] = list(payload.get("generation_notes", []))
        return payload

    def _chat_completion(self, system_prompt: str, user_prompt: str) -> str:
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
        except urllib.error.URLError as error:
            raise RuntimeError(f"LLM request failed: {error}") from error
        try:
            return payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise RuntimeError(f"Unexpected LLM response payload: {payload}") from error

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.referer:
            headers["HTTP-Referer"] = self.referer
        if self.title:
            headers["X-Title"] = self.title
        return headers


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
    provider = os.getenv("AIGB_PROVIDER", "openai_compatible").strip().lower() or "openai_compatible"
    if provider == "mock":
        return MockLLMClient(), "Using deterministic mock LLM client."
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
    raise RuntimeError(f"Unsupported provider '{provider}'. Use 'mock' or 'openai_compatible'.")
