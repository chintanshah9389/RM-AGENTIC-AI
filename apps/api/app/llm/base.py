from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def parse_intent(self, request: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def generate_message(self, context: dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    def regenerate_message(self, context: dict[str, Any], instruction: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def explain_recommendation(self, context: dict[str, Any]) -> str:
        raise NotImplementedError
