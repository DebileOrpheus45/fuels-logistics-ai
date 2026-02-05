"""
API endpoints for staleness monitoring.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.staleness_monitor import create_staleness_monitor
from app.auth import get_current_user

router = APIRouter(prefix="/api/staleness", tags=["staleness"])


@router.post("/check")
def run_staleness_check(db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """
    Run a manual staleness check for all sites and loads.
    Creates escalations for any stale data found.
    """
    monitor = create_staleness_monitor(db)
    summary = monitor.run_staleness_check()
    return summary


@router.get("/inventory")
def get_stale_inventory_sites(db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Get all sites with stale inventory data."""
    monitor = create_staleness_monitor(db)
    stale_sites = monitor.check_inventory_staleness()
    return {
        "count": len(stale_sites),
        "sites": stale_sites
    }


@router.get("/eta")
def get_stale_eta_loads(db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Get all loads with stale ETA data."""
    monitor = create_staleness_monitor(db)
    stale_loads = monitor.check_eta_staleness()
    return {
        "count": len(stale_loads),
        "loads": stale_loads
    }
