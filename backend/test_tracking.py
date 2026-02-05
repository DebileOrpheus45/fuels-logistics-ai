from app.database import SessionLocal
from app.models import Load
from app.schemas import LoadResponse, LoadWithDetails
from sqlalchemy.orm import joinedload

db = SessionLocal()
load = db.query(Load).options(
    joinedload(Load.carrier),
    joinedload(Load.destination_site)
).filter(Load.po_number == 'PO-2024-001').first()

print(f"ORM has tracking_points: {hasattr(load, 'tracking_points')}")
print(f"ORM tracking_points length: {len(load.tracking_points) if load.tracking_points else 0}")
print(f"ORM tracking_points type: {type(load.tracking_points)}")

try:
    schema = LoadWithDetails.model_validate(load)
    print(f"\nValidation SUCCESS")
    print(f"Schema tracking_points length: {len(schema.tracking_points) if schema.tracking_points else 0}")

    dumped = schema.model_dump(mode='json')
    print(f"\nDumped keys: {list(dumped.keys())}")
    print(f"'tracking_points' in dumped: {'tracking_points' in dumped}")
    print(f"'notes' in dumped: {'notes' in dumped}")

    if 'tracking_points' in dumped:
        print(f"Dumped tracking_points length: {len(dumped['tracking_points'])}")
    else:
        print("tracking_points NOT in dumped dict!")

except Exception as e:
    print(f"\nValidation ERROR: {e}")
    import traceback
    traceback.print_exc()

db.close()
