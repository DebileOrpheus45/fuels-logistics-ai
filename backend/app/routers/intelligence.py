from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.auth import get_current_user
from app.models import User
from app.database import get_db

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


@router.get("/")
def get_intelligence(current_user: User = Depends(get_current_user)):
    """Get full knowledge graph data for the Intelligence page."""
    from app.services.knowledge_graph import get_all_intelligence
    return get_all_intelligence()


@router.post("/refresh")
def refresh_knowledge_graph(current_user: User = Depends(get_current_user)):
    """Rebuild knowledge graph stats from existing data."""
    from app.services.knowledge_graph import rebuild_knowledge_graph
    return rebuild_knowledge_graph()


@router.post("/seed-historical")
def seed_historical(current_user: User = Depends(get_current_user)):
    """Seed historical delivered loads and escalations, then rebuild knowledge graph."""
    from seed_historical_data import seed_historical_data
    import io, contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        seed_historical_data()
    return {"output": buf.getvalue()}


@router.get("/status-summary")
def get_status_summary(
    llm: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
):
    """Generate executive status summary. Use ?llm=true for AI-powered briefing."""
    if llm:
        from app.services.knowledge_graph import generate_llm_status_summary
        return generate_llm_status_summary()
    from app.services.knowledge_graph import generate_status_summary
    return {"summary": generate_status_summary(), "source": "template"}


@router.get("/full-summary")
def get_full_summary(
    llm: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
):
    """Generate comprehensive knowledge graph summary. Use ?llm=true for AI-powered version."""
    if llm:
        from app.services.knowledge_graph import generate_llm_knowledge_graph_summary
        return generate_llm_knowledge_graph_summary()
    from app.services.knowledge_graph import generate_knowledge_graph_summary
    return {"summary": generate_knowledge_graph_summary(), "source": "template"}


@router.get("/admin/llm-usage")
def get_llm_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get cumulative LLM usage statistics for the Admin dashboard."""
    from app.services.llm_usage import get_usage_summary
    return get_usage_summary(db)


@router.post("/admin/migrate-utc-to-eastern")
def migrate_utc_to_eastern(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    One-time migration: shift all old UTC timestamps to Eastern (UTC-5).
    Safe to run multiple times — but should only be needed once.
    """
    from sqlalchemy import text

    # All tables + datetime columns that were stored with datetime.utcnow()
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


@router.get("/carrier/{carrier_id}")
def get_carrier_intel(carrier_id: int, current_user: User = Depends(get_current_user)):
    """Get intelligence for a specific carrier."""
    from app.services.knowledge_graph import get_carrier_intelligence
    data = get_carrier_intelligence(carrier_id)
    if not data:
        return {"detail": "No data for this carrier"}
    return data


@router.get("/site/{site_id}")
def get_site_intel(site_id: int, current_user: User = Depends(get_current_user)):
    """Get intelligence for a specific site."""
    from app.services.knowledge_graph import get_site_intelligence
    data = get_site_intelligence(site_id)
    if not data:
        return {"detail": "No data for this site"}
    return data
