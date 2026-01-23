from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import Site, Load
from app.schemas import SnapshotIngestion, SnapshotIngestionResponse

router = APIRouter(prefix="/api/snapshots", tags=["snapshots"])


@router.post("/ingest", response_model=SnapshotIngestionResponse)
def ingest_snapshot(
    snapshot: SnapshotIngestion,
    db: Session = Depends(get_db)
):
    """
    Ingest an hourly snapshot of site and load state.

    This endpoint updates the CURRENT STATE (inventory levels, ETAs) of sites and loads,
    separate from their configuration/constraints.

    Use cases:
    - Hourly exports from fuel management systems
    - Google Sheets automated pulls
    - Manual updates from coordinator

    Updates:
    - Site current_inventory, hours_to_runout, last_inventory_update_at
    - Load current_eta, status, driver info, last_eta_update_at
    """
    sites_updated = 0
    sites_not_found = []
    loads_updated = 0
    loads_not_found = []
    errors = []

    # Update sites
    for site_state in snapshot.sites:
        db_site = db.query(Site).filter(
            Site.consignee_code == site_state.site_id
        ).first()

        if not db_site:
            sites_not_found.append(site_state.site_id)
            continue

        try:
            # Update inventory state
            if site_state.current_inventory is not None:
                db_site.current_inventory = site_state.current_inventory
                db_site.last_inventory_update_at = snapshot.snapshot_time

            if site_state.hours_to_runout is not None:
                db_site.hours_to_runout = site_state.hours_to_runout

            # Tag with customer/ERP if not already set
            if not db_site.customer:
                db_site.customer = snapshot.customer
            if not db_site.erp_source:
                db_site.erp_source = snapshot.erp_source

            sites_updated += 1

        except Exception as e:
            errors.append({
                "site_id": site_state.site_id,
                "error": str(e)
            })

    # Update loads
    for load_state in snapshot.loads:
        db_load = db.query(Load).filter(
            Load.po_number == load_state.po_number
        ).first()

        if not db_load:
            loads_not_found.append(load_state.po_number)
            continue

        try:
            # Update ETA and status
            if load_state.current_eta is not None:
                # Only update last_eta_update_at if ETA actually changed
                if db_load.current_eta != load_state.current_eta:
                    db_load.current_eta = load_state.current_eta
                    db_load.last_eta_update_at = snapshot.snapshot_time
                    db_load.last_eta_update = snapshot.snapshot_time  # Legacy field

            if load_state.status is not None:
                db_load.status = load_state.status

            if load_state.driver_name is not None:
                db_load.driver_name = load_state.driver_name

            if load_state.driver_phone is not None:
                db_load.driver_phone = load_state.driver_phone

            if load_state.volume is not None:
                db_load.volume = load_state.volume

            loads_updated += 1

        except Exception as e:
            errors.append({
                "po_number": load_state.po_number,
                "error": str(e)
            })

    db.commit()

    return SnapshotIngestionResponse(
        success=len(errors) == 0,
        snapshot_time=snapshot.snapshot_time,
        source=snapshot.source,
        sites_updated=sites_updated,
        sites_not_found=sites_not_found,
        loads_updated=loads_updated,
        loads_not_found=loads_not_found,
        errors=errors
    )
