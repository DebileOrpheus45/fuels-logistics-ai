"""
Google Sheets integration endpoints.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, Site, Load
from app.integrations.sheets_service import sheets_service

router = APIRouter(prefix="/sheets", tags=["sheets"])


class SheetConfig(BaseModel):
    spreadsheet_id: str
    worksheet_name: str = "Dashboard"


class SyncRequest(BaseModel):
    spreadsheet_url: str
    sites: Optional[List[Dict[str, Any]]] = None
    loads: Optional[List[Dict[str, Any]]] = None


class SyncResponse(BaseModel):
    success: bool
    message: str
    rows_updated: int = 0


def extract_spreadsheet_id(url: str) -> str:
    """Extract spreadsheet ID from Google Sheets URL."""
    # URL format: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#...
    try:
        if "/d/" in url:
            parts = url.split("/d/")[1]
            return parts.split("/")[0]
        return url  # Assume it's already just the ID
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Google Sheets URL")


@router.get("/status")
def get_sheets_status(current_user: User = Depends(get_current_user)):
    """
    Check if Google Sheets integration is configured and working.
    """
    return {
        "configured": sheets_service.is_configured,
        "message": "Google Sheets is configured and ready" if sheets_service.is_configured
        else "Google Sheets not configured. Add sheets_credentials.json to enable."
    }


@router.post("/sync", response_model=SyncResponse)
def sync_to_sheets(
    request: SyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sync current site and load status to a Google Sheet.

    Creates/updates a dashboard with:
    - Site inventory status
    - Active loads and ETAs
    - Critical alerts
    """
    spreadsheet_id = extract_spreadsheet_id(request.spreadsheet_url)
    worksheet_name = "Dashboard"

    # If no sites provided, get from DB
    if not request.sites:
        sites = db.query(Site).all()
        site_data = [
            {
                "consignee_code": s.consignee_code,
                "consignee_name": s.consignee_name,
                "current_inventory": s.current_inventory,
                "hours_to_runout": s.hours_to_runout,
            }
            for s in sites
        ]
    else:
        site_data = request.sites

    # If no loads provided, get from DB
    if not request.loads:
        loads = db.query(Load).filter(Load.status.in_(["SCHEDULED", "IN_TRANSIT"])).all()
        load_data = [
            {
                "po_number": l.po_number,
                "destination_site_id": l.destination_site_id,
                "status": l.status.value if hasattr(l.status, 'value') else str(l.status),
                "current_eta": l.current_eta.isoformat() if l.current_eta else None,
            }
            for l in loads
        ]
    else:
        load_data = request.loads

    # Build header row
    headers = ["Site Code", "Site Name", "Inventory (gal)", "Hours to Runout", "Status", "Active Loads", "ETA"]

    # Build data rows
    rows = []
    for site in site_data:
        hours = site.get("hours_to_runout") or 999
        status = "CRITICAL" if hours < 12 else "HIGH RISK" if hours < 24 else "AT RISK" if hours < 48 else "OK"

        # Find active loads for this site
        site_loads = [l for l in load_data if l.get("destination_site_id") == site.get("id")]
        active_count = len(site_loads)
        eta = site_loads[0].get("current_eta", "N/A") if site_loads else "N/A"

        rows.append([
            site.get("consignee_code", ""),
            site.get("consignee_name", ""),
            site.get("current_inventory", 0),
            round(hours, 1) if hours < 999 else "N/A",
            status,
            active_count,
            eta
        ])

    if not sheets_service.is_configured:
        # Mock mode - just return success
        return SyncResponse(
            success=True,
            message="[MOCK] Sync completed (Google Sheets not configured)",
            rows_updated=len(rows)
        )

    try:
        # Clear and update the worksheet
        sheet = sheets_service.open_spreadsheet(spreadsheet_id)
        if not sheet:
            raise HTTPException(status_code=500, detail="Could not open spreadsheet")

        worksheet = sheet.worksheet(worksheet_name)

        # Clear existing content
        worksheet.clear()

        # Update with new data
        all_data = [headers] + rows
        worksheet.update("A1", all_data)

        return SyncResponse(
            success=True,
            message=f"Synced {len(rows)} sites to Google Sheets",
            rows_updated=len(rows)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/update-eta")
def update_eta_in_sheet(
    spreadsheet_url: str,
    po_number: str,
    eta: str,
    worksheet_name: str = "Dashboard",
    po_column: int = 1,
    eta_column: int = 7,
    current_user: User = Depends(get_current_user)
):
    """
    Update a single ETA value in a Google Sheet.

    Finds the row with the given PO number and updates the ETA column.
    """
    spreadsheet_id = extract_spreadsheet_id(spreadsheet_url)

    success = sheets_service.update_eta_column(
        spreadsheet_id=spreadsheet_id,
        worksheet_name=worksheet_name,
        po_number=po_number,
        po_column=po_column,
        eta_column=eta_column,
        eta_value=eta
    )

    if success:
        return {"success": True, "message": f"Updated ETA for PO {po_number}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update ETA")


@router.post("/append-log")
def append_log_row(
    spreadsheet_url: str,
    values: List[str],
    worksheet_name: str = "Log",
    current_user: User = Depends(get_current_user)
):
    """
    Append a row to a log worksheet.

    Useful for tracking agent activities, email sends, etc.
    """
    spreadsheet_id = extract_spreadsheet_id(spreadsheet_url)

    success = sheets_service.append_row(
        spreadsheet_id=spreadsheet_id,
        worksheet_name=worksheet_name,
        values=values
    )

    if success:
        return {"success": True, "message": "Row appended"}
    else:
        raise HTTPException(status_code=500, detail="Failed to append row")
