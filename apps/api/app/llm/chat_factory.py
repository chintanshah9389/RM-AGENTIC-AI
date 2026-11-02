"""LangChain chat models for create_agent (NVIDIA OpenAI-compatible + offline fake)."""

from __future__ import annotations

from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai import ChatOpenAI
from pydantic import Field

from app.core.config import get_settings


class DeterministicToolChatModel(BaseChatModel):
    """Offline chat model that supports bind_tools for create_agent demos."""

    responses: list[BaseMessage] = Field(default_factory=list)
    i: int = 0
    bound_tools: list[Any] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "crm-deterministic-tool-chat"

    def bind_tools(self, tools: Any, **kwargs: Any) -> DeterministicToolChatModel:
        # Mutate in place — model_copy would reset the response cursor and loop forever.
        object.__setattr__(self, "bound_tools", list(tools or []))
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        if not self.responses:
            raise RuntimeError("DeterministicToolChatModel has no responses configured")
        idx = min(self.i, len(self.responses) - 1)
        message = self.responses[idx]
        # Advance cursor without resetting across bind_tools calls
        object.__setattr__(self, "i", idx + 1)
        return ChatResult(generations=[ChatGeneration(message=message)])


def get_chat_model(*, purpose: str = "default") -> BaseChatModel:
    """Return a LangChain chat model for agent tool-calling."""
    settings = get_settings()
    provider = (settings.llm_provider or "mock").lower()

    if provider == "nvidia" and settings.nvidia_api_key:
        return ChatOpenAI(
            model=settings.nvidia_model,
            api_key=settings.nvidia_api_key,
            base_url=settings.nvidia_base_url.rstrip("/"),
            temperature=0.0 if purpose == "intent" else 0.3,
            max_tokens=700,
        )

    # Mock provider: model responses are injected per-agent before invoke.
    return DeterministicToolChatModel(responses=[AIMessage(content="{}")])
