from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.mock_provider import MockLLMProvider
from app.llm.nvidia_provider import NvidiaLLMProvider


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    settings = get_settings()
    name = (provider_name or settings.llm_provider or "mock").strip().lower()
    if name == "nvidia":
        return NvidiaLLMProvider()
    return MockLLMProvider()
