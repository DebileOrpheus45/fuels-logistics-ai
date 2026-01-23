"""
Seed script to populate the database with test data.
Run this after starting Docker and the database.

Usage:
    cd backend
    python seed_data.py
"""

from datetime import datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.models import (
    Site, Carrier, Lane, Load, AIAgent,
    LoadStatus, AgentStatus
)


def seed_database():
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Site).count() > 0:
            print("Database already has data. Skipping seed.")
            return

        print("Seeding database with test data...")

        # Create carriers
        carriers = [
            Carrier(
                carrier_name="FastFuel Transport",
                dispatcher_email="dispatch@fastfuel.com",
                dispatcher_phone="555-0101",
                response_time_sla_hours=4
            ),
            Carrier(
                carrier_name="PetroHaul Inc",
                dispatcher_email="dispatch@petrohaul.com",
                dispatcher_phone="555-0102",
                response_time_sla_hours=4
            ),
            Carrier(
                carrier_name="Energy Express",
                dispatcher_email="dispatch@energyexpress.com",
                dispatcher_phone="555-0103",
                response_time_sla_hours=6
            ),
        ]
        for carrier in carriers:
            db.add(carrier)
        db.commit()
        print(f"Created {len(carriers)} carriers")

        # Create AI Agent
        agent = AIAgent(
            agent_name="Coordinator Agent 1",
            status=AgentStatus.STOPPED,
            check_interval_minutes=15,
            configuration={
                "email_templates": {
                    "eta_request": "Hi, can you please provide an updated ETA for PO #{po_number}?"
                },
                "escalation_thresholds": {
                    "critical_hours": 12,
                    "high_hours": 24
                }
            }
        )
        db.add(agent)
        db.commit()
        print("Created AI agent")

        # Create sites
        sites_data = [
            ("SITE001", "Downtown Gas Station", "123 Main St, City, ST 12345", 10000, 6500, 36),
            ("SITE002", "Highway Stop #42", "456 Highway Rd, Town, ST 12346", 15000, 12000, 72),
            ("SITE003", "Suburban Fuel Center", "789 Oak Ave, Suburb, ST 12347", 8000, 2000, 18),
            ("SITE004", "Airport Fuel Depot", "101 Airport Blvd, City, ST 12348", 50000, 35000, 96),
            ("SITE005", "Industrial Park Station", "202 Factory Ln, Industrial, ST 12349", 12000, 8500, 48),
        ]

        sites = []
        for code, name, address, capacity, inventory, hours in sites_data:
            site = Site(
                consignee_code=code,
                consignee_name=name,
                address=address,
                tank_capacity=capacity,
                current_inventory=inventory,
                hours_to_runout=hours,
                runout_threshold_hours=48,
                assigned_agent_id=agent.id
            )
            db.add(site)
            sites.append(site)
        db.commit()
        print(f"Created {len(sites)} sites")

        # Create lanes
        lanes = []
        for site in sites:
            lane = Lane(
                site_id=site.id,
                carrier_id=carriers[0].id,  # Assign first carrier
                origin_terminal="Houston Terminal",
                is_active=True
            )
            db.add(lane)
            lanes.append(lane)
        db.commit()
        print(f"Created {len(lanes)} lanes")

        # Create some loads
        loads_data = [
            ("PO-2024-001", sites[0], carriers[0], LoadStatus.IN_TRANSIT, 8500, "gas", 6),
            ("PO-2024-002", sites[1], carriers[1], LoadStatus.SCHEDULED, 9000, "diesel", 24),
            ("PO-2024-003", sites[2], carriers[0], LoadStatus.IN_TRANSIT, 7500, "gas", 3),
            ("PO-2024-004", sites[3], carriers[2], LoadStatus.SCHEDULED, 25000, "diesel", 48),
            ("PO-2024-005", sites[4], carriers[1], LoadStatus.DELAYED, 10000, "gas", None),
        ]

        for po, site, carrier, status, volume, product, eta_hours in loads_data:
            eta = datetime.utcnow() + timedelta(hours=eta_hours) if eta_hours else None
            load = Load(
                po_number=po,
                tms_load_number=f"TMS-{po}",
                carrier_id=carrier.id,
                destination_site_id=site.id,
                origin_terminal="Houston Terminal",
                product_type=product,
                volume=volume,
                status=status,
                current_eta=eta,
                last_eta_update=datetime.utcnow() if eta else None,
                has_macropoint_tracking=(status == LoadStatus.IN_TRANSIT),
                driver_name="John Doe" if status == LoadStatus.IN_TRANSIT else None,
                driver_phone="555-1234" if status == LoadStatus.IN_TRANSIT else None,
            )
            db.add(load)
        db.commit()
        print(f"Created {len(loads_data)} loads")

        print("\nDatabase seeded successfully!")
        print("\nTest data summary:")
        print(f"  - {len(carriers)} carriers")
        print(f"  - {len(sites)} sites (assigned to agent)")
        print(f"  - {len(lanes)} lanes")
        print(f"  - {len(loads_data)} loads")
        print(f"  - 1 AI agent (stopped)")
        print("\nSites at risk (< 48 hours to runout):")
        for site in sites:
            if site.hours_to_runout and site.hours_to_runout <= 48:
                print(f"  - {site.consignee_code}: {site.hours_to_runout} hours remaining")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
