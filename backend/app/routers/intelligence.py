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
def get_full_summary(current_user: User = Depends(get_current_user)):
    """Generate comprehensive knowledge graph narrative summary."""
    from app.services.knowledge_graph import generate_knowledge_graph_summary
    return {"summary": generate_knowledge_graph_summary()}


@router.get("/admin/llm-usage")
def get_llm_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get cumulative LLM usage statistics for the Admin dashboard."""
    from app.services.llm_usage import get_usage_summary
    return get_usage_summary(db)


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
