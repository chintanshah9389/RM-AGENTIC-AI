"""Helpers to run LangChain create_agent with safe fallbacks."""

from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from app.core.config import get_settings
from app.llm.chat_factory import DeterministicToolChatModel, get_chat_model

T = TypeVar("T", bound=BaseModel)


def _extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def extract_agent_payload(result: dict[str, Any], schema: type[T] | None = None) -> dict[str, Any]:
    structured = result.get("structured_response")
    if structured is not None:
        if hasattr(structured, "model_dump"):
            return structured.model_dump()
        if isinstance(structured, dict):
            return structured

    messages: list[BaseMessage] = list(result.get("messages") or [])
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            parsed = _extract_json(str(msg.content))
            if parsed:
                return parsed
            if schema is None:
                return {"body": str(msg.content).strip()}
    return {}


def tools_called(result: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for msg in result.get("messages") or []:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", None)
                if name:
                    names.append(str(name))
    return names


def run_create_agent(
    *,
    tools: list[BaseTool],
    system_prompt: str,
    user_prompt: str,
    response_format: type[BaseModel] | None,
    purpose: str,
    mock_responses: list[BaseMessage] | None = None,
    agent_name: str,
) -> dict[str, Any]:
    """Run langchain.agents.create_agent and return normalized metadata + payload."""
    settings = get_settings()
    provider = (settings.llm_provider or "mock").lower()
    model: BaseChatModel

    if provider == "nvidia" and settings.nvidia_api_key:
        model = get_chat_model(purpose=purpose)
        execution = "langchain.create_agent+nvidia"
    else:
        if not mock_responses:
            raise RuntimeError("mock_responses required for offline create_agent")
        model = DeterministicToolChatModel(responses=list(mock_responses))
        execution = "langchain.create_agent+mock_tools"

    # Avoid response_format ToolStrategy loops with offline/fake models; parse JSON instead.
    agent = create_agent(
        model,
        tools=tools,
        system_prompt=system_prompt,
        name=agent_name,
    )
    result = agent.invoke(
        {"messages": [HumanMessage(content=user_prompt)]},
        config={"recursion_limit": 25},
    )
    payload = extract_agent_payload(result, response_format)
    called = tools_called(result)
    return {
        "payload": payload,
        "toolsCalled": called,
        "executionMode": execution,
        "rawMessageCount": len(result.get("messages") or []),
        "llmProvider": "nvidia" if "nvidia" in execution else "mock",
        "agentName": agent_name,
        "toolRoundtrips": len(called),
    }
