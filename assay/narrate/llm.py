"""Provider-agnostic LLM interface for the optional narrator.

Rule: never import a vendor SDK outside its adapter. Choose the backend with ``ASSAY_LLM_PROVIDER``
("anthropic" | "openai" | "offline"); the provider's key comes from its usual env var. The default
is ``auto``: Anthropic if ``ANTHROPIC_API_KEY`` is set, else OpenAI if ``OPENAI_API_KEY`` is set,
else the deterministic :class:`OfflineClient`.

The narrator only ever writes *prose around numbers Assay already computed*. The numbers themselves
are never produced here, and :func:`assay.narrate.narrate.assert_grounded` enforces that downstream.
"""

from __future__ import annotations

import os
from typing import Any, Protocol


class LLMClient(Protocol):
    """The only contract the narrator depends on."""

    def complete(self, messages: list[dict[str, str]], schema: dict[str, Any]) -> dict[str, Any]:
        """Return a JSON object conforming to ``schema``. ``messages`` are {role, content} dicts."""
        ...


def _split_system(messages: list[dict[str, str]]) -> tuple[str, list[dict[str, str]]]:
    system = "\n\n".join(m["content"] for m in messages if m.get("role") == "system")
    rest = [m for m in messages if m.get("role") != "system"]
    return system, rest


_TOOL_NAME = "emit_narration"


class AnthropicAdapter:
    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.model = model

    def complete(self, messages: list[dict[str, str]], schema: dict[str, Any]) -> dict[str, Any]:
        import anthropic  # imported only inside the adapter

        client = anthropic.Anthropic()
        system, convo = _split_system(messages)
        resp = client.messages.create(
            model=self.model,
            max_tokens=1500,
            system=system or anthropic.NOT_GIVEN,
            messages=convo,
            tools=[
                {"name": _TOOL_NAME, "description": "Emit narration prose.", "input_schema": schema}
            ],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
        )
        for block in resp.content:
            if block.type == "tool_use" and block.name == _TOOL_NAME:
                return dict(block.input)
        raise RuntimeError("Anthropic response contained no tool_use block")


class OpenAIAdapter:
    def __init__(self, model: str = "gpt-4o"):
        self.model = model

    def complete(self, messages: list[dict[str, str]], schema: dict[str, Any]) -> dict[str, Any]:
        import json

        import openai  # imported only inside the adapter

        client = openai.OpenAI()
        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "narration", "schema": schema},
            },
        )
        return json.loads(resp.choices[0].message.content)


class OfflineClient:
    """Deterministic no-network client. Returns no prose, so callers fall back to the report's own
    deterministic text. It exists so the narrator path runs with no key and in tests."""

    model = "offline-deterministic"

    def complete(self, messages: list[dict[str, str]], schema: dict[str, Any]) -> dict[str, Any]:
        return {"prose": ""}


def get_llm_client() -> LLMClient:
    """Factory selected by ASSAY_LLM_PROVIDER (default: auto-detect from available keys)."""
    provider = os.environ.get("ASSAY_LLM_PROVIDER", "auto").lower()
    if provider == "auto":
        if os.environ.get("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.environ.get("OPENAI_API_KEY"):
            provider = "openai"
        else:
            provider = "offline"
    if provider == "anthropic":
        return AnthropicAdapter()
    if provider == "openai":
        return OpenAIAdapter()
    if provider == "offline":
        return OfflineClient()
    raise ValueError(f"Unknown ASSAY_LLM_PROVIDER: {provider!r}")
