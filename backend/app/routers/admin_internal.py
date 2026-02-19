"""
Internal admin endpoints — one-time migrations and utilities.
Only mounted when DEBUG=True. Not shown in public API docs.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.models import User
from app.database import get_db

router = APIRouter(prefix="/api/_internal", tags=["internal"], include_in_schema=False)


@router.post("/seed-historical")
def seed_historical(current_user: User = Depends(get_current_user)):
    """Seed historical delivered loads and escalations, then rebuild knowledge graph."""
    from seed_historical_data import seed_historical_data
    import io, contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        seed_historical_data()
    return {"output": buf.getvalue()}


@router.post("/migrate-utc-to-eastern")
def migrate_utc_to_eastern(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    One-time migration: shift all old UTC timestamps to Eastern (UTC-5).
    Safe to run multiple times — but should only be needed once.
    """
    from sqlalchemy import text

    migrations = [
        ("sites", ["last_inventory_update_at", "created_at", "updated_at"]),
        ("loads", ["current_eta", "last_eta_update", "last_email_sent", "last_eta_update_at",
                    "shipped_at", "created_at", "updated_at"]),
        ("carriers", ["created_at", "updated_at"]),
        ("ai_agents", ["last_activity_at", "created_at", "updated_at"]),
        ("activities", ["created_at"]),
        ("escalations", ["created_at", "resolved_at", "updated_at"]),
        ("email_logs", ["sent_at", "delivered_at", "bounced_at", "complaint_at", "created_at", "updated_at"]),
        ("inbound_emails", ["parsed_eta", "received_at", "processed_at", "created_at"]),
        ("carrier_stats", ["updated_at"]),
        ("site_stats", ["updated_at"]),
        ("agent_run_history", ["started_at", "completed_at"]),
        ("llm_usage", ["created_at"]),
        ("users", ["created_at", "updated_at", "last_login_at"]),
    ]

    total_updated = 0
    details = []
    for table, columns in migrations:
        for col in columns:
            try:
                result = db.execute(
                    text(f"UPDATE {table} SET {col} = {col} - INTERVAL '5 hours' WHERE {col} IS NOT NULL")
                )
                count = result.rowcount
                total_updated += count
                details.append(f"{table}.{col}: {count} rows")
            except Exception as e:
                details.append(f"{table}.{col}: ERROR — {str(e)}")

    db.commit()
    return {
        "message": f"Migrated {total_updated} timestamp values (UTC → Eastern, -5h)",
        "details": details,
    }
