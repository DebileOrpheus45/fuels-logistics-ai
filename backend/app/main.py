from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.config import get_settings
from app.routers import sites, loads, agents, escalations, carriers, emails, snapshots
from app.schemas import DashboardStats

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    Base.metadata.create_all(bind=engine)

    # Start agent scheduler
    from app.agents.agent_scheduler import start_scheduler, stop_scheduler
    start_scheduler()

    yield

    # Shutdown: stop scheduler
    stop_scheduler()


app = FastAPI(
    title="Fuels Logistics AI Coordinator",
    description="AI-powered platform for managing fuel logistics operations",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sites.router)
app.include_router(loads.router)
app.include_router(carriers.router)
app.include_router(agents.router)
app.include_router(escalations.router)
app.include_router(emails.router)
app.include_router(snapshots.router)


@app.get("/")
def root():
    """Root endpoint with API info."""
    return {
        "name": "Fuels Logistics AI Coordinator API",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats():
    """Get high-level dashboard statistics."""
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models import Site, Load, LoadStatus, Escalation, EscalationStatus, AIAgent, AgentStatus

    db: Session = SessionLocal()
    try:
        total_sites = db.query(Site).count()

        sites_at_risk = db.query(Site).filter(
            Site.hours_to_runout.isnot(None),
            Site.hours_to_runout <= Site.runout_threshold_hours
        ).count()

        active_loads = db.query(Load).filter(
            Load.status.in_([LoadStatus.SCHEDULED, LoadStatus.IN_TRANSIT])
        ).count()

        delayed_loads = db.query(Load).filter(
            Load.status == LoadStatus.DELAYED
        ).count()

        open_escalations = db.query(Escalation).filter(
            Escalation.status != EscalationStatus.RESOLVED
        ).count()

        active_agents = db.query(AIAgent).filter(
            AIAgent.status == AgentStatus.ACTIVE
        ).count()

        return DashboardStats(
            total_sites=total_sites,
            sites_at_risk=sites_at_risk,
            active_loads=active_loads,
            delayed_loads=delayed_loads,
            open_escalations=open_escalations,
            active_agents=active_agents
        )
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
