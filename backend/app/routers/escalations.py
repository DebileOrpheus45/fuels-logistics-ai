from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Escalation, EscalationStatus, EscalationPriority, IssueType
from app.schemas import (
    EscalationCreate, EscalationUpdate, EscalationResponse, EscalationWithDetails
)

router = APIRouter(prefix="/api/escalations", tags=["escalations"])


@router.get("/", response_model=List[EscalationResponse])
def get_escalations(
    skip: int = 0,
    limit: int = 100,
    status: Optional[EscalationStatus] = None,
    priority: Optional[EscalationPriority] = None,
    open_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all escalations with optional filters."""
    query = db.query(Escalation)

    if status:
        query = query.filter(Escalation.status == status)

    if priority:
        query = query.filter(Escalation.priority == priority)

    if open_only:
        query = query.filter(Escalation.status != EscalationStatus.RESOLVED)

    return query.order_by(
        Escalation.priority.desc(),
        Escalation.created_at.desc()
    ).offset(skip).limit(limit).all()


@router.get("/open", response_model=List[EscalationWithDetails])
def get_open_escalations(db: Session = Depends(get_db)):
    """Get all open (unresolved) escalations with full details."""
    escalations = db.query(Escalation).options(
        joinedload(Escalation.load),
        joinedload(Escalation.site)
    ).filter(
        Escalation.status != EscalationStatus.RESOLVED
    ).order_by(
        Escalation.priority.desc(),
        Escalation.created_at.desc()
    ).all()

    return escalations


@router.get("/stats")
def get_escalation_stats(db: Session = Depends(get_db)):
    """Get escalation statistics."""
    open_count = db.query(Escalation).filter(
        Escalation.status == EscalationStatus.OPEN
    ).count()

    in_progress_count = db.query(Escalation).filter(
        Escalation.status == EscalationStatus.IN_PROGRESS
    ).count()

    critical_count = db.query(Escalation).filter(
        Escalation.status != EscalationStatus.RESOLVED,
        Escalation.priority == EscalationPriority.CRITICAL
    ).count()

    high_count = db.query(Escalation).filter(
        Escalation.status != EscalationStatus.RESOLVED,
        Escalation.priority == EscalationPriority.HIGH
    ).count()

    return {
        "open": open_count,
        "in_progress": in_progress_count,
        "critical": critical_count,
        "high_priority": high_count,
        "total_unresolved": open_count + in_progress_count
    }


@router.get("/{escalation_id}", response_model=EscalationWithDetails)
def get_escalation(escalation_id: int, db: Session = Depends(get_db)):
    """Get a specific escalation with full details."""
    escalation = db.query(Escalation).options(
        joinedload(Escalation.load),
        joinedload(Escalation.site)
    ).filter(Escalation.id == escalation_id).first()

    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return escalation


@router.post("/", response_model=EscalationResponse, status_code=201)
def create_escalation(escalation: EscalationCreate, db: Session = Depends(get_db)):
    """Create a new escalation."""
    db_escalation = Escalation(**escalation.model_dump())
    db.add(db_escalation)
    db.commit()
    db.refresh(db_escalation)
    return db_escalation


@router.patch("/{escalation_id}", response_model=EscalationResponse)
def update_escalation(
    escalation_id: int,
    escalation: EscalationUpdate,
    db: Session = Depends(get_db)
):
    """Update an escalation's status or details."""
    db_escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    if not db_escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")

    update_data = escalation.model_dump(exclude_unset=True)

    # If resolving, set the resolved timestamp
    if update_data.get('status') == EscalationStatus.RESOLVED:
        update_data['resolved_at'] = datetime.utcnow()

    for field, value in update_data.items():
        setattr(db_escalation, field, value)

    db.commit()
    db.refresh(db_escalation)
    return db_escalation


@router.post("/{escalation_id}/assign", response_model=EscalationResponse)
def assign_escalation(
    escalation_id: int,
    assigned_to: str,
    db: Session = Depends(get_db)
):
    """Assign an escalation to a human coordinator."""
    db_escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    if not db_escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")

    db_escalation.assigned_to = assigned_to
    db_escalation.status = EscalationStatus.IN_PROGRESS

    db.commit()
    db.refresh(db_escalation)
    return db_escalation


@router.post("/{escalation_id}/resolve", response_model=EscalationResponse)
def resolve_escalation(
    escalation_id: int,
    resolution_notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Mark an escalation as resolved."""
    db_escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    if not db_escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")

    db_escalation.status = EscalationStatus.RESOLVED
    db_escalation.resolved_at = datetime.utcnow()
    if resolution_notes:
        db_escalation.resolution_notes = resolution_notes

    db.commit()
    db.refresh(db_escalation)
    return db_escalation


@router.delete("/{escalation_id}", status_code=204)
def delete_escalation(escalation_id: int, db: Session = Depends(get_db)):
    """Delete an escalation."""
    db_escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    if not db_escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")

    db.delete(db_escalation)
    db.commit()
    return None
