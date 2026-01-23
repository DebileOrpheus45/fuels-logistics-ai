from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from app.database import get_db
from app.models import Load, LoadStatus, Site, Carrier
from app.schemas import (
    LoadCreate, LoadUpdate, LoadResponse, LoadWithDetails
)

router = APIRouter(prefix="/api/loads", tags=["loads"])


@router.get("/", response_model=List[LoadResponse])
def get_loads(
    skip: int = 0,
    limit: int = 100,
    status: Optional[LoadStatus] = None,
    site_id: Optional[int] = None,
    carrier_id: Optional[int] = None,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all loads with optional filters."""
    query = db.query(Load)

    if status:
        query = query.filter(Load.status == status)

    if site_id:
        query = query.filter(Load.destination_site_id == site_id)

    if carrier_id:
        query = query.filter(Load.carrier_id == carrier_id)

    if active_only:
        query = query.filter(
            Load.status.in_([LoadStatus.SCHEDULED, LoadStatus.IN_TRANSIT])
        )

    return query.order_by(Load.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/active", response_model=List[LoadWithDetails])
def get_active_loads(db: Session = Depends(get_db)):
    """Get all active (scheduled or in transit) loads with details."""
    loads = db.query(Load).options(
        joinedload(Load.carrier),
        joinedload(Load.destination_site)
    ).filter(
        Load.status.in_([LoadStatus.SCHEDULED, LoadStatus.IN_TRANSIT])
    ).order_by(Load.current_eta.asc().nullslast()).all()

    return loads


@router.get("/needs-eta-update", response_model=List[LoadWithDetails])
def get_loads_needing_eta_update(
    hours_since_last_email: int = 4,
    db: Session = Depends(get_db)
):
    """Get active loads that need ETA updates (no Macropoint and old/no email)."""
    from datetime import timedelta
    cutoff_time = datetime.utcnow() - timedelta(hours=hours_since_last_email)

    loads = db.query(Load).options(
        joinedload(Load.carrier),
        joinedload(Load.destination_site)
    ).filter(
        and_(
            Load.status.in_([LoadStatus.SCHEDULED, LoadStatus.IN_TRANSIT]),
            Load.has_macropoint_tracking == False,
            or_(
                Load.last_email_sent.is_(None),
                Load.last_email_sent < cutoff_time
            )
        )
    ).all()

    return loads


@router.get("/{load_id}", response_model=LoadWithDetails)
def get_load(load_id: int, db: Session = Depends(get_db)):
    """Get a specific load with carrier and site details."""
    load = db.query(Load).options(
        joinedload(Load.carrier),
        joinedload(Load.destination_site)
    ).filter(Load.id == load_id).first()

    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    return load


@router.get("/by-po/{po_number}", response_model=LoadWithDetails)
def get_load_by_po(po_number: str, db: Session = Depends(get_db)):
    """Get a load by its PO number."""
    load = db.query(Load).options(
        joinedload(Load.carrier),
        joinedload(Load.destination_site)
    ).filter(Load.po_number == po_number).first()

    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    return load


@router.post("/", response_model=LoadResponse, status_code=201)
def create_load(load: LoadCreate, db: Session = Depends(get_db)):
    """Create a new load."""
    # Verify carrier and site exist
    carrier = db.query(Carrier).filter(Carrier.id == load.carrier_id).first()
    if not carrier:
        raise HTTPException(status_code=400, detail="Carrier not found")

    site = db.query(Site).filter(Site.id == load.destination_site_id).first()
    if not site:
        raise HTTPException(status_code=400, detail="Destination site not found")

    # Check for duplicate PO
    existing = db.query(Load).filter(Load.po_number == load.po_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Load with this PO number already exists")

    db_load = Load(**load.model_dump())
    db.add(db_load)
    db.commit()
    db.refresh(db_load)
    return db_load


@router.patch("/{load_id}", response_model=LoadResponse)
def update_load(load_id: int, load: LoadUpdate, db: Session = Depends(get_db)):
    """Update a load's information."""
    db_load = db.query(Load).filter(Load.id == load_id).first()
    if not db_load:
        raise HTTPException(status_code=404, detail="Load not found")

    update_data = load.model_dump(exclude_unset=True)

    # If updating ETA, also update the timestamp
    if 'current_eta' in update_data:
        update_data['last_eta_update'] = datetime.utcnow()

    for field, value in update_data.items():
        setattr(db_load, field, value)

    db.commit()
    db.refresh(db_load)
    return db_load


@router.post("/{load_id}/update-eta", response_model=LoadResponse)
def update_load_eta(
    load_id: int,
    eta: datetime,
    db: Session = Depends(get_db)
):
    """Update a load's ETA (convenience endpoint)."""
    db_load = db.query(Load).filter(Load.id == load_id).first()
    if not db_load:
        raise HTTPException(status_code=404, detail="Load not found")

    db_load.current_eta = eta
    db_load.last_eta_update = datetime.utcnow()

    db.commit()
    db.refresh(db_load)
    return db_load


@router.post("/{load_id}/mark-email-sent", response_model=LoadResponse)
def mark_email_sent(load_id: int, db: Session = Depends(get_db)):
    """Mark that an ETA request email was sent for this load."""
    db_load = db.query(Load).filter(Load.id == load_id).first()
    if not db_load:
        raise HTTPException(status_code=404, detail="Load not found")

    db_load.last_email_sent = datetime.utcnow()

    db.commit()
    db.refresh(db_load)
    return db_load


@router.delete("/{load_id}", status_code=204)
def delete_load(load_id: int, db: Session = Depends(get_db)):
    """Delete a load."""
    db_load = db.query(Load).filter(Load.id == load_id).first()
    if not db_load:
        raise HTTPException(status_code=404, detail="Load not found")

    db.delete(db_load)
    db.commit()
    return None
