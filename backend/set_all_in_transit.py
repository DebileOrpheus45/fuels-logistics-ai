"""
Set all scheduled loads to in_transit so they get GPS tracking data.
"""
from app.database import SessionLocal
from app.models import Load

db = SessionLocal()

try:
    loads = db.query(Load).filter(Load.status == 'scheduled').all()

    print(f"Found {len(loads)} scheduled loads")

    for load in loads:
        load.status = 'in_transit'
        print(f"  Set {load.po_number} to in_transit")

    db.commit()
    print(f"\nSuccessfully updated {len(loads)} loads to in_transit")

except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
