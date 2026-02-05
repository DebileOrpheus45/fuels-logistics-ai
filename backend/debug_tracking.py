"""
Comprehensive debugging script to verify tracking data.
"""
import json
from app.database import SessionLocal
from app.models import Load
from sqlalchemy.orm import joinedload

db = SessionLocal()

print("=" * 80)
print("DATABASE TRACKING DATA VERIFICATION")
print("=" * 80)

# Get all loads
loads = db.query(Load).options(
    joinedload(Load.carrier),
    joinedload(Load.destination_site)
).all()

print(f"\nTotal loads in database: {len(loads)}\n")

for load in loads:
    print(f"\n{'='*80}")
    print(f"PO Number: {load.po_number}")
    print(f"Status: {load.status}")
    print(f"Origin Terminal: {load.origin_terminal}")

    # Check tracking_points
    print(f"\nTracking Points:")
    print(f"  - Has attribute: {hasattr(load, 'tracking_points')}")
    print(f"  - Value type: {type(load.tracking_points)}")
    print(f"  - Is None: {load.tracking_points is None}")
    print(f"  - Length: {len(load.tracking_points) if load.tracking_points else 0}")
    if load.tracking_points:
        print(f"  - First point: {load.tracking_points[0]}")

    # Check addresses
    print(f"\nAddresses:")
    print(f"  - origin_address: {load.origin_address}")
    print(f"  - destination_address: {load.destination_address}")

    # Check shipped_at
    print(f"\nShipped At: {load.shipped_at}")

    # Check notes
    print(f"\nNotes:")
    print(f"  - Has attribute: {hasattr(load, 'notes')}")
    print(f"  - Value type: {type(load.notes)}")
    print(f"  - Length: {len(load.notes) if load.notes else 0}")

db.close()

print("\n" + "=" * 80)
print("API SIMULATION")
print("=" * 80)

# Simulate what the API would return
db = SessionLocal()
loads = db.query(Load).options(
    joinedload(Load.carrier),
    joinedload(Load.destination_site)
).filter(Load.status.in_(['scheduled', 'in_transit'])).all()

print(f"\nActive loads: {len(loads)}\n")

for load in loads[:2]:  # First 2 loads
    load_dict = {
        "id": load.id,
        "po_number": load.po_number,
        "status": load.status.value if hasattr(load.status, 'value') else str(load.status),
        "tracking_points": load.tracking_points or [],
        "origin_address": load.origin_address,
        "destination_address": load.destination_address,
        "shipped_at": load.shipped_at.isoformat() if load.shipped_at else None,
        "notes": load.notes or [],
    }

    print(f"\n{load.po_number}:")
    print(json.dumps(load_dict, indent=2, default=str))

db.close()
