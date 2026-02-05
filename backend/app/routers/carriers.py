from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Carrier, User
from app.schemas import CarrierCreate, CarrierUpdate, CarrierResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/carriers", tags=["carriers"])


@router.get("/", response_model=List[CarrierResponse])
def get_carriers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all carriers."""
    return db.query(Carrier).offset(skip).limit(limit).all()


@router.get("/{carrier_id}", response_model=CarrierResponse)
def get_carrier(carrier_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Get a specific carrier."""
    carrier = db.query(Carrier).filter(Carrier.id == carrier_id).first()
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    return carrier


@router.post("/", response_model=CarrierResponse, status_code=201)
def create_carrier(carrier: CarrierCreate, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Create a new carrier."""
    db_carrier = Carrier(**carrier.model_dump())
    db.add(db_carrier)
    db.commit()
    db.refresh(db_carrier)
    return db_carrier


@router.patch("/{carrier_id}", response_model=CarrierResponse)
def update_carrier(
    carrier_id: int,
    carrier: CarrierUpdate,
    db: Session = Depends(get_db)
):
    """Update a carrier's information."""
    db_carrier = db.query(Carrier).filter(Carrier.id == carrier_id).first()
    if not db_carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")

    update_data = carrier.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_carrier, field, value)

    db.commit()
    db.refresh(db_carrier)
    return db_carrier


@router.delete("/{carrier_id}", status_code=204)
def delete_carrier(carrier_id: int, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)):
    """Delete a carrier."""
    db_carrier = db.query(Carrier).filter(Carrier.id == carrier_id).first()
    if not db_carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")

    db.delete(db_carrier)
    db.commit()
    return None
