from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import AuditEvent

SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "passwordHash",
    "token",
    "jwt",
    "api_key",
    "apiKey",
    "secret",
    "fullAccountNumber",
}


def _sanitize(metadata: Optional[dict[str, Any]]) -> dict[str, Any]:
    if not metadata:
        return {}
    clean: dict[str, Any] = {}
    for key, value in metadata.items():
        if key in SENSITIVE_KEYS:
            continue
        clean[key] = value
    return clean


def write_audit(
    db: Session,
    *,
    event_type: str,
    summary: str,
    status: str = "INFO",
    user_id: Optional[str] = None,
    user_role: Optional[str] = None,
    correlation_id: Optional[str] = None,
    workflow_run_id: Optional[str] = None,
    campaign_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> AuditEvent:
    event = AuditEvent(
        user_id=user_id,
        user_role=user_role,
        correlation_id=correlation_id,
        workflow_run_id=workflow_run_id,
        campaign_id=campaign_id,
        customer_id=customer_id,
        agent_name=agent_name,
        event_type=event_type,
        status=status,
        summary=summary,
        metadata_json=_sanitize(metadata),
    )
    db.add(event)
    db.flush()
    return event
