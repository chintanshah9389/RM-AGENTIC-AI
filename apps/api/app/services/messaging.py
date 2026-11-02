from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import MessageDraft, SimulatedMessage
from app.services.audit import write_audit


class MessagingProvider(ABC):
    name: str = "base"

    @abstractmethod
    def send_message(
        self,
        db: Session,
        *,
        message: MessageDraft,
        contact_allowed: bool,
        user_id: str,
        user_role: str,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError


class MockWhatsAppProvider(MessagingProvider):
    name = "mock_whatsapp"

    def send_message(
        self,
        db: Session,
        *,
        message: MessageDraft,
        contact_allowed: bool,
        user_id: str,
        user_role: str,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        if not contact_allowed:
            raise PermissionError("Customer is blocked by compliance. Message cannot be sent.")
        if message.status != "APPROVED":
            raise PermissionError("Only approved messages can be simulated.")

        external_id = f"SIM-WA-{uuid.uuid4().hex[:12].upper()}"
        simulated = SimulatedMessage(
            message_id=message.id,
            campaign_id=message.campaign_id,
            customer_id=message.customer_id,
            external_message_id=external_id,
            status="SIMULATED_SENT",
            sent_at=datetime.utcnow(),
        )
        db.add(simulated)
        message.status = "SIMULATED_SENT"
        message.updated_at = datetime.utcnow()
        db.flush()

        write_audit(
            db,
            event_type="MOCK_WHATSAPP_SEND",
            summary="Simulated WhatsApp send. No real customer message was sent.",
            status="SUCCESS",
            user_id=user_id,
            user_role=user_role,
            correlation_id=correlation_id,
            campaign_id=message.campaign_id,
            customer_id=message.customer_id,
            agent_name="MockWhatsAppProvider",
            metadata={"externalMessageId": external_id, "messageId": message.id},
        )

        return {
            "externalMessageId": external_id,
            "status": "SIMULATED_SENT",
            "disclaimer": "Simulated WhatsApp send. No real customer message was sent.",
            "sentAt": simulated.sent_at.isoformat(),
        }


def get_messaging_provider() -> MessagingProvider:
    return MockWhatsAppProvider()
