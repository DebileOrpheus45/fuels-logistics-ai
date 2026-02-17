from typing import List, Optional
from datetime import datetime
import logging
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
import json
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from app.database import get_db
from app.models import Load, LoadStatus, Site, Carrier, User
from app.schemas import LoadCreate, LoadUpdate, LoadResponse, LoadWithDetails
from app.auth import get_current_user
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

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


@router.get("/active")
def get_active_loads(db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Get all active (scheduled or in transit) loads with details."""
    loads = db.query(Load).options(
        joinedload(Load.carrier),
        joinedload(Load.destination_site)
    ).filter(
        Load.status.in_([LoadStatus.SCHEDULED, LoadStatus.IN_TRANSIT])
    ).order_by(Load.current_eta.asc().nullslast()).all()

    # Manually construct the response to ensure tracking_points is included
    result = []
    for load in loads:
        load_dict = {
            "id": load.id,
            "po_number": load.po_number,
            "tms_load_number": load.tms_load_number,
            "lane_id": load.lane_id,
            "carrier_id": load.carrier_id,
            "destination_site_id": load.destination_site_id,
            "origin_terminal": load.origin_terminal,
            "product_type": load.product_type,
            "volume": load.volume,
            "status": load.status.value if load.status else None,
            "has_macropoint_tracking": load.has_macropoint_tracking,
            "driver_name": load.driver_name,
            "driver_phone": load.driver_phone,
            "current_eta": load.current_eta.isoformat() if load.current_eta else None,
            "last_eta_update": load.last_eta_update.isoformat() if load.last_eta_update else None,
            "last_email_sent": load.last_email_sent.isoformat() if load.last_email_sent else None,
            "notes": load.notes or [],
            "tracking_points": load.tracking_points or [],
            "origin_address": load.origin_address,
            "destination_address": load.destination_address,
            "shipped_at": load.shipped_at.isoformat() if load.shipped_at else None,
            "created_at": load.created_at.isoformat() if load.created_at else None,
            "updated_at": load.updated_at.isoformat() if load.updated_at else None,
            "carrier": {
                "id": load.carrier.id,
                "carrier_name": load.carrier.carrier_name,
                "dispatcher_email": load.carrier.dispatcher_email,
                "dispatcher_phone": load.carrier.dispatcher_phone,
                "response_time_sla_hours": load.carrier.response_time_sla_hours,
                "created_at": load.carrier.created_at.isoformat() if load.carrier.created_at else None,
                "updated_at": load.carrier.updated_at.isoformat() if load.carrier.updated_at else None,
            } if load.carrier else None,
            "destination_site": {
                "id": load.destination_site.id,
                "consignee_code": load.destination_site.consignee_code,
                "consignee_name": load.destination_site.consignee_name,
                "address": load.destination_site.address,
                "tank_capacity": load.destination_site.tank_capacity,
                "current_inventory": load.destination_site.current_inventory,
                "consumption_rate": load.destination_site.consumption_rate,
                "hours_to_runout": load.destination_site.hours_to_runout,
                "runout_threshold_hours": load.destination_site.runout_threshold_hours,
                "min_delivery_quantity": load.destination_site.min_delivery_quantity,
                "notes": load.destination_site.notes,
                "customer": load.destination_site.customer,
                "erp_source": load.destination_site.erp_source,
                "service_type": load.destination_site.service_type,
                "assigned_agent_id": load.destination_site.assigned_agent_id,
                "created_at": load.destination_site.created_at.isoformat() if load.destination_site.created_at else None,
                "updated_at": load.destination_site.updated_at.isoformat() if load.destination_site.updated_at else None,
            } if load.destination_site else None,
        }
        result.append(load_dict)

    return JSONResponse(content=result)


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
def get_load(load_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Get a specific load with carrier and site details."""
    load = db.query(Load).options(
        joinedload(Load.carrier),
        joinedload(Load.destination_site)
    ).filter(Load.id == load_id).first()

    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    return load


@router.get("/by-po/{po_number}", response_model=LoadWithDetails)
def get_load_by_po(po_number: str, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Get a load by its PO number."""
    load = db.query(Load).options(
        joinedload(Load.carrier),
        joinedload(Load.destination_site)
    ).filter(Load.po_number == po_number).first()

    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    return load


@router.post("/", response_model=LoadResponse, status_code=201)
def create_load(load: LoadCreate, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
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
def update_load(load_id: int, load: LoadUpdate, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
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
def mark_email_sent(load_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Mark that an ETA request email was sent for this load."""
    db_load = db.query(Load).filter(Load.id == load_id).first()
    if not db_load:
        raise HTTPException(status_code=404, detail="Load not found")

    db_load.last_email_sent = datetime.utcnow()

    db.commit()
    db.refresh(db_load)
    return db_load


@router.post("/{load_id}/notes", response_model=LoadResponse)
def add_note_to_load(
    load_id: int,
    note_text: str,
    author: str,
    note_type: str = "human",  # "human" or "ai"
    db: Session = Depends(get_db)
):
    """Add a collaborative note to a load."""
    db_load = db.query(Load).filter(Load.id == load_id).first()
    if not db_load:
        raise HTTPException(status_code=404, detail="Load not found")

    # Get existing notes or initialize empty list
    notes = db_load.notes if db_load.notes else []

    # Add new note
    new_note = {
        "author": author,
        "type": note_type,
        "text": note_text,
        "timestamp": datetime.utcnow().isoformat()
    }
    notes.append(new_note)

    db_load.notes = notes
    db.commit()
    db.refresh(db_load)
    return db_load


@router.post("/{load_id}/request-eta")
def request_eta_for_load(
    load_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send an ETA request email for a single load."""
    load = db.query(Load).options(
        joinedload(Load.carrier),
        joinedload(Load.destination_site),
    ).filter(Load.id == load_id).first()
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    if not load.carrier or not load.carrier.dispatcher_email:
        raise HTTPException(status_code=400, detail="No dispatcher email for carrier")

    site = load.destination_site
    hours_to_runout = site.hours_to_runout if site else None

    result = email_service.send_eta_request(
        to_email=load.carrier.dispatcher_email,
        carrier_name=load.carrier.carrier_name,
        po_number=load.po_number,
        site_name=site.consignee_name if site else "Unknown",
        hours_to_runout=hours_to_runout,
        driver_name=load.driver_name,
    )

    if result.get("success"):
        load.last_email_sent = datetime.utcnow()
        db.commit()

    return {
        "load_id": load.id,
        "po_number": load.po_number,
        "carrier": load.carrier.carrier_name,
        "to_email": load.carrier.dispatcher_email,
        "success": result.get("success", False),
        "message": result.get("error") if not result.get("success") else "ETA request sent",
    }


@router.post("/request-eta-all")
def request_eta_for_all_active_loads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send ETA request emails for all active loads (scheduled + in transit)."""
    loads = db.query(Load).options(
        joinedload(Load.carrier),
        joinedload(Load.destination_site),
    ).filter(
        Load.status.in_([LoadStatus.SCHEDULED, LoadStatus.IN_TRANSIT])
    ).all()

    results = []
    sent_count = 0
    for load in loads:
        if not load.carrier or not load.carrier.dispatcher_email:
            results.append({
                "load_id": load.id,
                "po_number": load.po_number,
                "success": False,
                "message": "No dispatcher email",
            })
            continue

        site = load.destination_site
        hours_to_runout = site.hours_to_runout if site else None

        result = email_service.send_eta_request(
            to_email=load.carrier.dispatcher_email,
            carrier_name=load.carrier.carrier_name,
            po_number=load.po_number,
            site_name=site.consignee_name if site else "Unknown",
            hours_to_runout=hours_to_runout,
            driver_name=load.driver_name,
        )

        if result.get("success"):
            load.last_email_sent = datetime.utcnow()
            sent_count += 1

        results.append({
            "load_id": load.id,
            "po_number": load.po_number,
            "carrier": load.carrier.carrier_name,
            "success": result.get("success", False),
            "message": result.get("error") if not result.get("success") else "Sent",
        })

        # Resend free tier: 2 req/s rate limit
        time.sleep(1)

    db.commit()

    return {
        "total": len(loads),
        "sent": sent_count,
        "failed": len(loads) - sent_count,
        "results": results,
    }


@router.delete("/{load_id}", status_code=204)
def delete_load(load_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Delete a load."""
    db_load = db.query(Load).filter(Load.id == load_id).first()
    if not db_load:
        raise HTTPException(status_code=404, detail="Load not found")

    db.delete(db_load)
    db.commit()
    return None
