from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import AIAgent, AgentStatus, Site, Activity, ActivityType, User, AgentRunHistory
from app.schemas import (
    AIAgentCreate, AIAgentUpdate, AIAgentResponse, AIAgentWithSites,
    ActivityCreate, ActivityResponse, AIAgentSiteAssignment, AgentRunHistoryResponse
)
from app.auth import get_current_user

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("/", response_model=List[AIAgentResponse])
def get_agents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[AgentStatus] = None,
    db: Session = Depends(get_db)
):
    """Get all AI agents."""
    query = db.query(AIAgent)

    if status:
        query = query.filter(AIAgent.status == status)

    return query.offset(skip).limit(limit).all()


@router.get("/{agent_id}", response_model=AIAgentWithSites)
def get_agent(agent_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Get a specific agent with its assigned sites."""
    agent = db.query(AIAgent).options(
        joinedload(AIAgent.assigned_sites)
    ).filter(AIAgent.id == agent_id).first()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/", response_model=AIAgentResponse, status_code=201)
def create_agent(agent: AIAgentCreate, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Create a new AI agent."""
    db_agent = AIAgent(**agent.model_dump())
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent


@router.patch("/{agent_id}", response_model=AIAgentResponse)
def update_agent(agent_id: int, agent: AIAgentUpdate, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Update an agent's configuration."""
    db_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    update_data = agent.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_agent, field, value)

    db.commit()
    db.refresh(db_agent)
    return db_agent


@router.post("/{agent_id}/start", response_model=AIAgentResponse)
def start_agent(agent_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Start an AI agent."""
    db_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db_agent.status = AgentStatus.ACTIVE
    db.commit()
    db.refresh(db_agent)
    return db_agent


@router.post("/{agent_id}/pause", response_model=AIAgentResponse)
def pause_agent(agent_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Pause an AI agent."""
    db_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db_agent.status = AgentStatus.PAUSED
    db.commit()
    db.refresh(db_agent)
    return db_agent


@router.post("/{agent_id}/stop", response_model=AIAgentResponse)
def stop_agent(agent_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Stop an AI agent."""
    db_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db_agent.status = AgentStatus.STOPPED
    db.commit()
    db.refresh(db_agent)
    return db_agent


@router.post("/{agent_id}/assign-site/{site_id}", response_model=AIAgentWithSites)
def assign_site_to_agent(
    agent_id: int,
    site_id: int,
    db: Session = Depends(get_db)
):
    """Assign a site to be managed by this agent."""
    db_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    db_site = db.query(Site).filter(Site.id == site_id).first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found")

    db_site.assigned_agent_id = agent_id
    db.commit()

    # Reload agent with sites
    db.refresh(db_agent)
    return db.query(AIAgent).options(
        joinedload(AIAgent.assigned_sites)
    ).filter(AIAgent.id == agent_id).first()


@router.post("/{agent_id}/unassign-site/{site_id}", response_model=AIAgentWithSites)
def unassign_site_from_agent(
    agent_id: int,
    site_id: int,
    db: Session = Depends(get_db)
):
    """Remove a site from this agent's management."""
    db_site = db.query(Site).filter(
        Site.id == site_id,
        Site.assigned_agent_id == agent_id
    ).first()

    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found or not assigned to this agent")

    db_site.assigned_agent_id = None
    db.commit()

    return db.query(AIAgent).options(
        joinedload(AIAgent.assigned_sites)
    ).filter(AIAgent.id == agent_id).first()


@router.post("/{agent_id}/assign-sites", response_model=AIAgentWithSites)
def bulk_assign_sites_to_agent(
    agent_id: int,
    assignment: AIAgentSiteAssignment,
    db: Session = Depends(get_db)
):
    """
    Bulk assign multiple sites to an agent.
    This replaces all current assignments - sites not in the list will be unassigned.
    """
    db_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # First, unassign all sites currently assigned to this agent
    db.query(Site).filter(Site.assigned_agent_id == agent_id).update(
        {"assigned_agent_id": None}
    )

    # Then assign the new sites
    if assignment.site_ids:
        db.query(Site).filter(Site.id.in_(assignment.site_ids)).update(
            {"assigned_agent_id": agent_id},
            synchronize_session=False
        )

    db.commit()

    return db.query(AIAgent).options(
        joinedload(AIAgent.assigned_sites)
    ).filter(AIAgent.id == agent_id).first()


@router.delete("/{agent_id}", status_code=204)
def delete_agent(agent_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Delete an AI agent."""
    db_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Unassign all sites first
    db.query(Site).filter(Site.assigned_agent_id == agent_id).update(
        {"assigned_agent_id": None}
    )

    db.delete(db_agent)
    db.commit()
    return None


# ============== Activity Endpoints ==============

@router.get("/activities/all", response_model=List[ActivityResponse])
def get_all_activities(
    limit: int = Query(default=100, le=500),
    activity_type: Optional[ActivityType] = None,
    db: Session = Depends(get_db)
):
    """Get all activities across all agents (including system activities)."""
    query = db.query(Activity)
    if activity_type:
        query = query.filter(Activity.activity_type == activity_type)
    return query.order_by(Activity.created_at.desc()).limit(limit).all()


@router.get("/{agent_id}/activities", response_model=List[ActivityResponse])
def get_agent_activities(
    agent_id: int,
    skip: int = 0,
    limit: int = 50,
    activity_type: Optional[ActivityType] = None,
    db: Session = Depends(get_db)
):
    """Get activity logs for a specific agent."""
    query = db.query(Activity).filter(Activity.agent_id == agent_id)

    if activity_type:
        query = query.filter(Activity.activity_type == activity_type)

    return query.order_by(Activity.created_at.desc()).offset(skip).limit(limit).all()


@router.post("/{agent_id}/activities", response_model=ActivityResponse, status_code=201)
def log_activity(
    agent_id: int,
    activity: ActivityCreate,
    db: Session = Depends(get_db)
):
    """Log an activity for an agent (used by agent system internally)."""
    db_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Ensure agent_id matches
    activity_data = activity.model_dump()
    activity_data['agent_id'] = agent_id

    db_activity = Activity(**activity_data)
    db.add(db_activity)

    # Update agent's last activity timestamp
    db_agent.last_activity_at = datetime.utcnow()

    db.commit()
    db.refresh(db_activity)
    return db_activity


@router.post("/{agent_id}/run-check")
def run_agent_check_cycle(agent_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """
    Manually trigger one check cycle for an agent.
    The agent will analyze its assigned sites and take appropriate actions.
    """
    db_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check if agent has assigned sites
    assigned_sites = db.query(Site).filter(Site.assigned_agent_id == agent_id).count()
    if assigned_sites == 0:
        raise HTTPException(
            status_code=400,
            detail="Agent has no assigned sites. Assign sites before running checks."
        )

    # Run the check cycle
    from app.agents.coordinator_agent import run_agent_check
    result = run_agent_check(agent_id)

    return {
        "agent_id": agent_id,
        "agent_name": db_agent.agent_name,
        "result": result
    }


# ============== Scheduler Endpoints ==============

@router.post("/{agent_id}/schedule")
def schedule_agent(agent_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """
    Add an agent to the automated scheduler.
    The agent will run checks at its configured interval.
    """
    db_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Set agent to active
    db_agent.status = AgentStatus.ACTIVE
    db.commit()

    # Add to scheduler
    from app.agents.agent_scheduler import add_agent_job
    add_agent_job(agent_id, db_agent.check_interval_minutes)

    return {
        "message": f"Agent {agent_id} scheduled to run every {db_agent.check_interval_minutes} minutes",
        "agent_id": agent_id,
        "interval_minutes": db_agent.check_interval_minutes
    }


@router.post("/{agent_id}/unschedule")
def unschedule_agent(agent_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """
    Remove an agent from the automated scheduler.
    """
    db_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Set agent to stopped
    db_agent.status = AgentStatus.STOPPED
    db.commit()

    # Remove from scheduler
    from app.agents.agent_scheduler import remove_agent_job
    remove_agent_job(agent_id)

    return {
        "message": f"Agent {agent_id} removed from scheduler",
        "agent_id": agent_id
    }


@router.get("/scheduler/jobs")
def get_scheduler_jobs():
    """Get all scheduled agent jobs."""
    from app.agents.agent_scheduler import get_scheduled_jobs
    jobs = get_scheduled_jobs()
    return {"jobs": jobs}


# ============== Run History Endpoints ==============

@router.get("/{agent_id}/run-history", response_model=List[AgentRunHistoryResponse])
def get_agent_run_history(
    agent_id: int,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get run history for a specific agent.

    Returns a list of agent runs with details about what was analyzed,
    decisions made, and actions taken.
    """
    from app.models import AgentRunStatus

    db_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    query = db.query(AgentRunHistory).filter(AgentRunHistory.agent_id == agent_id)

    if status:
        try:
            run_status = AgentRunStatus(status.upper())
            query = query.filter(AgentRunHistory.status == run_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    return query.order_by(AgentRunHistory.started_at.desc()).offset(skip).limit(limit).all()


@router.get("/run-history/recent", response_model=List[AgentRunHistoryResponse])
def get_recent_run_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recent run history across all agents.

    Useful for the Agent Monitor dashboard to show recent activity.
    """
    return (
        db.query(AgentRunHistory)
        .order_by(AgentRunHistory.started_at.desc())
        .limit(limit)
        .all()
    )
