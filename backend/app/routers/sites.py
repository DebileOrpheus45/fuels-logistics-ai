from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import get_db
from app.models import Site, Load, LoadStatus, UploadAuditLog, Customer, ERPSource, ServiceType
from app.schemas import (
    SiteCreate, SiteUpdate, SiteResponse, SiteWithLoads,
    SiteInventoryStatus, SiteBatchUpdate, BatchUploadResponse,
    UploadAuditLogResponse, ERPTemplateInfo
)

router = APIRouter(prefix="/api/sites", tags=["sites"])


@router.get("/", response_model=List[SiteResponse])
def get_sites(
    skip: int = 0,
    limit: int = 100,
    at_risk_only: bool = False,
    customer: Optional[str] = None,
    service_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all sites, optionally filtered by risk status, customer, or service type."""
    query = db.query(Site)

    if at_risk_only:
        query = query.filter(
            and_(
                Site.hours_to_runout.isnot(None),
                Site.hours_to_runout <= Site.runout_threshold_hours
            )
        )

    if customer:
        query = query.filter(Site.customer == customer)

    if service_type:
        query = query.filter(Site.service_type == service_type)

    return query.offset(skip).limit(limit).all()


@router.get("/inventory-status", response_model=List[SiteInventoryStatus])
def get_inventory_status(db: Session = Depends(get_db)):
    """Get inventory status summary for all sites."""
    sites = db.query(Site).all()
    result = []

    for site in sites:
        active_loads = db.query(Load).filter(
            and_(
                Load.destination_site_id == site.id,
                Load.status.in_([LoadStatus.SCHEDULED, LoadStatus.IN_TRANSIT])
            )
        ).count()

        is_at_risk = (
            site.hours_to_runout is not None and
            site.hours_to_runout <= site.runout_threshold_hours
        )

        result.append(SiteInventoryStatus(
            site_id=site.id,
            consignee_code=site.consignee_code,
            consignee_name=site.consignee_name,
            current_inventory=site.current_inventory or 0,
            hours_to_runout=site.hours_to_runout,
            is_at_risk=is_at_risk,
            active_loads_count=active_loads
        ))

    return result


@router.get("/customers")
def get_customers():
    """Get list of available customers for dropdown selection."""
    return [
        {"value": c.value, "label": c.value.replace("_", " ").title()}
        for c in Customer
    ]


@router.get("/erp-sources")
def get_erp_sources():
    """Get list of available ERP sources for dropdown selection."""
    return [
        {"value": e.value, "label": e.value.replace("_", " ").title()}
        for e in ERPSource
    ]


@router.get("/service-types")
def get_service_types():
    """Get list of available service types."""
    return [
        {"value": s.value, "label": s.value.replace("_", " ").title()}
        for s in ServiceType
    ]


@router.get("/erp-templates/{erp_source}", response_model=ERPTemplateInfo)
def get_erp_template(erp_source: str):
    """
    Get the CSV template format for a specific ERP system.
    Each ERP has different column names and formats.
    """
    templates = {
        "fuel_shepherd": {
            "erp_source": ERPSource.FUEL_SHEPHERD,
            "display_name": "Fuel Shepherd",
            "columns": [
                "site_id", "site_name", "tank_size_gal", "usage_rate_gph",
                "alert_threshold_hrs", "min_drop_gal", "comments", "service_level"
            ],
            "required_columns": ["site_id", "site_name"],
            "sample_data": [
                {
                    "site_id": "FS-001",
                    "site_name": "Main Street Station",
                    "tank_size_gal": "10000",
                    "usage_rate_gph": "250",
                    "alert_threshold_hrs": "48",
                    "min_drop_gal": "3000",
                    "comments": "High traffic location",
                    "service_level": "inventory_and_tracking"
                }
            ]
        },
        "fuelquest": {
            "erp_source": ERPSource.FUELQUEST,
            "display_name": "FuelQuest",
            "columns": [
                "location_code", "location_name", "capacity", "consumption",
                "threshold", "minimum_delivery", "notes", "tracking_type"
            ],
            "required_columns": ["location_code", "location_name"],
            "sample_data": [
                {
                    "location_code": "FQ-001",
                    "location_name": "Downtown Depot",
                    "capacity": "15000",
                    "consumption": "300",
                    "threshold": "36",
                    "minimum_delivery": "4000",
                    "notes": "24/7 operation",
                    "tracking_type": "tracking_only"
                }
            ]
        },
        "manual": {
            "erp_source": ERPSource.MANUAL,
            "display_name": "Manual Entry",
            "columns": [
                "consignee_code", "consignee_name", "tank_capacity", "consumption_rate",
                "runout_threshold_hours", "min_delivery_quantity", "notes", "service_type"
            ],
            "required_columns": ["consignee_code", "consignee_name"],
            "sample_data": [
                {
                    "consignee_code": "SITE001",
                    "consignee_name": "Sample Station",
                    "tank_capacity": "10000",
                    "consumption_rate": "250",
                    "runout_threshold_hours": "48",
                    "min_delivery_quantity": "3000",
                    "notes": "Example notes",
                    "service_type": "inventory_and_tracking"
                }
            ]
        }
    }

    if erp_source not in templates:
        raise HTTPException(status_code=404, detail=f"Unknown ERP source: {erp_source}")

    return templates[erp_source]


@router.get("/upload-history", response_model=List[UploadAuditLogResponse])
def get_upload_history(
    limit: int = 20,
    customer: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get recent upload audit logs, optionally filtered by customer."""
    query = db.query(UploadAuditLog)

    if customer:
        query = query.filter(UploadAuditLog.customer == customer)

    return query.order_by(UploadAuditLog.created_at.desc()).limit(limit).all()


@router.get("/{site_id:int}", response_model=SiteWithLoads)
def get_site(site_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    """Get a specific site with its active loads."""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.post("/", response_model=SiteResponse, status_code=201)
def create_site(site: SiteCreate, db: Session = Depends(get_db)):
    """Create a new site."""
    existing = db.query(Site).filter(Site.consignee_code == site.consignee_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Site with this consignee code already exists")

    db_site = Site(**site.model_dump())
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site


@router.patch("/{site_id:int}", response_model=SiteResponse)
def update_site(site: SiteUpdate, site_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    """Update a site's information."""
    db_site = db.query(Site).filter(Site.id == site_id).first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found")

    update_data = site.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_site, field, value)

    db.commit()
    db.refresh(db_site)
    return db_site


@router.delete("/{site_id:int}", status_code=204)
def delete_site(site_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    """Delete a site."""
    db_site = db.query(Site).filter(Site.id == site_id).first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found")

    db.delete(db_site)
    db.commit()
    return None


@router.post("/{site_id:int}/update-inventory", response_model=SiteResponse)
def update_inventory(
    current_inventory: float,
    site_id: int = Path(..., ge=1),
    hours_to_runout: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Update a site's inventory levels (typically called by data import process)."""
    db_site = db.query(Site).filter(Site.id == site_id).first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site not found")

    db_site.current_inventory = current_inventory
    if hours_to_runout is not None:
        db_site.hours_to_runout = hours_to_runout

    db.commit()
    db.refresh(db_site)
    return db_site


@router.post("/batch-update", response_model=BatchUploadResponse)
def batch_update_sites(
    batch: SiteBatchUpdate,
    db: Session = Depends(get_db)
):
    """
    Batch update site constraints from CSV import.
    Matches sites by consignee_code and updates provided fields.
    Tags all updated sites with the specified customer and ERP source.
    Creates an audit log entry for tracking.
    """
    updated = 0
    created = 0
    not_found = []
    errors = []

    for site_data in batch.sites:
        db_site = db.query(Site).filter(
            Site.consignee_code == site_data.consignee_code
        ).first()

        if not db_site:
            not_found.append(site_data.consignee_code)
            continue

        try:
            update_data = site_data.model_dump(exclude_unset=True, exclude={'consignee_code'})
            for field, value in update_data.items():
                if value is not None:
                    setattr(db_site, field, value)
            # Always set customer and erp_source from the batch metadata
            db_site.customer = batch.customer
            db_site.erp_source = batch.erp_source
            updated += 1
        except Exception as e:
            errors.append({"code": site_data.consignee_code, "error": str(e)})

    db.commit()

    # Create audit log entry
    audit_log = UploadAuditLog(
        customer=batch.customer,
        erp_source=batch.erp_source,
        uploaded_by="coordinator",
        records_processed=len(batch.sites),
        records_updated=updated,
        records_created=created,
        records_failed=len(not_found) + len(errors),
        error_details=errors if errors else None
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return BatchUploadResponse(
        updated=updated,
        created=created,
        not_found=not_found,
        errors=errors,
        total_processed=len(batch.sites),
        audit_log_id=audit_log.id
    )


@router.get("/export-template")
def get_export_template(
    customer: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Export current site constraints as JSON for editing/re-import.
    Can be converted to CSV on frontend. Optionally filter by customer.
    """
    query = db.query(Site)
    if customer:
        query = query.filter(Site.customer == customer)

    sites = query.all()
    return [
        {
            "consignee_code": site.consignee_code,
            "consignee_name": site.consignee_name,
            "tank_capacity": site.tank_capacity,
            "consumption_rate": site.consumption_rate,
            "runout_threshold_hours": site.runout_threshold_hours,
            "min_delivery_quantity": site.min_delivery_quantity,
            "notes": site.notes,
            "service_type": site.service_type.value if site.service_type else None
        }
        for site in sites
    ]
