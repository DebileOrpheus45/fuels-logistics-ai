from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime

from app.database import engine, Base
from app.config import get_settings
from app.routers import sites, loads, agents, escalations, carriers, emails, snapshots, staleness, email_inbound, auth, sheets, intelligence
from app.schemas import DashboardStats
from app.auth import get_current_user
from app.models import User
from app.logging_config import setup_logging, get_logger

settings = get_settings()

# Initialize structured logging
# Use JSON logs in production (DEBUG=false), console logs in development
setup_logging(
    json_logs=not settings.debug,
    log_level=settings.log_level if hasattr(settings, 'log_level') else "INFO"
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("application_startup", version="0.4.0")
    logger.info("email_config", sendgrid_configured=bool(settings.sendgrid_api_key), sendgrid_from=settings.sendgrid_from_email)

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("database_initialized")

    # Auto-seed if database has no users (first deploy)
    from app.database import SessionLocal
    from app.models import User
    try:
        db = SessionLocal()
        if db.query(User).count() == 0:
            logger.info("empty_database_detected", action="auto_seeding")
            db.close()
            from seed_data import seed_database
            seed_database()
            from add_tracking_data import add_tracking_to_loads
            add_tracking_to_loads()
            logger.info("auto_seed_complete")
        else:
            db.close()
    except Exception as e:
        logger.warning("auto_seed_skipped", error=str(e))

    # Start agent scheduler
    from app.agents.agent_scheduler import start_scheduler, stop_scheduler
    start_scheduler()
    logger.info("agent_scheduler_started")

    yield

    # Shutdown
    logger.info("application_shutdown")
    stop_scheduler()


app = FastAPI(
    title="Fuels Logistics AI Coordinator",
    description="AI-powered platform for managing fuel logistics operations",
    version="0.3.0",  # Updated to reflect GPS tracking features
    lifespan=lifespan
)

# Configure CORS for frontend
cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()] if settings.cors_origins else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"http://localhost:\d+",  # Always allow localhost for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)  # Auth router first (no /api prefix for OAuth2 compatibility)
app.include_router(sites.router)
app.include_router(loads.router)
app.include_router(carriers.router)
app.include_router(agents.router)
app.include_router(escalations.router)
app.include_router(emails.router)
app.include_router(snapshots.router)
app.include_router(staleness.router)
app.include_router(email_inbound.router)
app.include_router(sheets.router)
app.include_router(intelligence.router)


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
    """
    Health check endpoint for monitoring and load balancers.

    Returns database connectivity status and basic system info.
    """
    from app.database import SessionLocal
    from sqlalchemy import text

    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.4.0",
        "checks": {}
    }

    # Check database connectivity
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health["checks"]["database"] = "ok"
    except Exception as e:
        health["status"] = "unhealthy"
        health["checks"]["database"] = f"error: {str(e)}"
        logger.error("health_check_failed", component="database", error=str(e))

    return health


@app.get("/api/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(current_user: User = Depends(get_current_user)):
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
