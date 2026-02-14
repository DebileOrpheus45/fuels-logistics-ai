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
    Site, Carrier, Lane, Load, AIAgent, User,
    LoadStatus, AgentStatus, AgentExecutionMode, UserRole
)
from app.auth import get_password_hash


def seed_database():
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Ensure users exist (even if other data already seeded)
        if db.query(User).count() == 0:
            users = [
                User(
                    username="admin",
                    email="admin@fuelslogistics.com",
                    full_name="System Admin",
                    password_hash=get_password_hash("admin123"),
                    role=UserRole.ADMIN,
                    is_active=True,
                ),
                User(
                    username="coordinator",
                    email="coordinator@fuelslogistics.com",
                    full_name="Fuel Coordinator",
                    password_hash=get_password_hash("fuel2024"),
                    role=UserRole.OPERATOR,
                    is_active=True,
                ),
            ]
            for user in users:
                db.add(user)
            db.commit()
            print(f"Created {len(users)} users (admin/admin123, coordinator/fuel2024)")

        # Check if rest of data already seeded
        if db.query(Site).count() > 0:
            print("Sites already exist. Skipping remaining seed data.")
            return

        print("Seeding database with test data...")

        # Create carriers - realistic fuel logistics companies
        carriers = [
            Carrier(
                carrier_name="Summit Petroleum Logistics",
                dispatcher_email="dispatch@summitpetro.com",
                dispatcher_phone="(713) 555-0101",
                response_time_sla_hours=4
            ),
            Carrier(
                carrier_name="Nationwide Fuel Transport",
                dispatcher_email="dispatch@nfttransport.com",
                dispatcher_phone="(817) 555-0245",
                response_time_sla_hours=4
            ),
            Carrier(
                carrier_name="American Energy Carriers",
                dispatcher_email="dispatch@americanenergy.com",
                dispatcher_phone="(404) 555-0389",
                response_time_sla_hours=6
            ),
        ]
        for carrier in carriers:
            db.add(carrier)
        db.commit()
        print(f"Created {len(carriers)} carriers")

        # Create AI Agent (starts in DRAFT_ONLY mode for safety)
        agent = AIAgent(
            agent_name="Coordinator Agent 1",
            status=AgentStatus.STOPPED,
            execution_mode=AgentExecutionMode.DRAFT_ONLY,  # Safe default - no automated actions
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

        # Create sites - realistic gas station locations
        sites_data = [
            ("ATL-001", "Peachtree Fuel & Convenience", "1245 Peachtree St NE, Atlanta, GA 30309", 10000, 6500, 36),
            ("DFW-042", "Highway 287 Travel Center", "8920 Highway 287, Fort Worth, TX 76179", 15000, 12000, 72),
            ("HOU-003", "Bay Area Fuel Stop", "2340 Bay Area Blvd, Houston, TX 77058", 8000, 2000, 18),
            ("LAX-004", "LAX Airport Fuel Services", "6201 W Imperial Hwy, Los Angeles, CA 90045", 50000, 35000, 96),
            ("CHI-005", "Midway Industrial Fuel", "5450 S Cicero Ave, Chicago, IL 60638", 12000, 8500, 48),
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

        # Create some loads - varied statuses and realistic details
        loads_data = [
            ("PO-2024-001", sites[0], carriers[0], LoadStatus.IN_TRANSIT, 8500, "gas", 6, "Mike Rodriguez", "(832) 555-7821"),
            ("PO-2024-002", sites[1], carriers[1], LoadStatus.SCHEDULED, 9000, "diesel", 24, None, None),
            ("PO-2024-003", sites[2], carriers[0], LoadStatus.IN_TRANSIT, 7500, "gas", 3, "Sarah Chen", "(713) 555-3492"),
            ("PO-2024-004", sites[3], carriers[2], LoadStatus.SCHEDULED, 25000, "diesel", 48, None, None),
            ("PO-2024-005", sites[4], carriers[1], LoadStatus.DELAYED, 10000, "gas", None, "James Parker", "(214) 555-9103"),
        ]

        for po, site, carrier, status, volume, product, eta_hours, driver, phone in loads_data:
            eta = datetime.utcnow() + timedelta(hours=eta_hours) if eta_hours else None
            load = Load(
                po_number=po,
                tms_load_number=f"TMS-{po}",
                carrier_id=carrier.id,
                destination_site_id=site.id,
                origin_terminal="Houston Port Terminal",
                product_type=product,
                volume=volume,
                status=status,
                current_eta=eta,
                last_eta_update=datetime.utcnow() if eta else None,
                has_macropoint_tracking=(status == LoadStatus.IN_TRANSIT),
                driver_name=driver,
                driver_phone=phone,
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
