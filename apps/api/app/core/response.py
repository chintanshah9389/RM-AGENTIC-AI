from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[Any] = Field(default_factory=list)


class ApiResponse(BaseModel):
    success: bool
    data: Any = None
    error: Optional[ErrorBody] = None
    trace_id: str = Field(default_factory=lambda: str(uuid4()))


def ok(data: Any = None, trace_id: Optional[str] = None) -> dict[str, Any]:
    payload = ApiResponse(success=True, data=data, error=None)
    if trace_id:
        payload.trace_id = trace_id
    return payload.model_dump()


def fail(
    code: str,
    message: str,
    details: Optional[list[Any]] = None,
    trace_id: Optional[str] = None,
) -> dict[str, Any]:
    payload = ApiResponse(
        success=False,
        data=None,
        error=ErrorBody(code=code, message=message, details=details or []),
    )
    if trace_id:
        payload.trace_id = trace_id
    return payload.model_dump()
