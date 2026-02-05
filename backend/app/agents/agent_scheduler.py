"""
Agent Scheduler - Runs AI agents on a configurable schedule.
Uses APScheduler for background task scheduling.
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import AIAgent, AgentStatus
from app.agents.coordinator_agent import run_agent_check
from app.services.staleness_monitor import create_staleness_monitor

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = BackgroundScheduler()
_scheduler_started = False


def run_scheduled_agent_check(agent_id: int):
    """
    Run a scheduled check for an agent.
    Called by the scheduler at configured intervals.
    """
    db: Session = SessionLocal()
    try:
        agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()

        if not agent:
            logger.warning(f"Agent {agent_id} not found, skipping scheduled check")
            return

        if agent.status != AgentStatus.ACTIVE:
            logger.info(f"Agent {agent_id} is not active (status: {agent.status}), skipping check")
            return

        logger.info(f"Running scheduled check for agent {agent_id} ({agent.agent_name})")
        result = run_agent_check(agent_id)
        logger.info(f"Agent {agent_id} check completed: {result.get('success', False)}")

    except Exception as e:
        logger.error(f"Error in scheduled check for agent {agent_id}: {e}")
    finally:
        db.close()


def add_agent_job(agent_id: int, interval_minutes: int = 15):
    """
    Add a scheduled job for an agent.

    Args:
        agent_id: The agent's database ID
        interval_minutes: How often to run checks (default 15 minutes)
    """
    job_id = f"agent_{agent_id}_check"

    # Remove existing job if any
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    scheduler.add_job(
        run_scheduled_agent_check,
        trigger=IntervalTrigger(minutes=interval_minutes),
        args=[agent_id],
        id=job_id,
        name=f"Agent {agent_id} Check",
        replace_existing=True
    )

    logger.info(f"Scheduled agent {agent_id} to run every {interval_minutes} minutes")


def remove_agent_job(agent_id: int):
    """Remove a scheduled job for an agent."""
    job_id = f"agent_{agent_id}_check"

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Removed scheduled job for agent {agent_id}")


def run_staleness_check_job():
    """
    Run staleness check for all sites and loads.
    Called by the scheduler at configured intervals.
    """
    db: Session = SessionLocal()
    try:
        logger.info("Running scheduled staleness check")
        monitor = create_staleness_monitor(db)
        summary = monitor.run_staleness_check()
        logger.info(
            f"Staleness check complete: "
            f"{summary['stale_inventory_count']} stale inventories, "
            f"{summary['stale_eta_count']} stale ETAs"
        )
    except Exception as e:
        logger.error(f"Error in scheduled staleness check: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler."""
    global _scheduler_started

    if _scheduler_started:
        return

    scheduler.start()
    _scheduler_started = True
    logger.info("Agent scheduler started")

    # Load all active agents and schedule them
    db: Session = SessionLocal()
    try:
        active_agents = db.query(AIAgent).filter(AIAgent.status == AgentStatus.ACTIVE).all()

        for agent in active_agents:
            add_agent_job(agent.id, agent.check_interval_minutes)

        logger.info(f"Loaded {len(active_agents)} active agents into scheduler")
    finally:
        db.close()

    # Schedule staleness monitoring (runs every 30 minutes)
    scheduler.add_job(
        run_staleness_check_job,
        trigger=IntervalTrigger(minutes=30),
        id="staleness_monitor",
        name="Staleness Monitor",
        replace_existing=True
    )
    logger.info("Scheduled staleness monitoring to run every 30 minutes")


def stop_scheduler():
    """Stop the background scheduler."""
    global _scheduler_started

    if scheduler.running:
        scheduler.shutdown(wait=False)
        _scheduler_started = False
        logger.info("Agent scheduler stopped")


def get_scheduled_jobs():
    """Get list of all scheduled jobs."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None
        })
    return jobs
