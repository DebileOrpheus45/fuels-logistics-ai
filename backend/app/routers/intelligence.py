from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.models import User

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
def get_status_summary(current_user: User = Depends(get_current_user)):
    """Generate executive status summary from current state + knowledge graph."""
    from app.services.knowledge_graph import generate_status_summary
    return {"summary": generate_status_summary()}


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
