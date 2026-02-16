"""
Seed historical delivered loads, resolved escalations, and rebuild the knowledge graph.

Creates ~25 delivered loads over the past 60 days with varied carriers, sites,
on-time/late delivery mix, and resolved escalations (some false alarms).

Usage:
    cd backend
    python seed_historical_data.py
"""

import random
from datetime import datetime, timedelta

from app.database import SessionLocal, engine, Base
from app.models import (
    Site, Carrier, Lane, Load, AIAgent, Escalation,
    LoadStatus, IssueType, EscalationPriority, EscalationStatus,
)


def seed_historical_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Get existing carriers and sites
        carriers = db.query(Carrier).all()
        sites = db.query(Site).all()
        agent = db.query(AIAgent).first()

        if not carriers or not sites:
            print("ERROR: No carriers or sites found. Run seed_data.py first.")
            return

        print(f"Found {len(carriers)} carriers, {len(sites)} sites")

        # Check for existing historical loads to avoid duplicates
        existing = db.query(Load).filter(Load.po_number.like("PO-HIST-%")).count()
        if existing > 0:
            print(f"Historical loads already exist ({existing} found). Skipping.")
            return

        now = datetime.utcnow()
        loads_created = []

        # --- 25 delivered loads spanning last 60 days ---
        historical_loads = [
            # (po, days_ago, carrier_idx, site_idx, volume, product, late_hours, driver)
            # late_hours: 0 = on time, >0 = hours late, <0 = early
            ("PO-HIST-001", 58, 0, 0, 8200, "gas",     0,    "Mike Rodriguez"),
            ("PO-HIST-002", 55, 1, 1, 9100, "diesel",  2.5,  "Tom Bradley"),
            ("PO-HIST-003", 52, 0, 2, 7800, "gas",     0,    "Sarah Chen"),
            ("PO-HIST-004", 50, 2, 3, 24000,"diesel",  0,    "Carlos Mendez"),
            ("PO-HIST-005", 47, 0, 4, 9500, "gas",     5.0,  "Mike Rodriguez"),
            ("PO-HIST-006", 44, 1, 0, 8800, "gas",     0,    "Linda Park"),
            ("PO-HIST-007", 42, 0, 1, 9200, "diesel",  0,    "Sarah Chen"),
            ("PO-HIST-008", 39, 2, 2, 7600, "gas",     8.0,  "James Parker"),
            ("PO-HIST-009", 37, 0, 3, 23000,"diesel",  0,    "Carlos Mendez"),
            ("PO-HIST-010", 35, 1, 4, 10200,"gas",     1.5,  "Tom Bradley"),
            ("PO-HIST-011", 32, 0, 0, 8400, "gas",     0,    "Mike Rodriguez"),
            ("PO-HIST-012", 30, 2, 1, 9000, "diesel",  12.0, "James Parker"),
            ("PO-HIST-013", 28, 1, 2, 7900, "gas",     0,    "Linda Park"),
            ("PO-HIST-014", 25, 0, 3, 25000,"diesel",  0,    "Sarah Chen"),
            ("PO-HIST-015", 22, 0, 4, 9800, "gas",     3.0,  "Mike Rodriguez"),
            ("PO-HIST-016", 20, 1, 0, 8600, "gas",     0,    "Tom Bradley"),
            ("PO-HIST-017", 18, 2, 1, 9300, "diesel",  6.5,  "James Parker"),
            ("PO-HIST-018", 15, 0, 2, 7700, "gas",     0,    "Sarah Chen"),
            ("PO-HIST-019", 13, 1, 3, 24500,"diesel",  0,    "Linda Park"),
            ("PO-HIST-020", 10, 0, 4, 10100,"gas",     0,    "Mike Rodriguez"),
            ("PO-HIST-021", 8,  2, 0, 8300, "gas",     4.0,  "James Parker"),
            ("PO-HIST-022", 6,  0, 1, 9400, "diesel",  0,    "Sarah Chen"),
            ("PO-HIST-023", 4,  1, 2, 7500, "gas",     0,    "Tom Bradley"),
            ("PO-HIST-024", 3,  0, 3, 23500,"diesel",  0,    "Carlos Mendez"),
            ("PO-HIST-025", 2,  2, 4, 9700, "gas",     7.0,  "James Parker"),
        ]

        # Also add 3 cancelled loads
        cancelled_loads = [
            ("PO-HIST-C01", 40, 1, 0, 8000, "gas",    "Tom Bradley"),
            ("PO-HIST-C02", 24, 2, 2, 7200, "diesel", "James Parker"),
            ("PO-HIST-C03", 11, 0, 4, 9900, "gas",    "Mike Rodriguez"),
        ]

        for po, days_ago, c_idx, s_idx, volume, product, late_hrs, driver in historical_loads:
            carrier = carriers[c_idx % len(carriers)]
            site = sites[s_idx % len(sites)]

            scheduled_at = now - timedelta(days=days_ago, hours=random.randint(6, 18))
            eta = scheduled_at + timedelta(hours=random.randint(8, 24))
            actual_delivery = eta + timedelta(hours=late_hrs)

            load = Load(
                po_number=po,
                tms_load_number=f"TMS-{po}",
                carrier_id=carrier.id,
                destination_site_id=site.id,
                origin_terminal=random.choice([
                    "Houston Port Terminal",
                    "Dallas Distribution Center",
                    "Gulf Coast Terminal",
                    "Atlanta Hub",
                ]),
                product_type=product,
                volume=volume,
                status=LoadStatus.DELIVERED,
                current_eta=eta,
                last_eta_update=eta - timedelta(hours=random.randint(1, 4)),
                has_macropoint_tracking=random.choice([True, True, False]),
                driver_name=driver,
                driver_phone=f"({random.randint(200,999)}) 555-{random.randint(1000,9999)}",
                last_email_sent=scheduled_at + timedelta(hours=random.randint(2, 6)),
                shipped_at=scheduled_at,
                origin_address=random.choice([
                    "12000 Ship Channel Rd, Houston, TX 77015",
                    "4500 Industrial Blvd, Dallas, TX 75207",
                    "890 Refinery Row, Pasadena, TX 77506",
                ]),
                destination_address=site.address,
                created_at=scheduled_at,
                updated_at=actual_delivery,
            )
            db.add(load)
            loads_created.append((load, late_hrs, actual_delivery, site, carrier))

        for po, days_ago, c_idx, s_idx, volume, product, driver in cancelled_loads:
            carrier = carriers[c_idx % len(carriers)]
            site = sites[s_idx % len(sites)]
            created = now - timedelta(days=days_ago)

            load = Load(
                po_number=po,
                tms_load_number=f"TMS-{po}",
                carrier_id=carrier.id,
                destination_site_id=site.id,
                origin_terminal="Houston Port Terminal",
                product_type=product,
                volume=volume,
                status=LoadStatus.CANCELLED,
                current_eta=None,
                driver_name=driver,
                created_at=created,
                updated_at=created + timedelta(hours=2),
            )
            db.add(load)

        db.commit()
        print(f"Created {len(historical_loads)} delivered loads + {len(cancelled_loads)} cancelled loads")

        # --- Escalations (resolved, mix of false alarms and real) ---
        escalation_data = [
            # (days_ago, site_idx, issue_type, priority, description, false_alarm, resolution)
            (55, 2, IssueType.RUNOUT_RISK, EscalationPriority.HIGH,
             "HOU-003 approaching runout — 14h remaining, carrier delayed",
             False, "Load PO-HIST-003 delivered 2h after escalation. Site did not run out."),

            (48, 0, IssueType.NO_CARRIER_RESPONSE, EscalationPriority.MEDIUM,
             "Summit Petroleum unresponsive — 3 ETA requests sent, no reply for 8h",
             False, "Carrier responded after direct phone call. ETA confirmed."),

            (42, 4, IssueType.DELAYED_SHIPMENT, EscalationPriority.HIGH,
             "Load PO-HIST-005 delayed 5h to CHI-005. Site at 36h inventory.",
             False, "Load delivered late. Carrier warned about SLA breach."),

            (38, 2, IssueType.RUNOUT_RISK, EscalationPriority.CRITICAL,
             "HOU-003 at 8h to runout — no confirmed ETA from carrier",
             True, "Inventory recalculated after manual dip reading — actually 28h remaining. False alarm."),

            (33, 3, IssueType.TERMINAL_OUT_OF_STOCK, EscalationPriority.HIGH,
             "Gulf Coast Terminal reporting diesel shortage — LAX-004 delivery may be affected",
             False, "Rerouted load to Dallas Distribution Center. Delivery delayed 4h but completed."),

            (28, 1, IssueType.DRIVER_ISSUE, EscalationPriority.MEDIUM,
             "Driver James Parker — phone unreachable for 6h during PO-HIST-012 transit",
             False, "Driver had phone battery issue. Resumed contact. Load delivered 12h late."),

            (22, 0, IssueType.RUNOUT_RISK, EscalationPriority.MEDIUM,
             "ATL-001 projected runout in 20h — load PO-HIST-015 running 3h late",
             True, "Consumption rate dropped overnight. Site had 32h remaining at delivery. False alarm."),

            (18, 4, IssueType.NO_CARRIER_RESPONSE, EscalationPriority.MEDIUM,
             "American Energy Carriers — no response to ETA request for PO-HIST-017",
             False, "Carrier dispatcher on PTO. Backup dispatcher confirmed ETA."),

            (14, 2, IssueType.RUNOUT_RISK, EscalationPriority.HIGH,
             "HOU-003 below threshold — 16h to runout, load PO-HIST-018 still at terminal",
             False, "Load dispatched within 1h of escalation. Delivered on time."),

            (9, 0, IssueType.DELAYED_SHIPMENT, EscalationPriority.MEDIUM,
             "Load PO-HIST-021 delayed due to traffic accident on I-10",
             False, "Rerouted via I-45. Arrived 4h late but site had adequate inventory."),

            (5, 1, IssueType.RUNOUT_RISK, EscalationPriority.MEDIUM,
             "DFW-042 consumption spike — projected runout dropped from 72h to 30h",
             True, "Weekend traffic caused temporary demand spike. Consumption normalized Monday."),

            (3, 4, IssueType.DELAYED_SHIPMENT, EscalationPriority.HIGH,
             "Load PO-HIST-025 — American Energy 7h late, CHI-005 at 22h to runout",
             False, "Load delivered. Carrier flagged for SLA review."),
        ]

        agent_id = agent.id if agent else None

        for days_ago, s_idx, issue_type, priority, desc, false_alarm, resolution in escalation_data:
            site = sites[s_idx % len(sites)]
            created = now - timedelta(days=days_ago)
            resolved = created + timedelta(hours=random.randint(1, 8))

            # Find a related load if one exists near this date
            related_load = None
            for load, _, _, ls, _ in loads_created:
                if ls.id == site.id and abs((load.created_at - created).days) <= 3:
                    related_load = load
                    break

            esc = Escalation(
                created_by_agent_id=agent_id,
                load_id=related_load.id if related_load else None,
                site_id=site.id,
                priority=priority,
                issue_type=issue_type,
                description=desc,
                status=EscalationStatus.RESOLVED,
                assigned_to="coordinator@fuelslogistics.com",
                resolution_notes=resolution,
                created_at=created,
                resolved_at=resolved,
                updated_at=resolved,
            )
            db.add(esc)

        db.commit()
        print(f"Created {len(escalation_data)} resolved escalations ({sum(1 for e in escalation_data if e[5])} false alarms)")

        # --- Rebuild knowledge graph from all this data ---
        print("\nRebuilding knowledge graph...")
        from app.services.knowledge_graph import rebuild_knowledge_graph
        result = rebuild_knowledge_graph()
        print(f"Knowledge graph rebuilt: {result}")

        # Print summary
        print("\n--- Historical Data Summary ---")
        print(f"Delivered loads:   {len(historical_loads)}")
        print(f"Cancelled loads:   {len(cancelled_loads)}")
        print(f"Escalations:       {len(escalation_data)}")
        print(f"  - Real issues:   {sum(1 for e in escalation_data if not e[5])}")
        print(f"  - False alarms:  {sum(1 for e in escalation_data if e[5])}")
        print(f"\nCarrier delivery breakdown:")
        for carrier in carriers:
            c_loads = [(l, late) for l, late, _, _, c in loads_created if c.id == carrier.id]
            on_time = sum(1 for _, late in c_loads if late <= 0)
            late = sum(1 for _, lat in c_loads if lat > 0)
            print(f"  {carrier.carrier_name}: {len(c_loads)} deliveries ({on_time} on-time, {late} late)")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_historical_data()
