from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    def run(self, state: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Return a partial state update."""
        raise NotImplementedError
