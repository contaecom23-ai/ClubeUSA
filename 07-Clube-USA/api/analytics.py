"""
Emissão de eventos de analytics — fire-and-forget.
Falhas de analytics NUNCA interrompem o fluxo principal.
"""
import logging

logger = logging.getLogger(__name__)


def emit_event(db, event_type: str, user_id: str | None = None, metadata: dict | None = None) -> None:
    try:
        db.table("events").insert(
            {
                "user_id": user_id,
                "event_type": event_type,
                "metadata": metadata or {},
            }
        ).execute()
    except Exception as exc:
        logger.warning("analytics emit_event(%s) falhou: %s", event_type, exc)
