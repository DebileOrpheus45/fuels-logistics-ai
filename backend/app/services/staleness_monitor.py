"""
Staleness monitoring service for detecting and alerting on stale data.

This service checks for:
- Stale inventory data (no updates from ERP/manual entry)
- Stale ETA data (no updates from carriers/Macropoint)

When data becomes stale, it creates escalations for human review.
"""

import logging
from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session

from app.models import Site, Load, Escalation, EscalationStatus, EscalationPriority
from app.database import get_db

logger = logging.getLogger(__name__)


class StalenessMonitor:
    """Monitor for stale inventory and ETA data."""

    def __init__(self, db: Session):
        self.db = db

    def check_inventory_staleness(self) -> List[Dict]:
        """
        Check all sites for stale inventory data.

        Returns:
            List of dicts with staleness info for sites with stale data
        """
        sites = self.db.query(Site).filter(
            Site.service_type == 'inventory_and_tracking'
        ).all()

        stale_sites = []

        for site in sites:
            if site.is_inventory_stale:
                staleness_hours = site.inventory_staleness_hours or 0

                stale_sites.append({
                    "site_id": site.id,
                    "site_name": site.consignee_name,
                    "site_code": site.consignee_code,
                    "staleness_hours": staleness_hours,
                    "last_update": site.last_inventory_update_at,
                    "threshold_hours": site.inventory_staleness_threshold_hours
                })

                # Create escalation if needed
                self._create_inventory_staleness_escalation(site, staleness_hours)

        return stale_sites

    def check_eta_staleness(self) -> List[Dict]:
        """
        Check all active loads for stale ETA data.

        Returns:
            List of dicts with staleness info for loads with stale ETAs
        """
        active_loads = self.db.query(Load).filter(
            Load.status.in_(['scheduled', 'in_transit'])
        ).all()

        stale_loads = []

        for load in active_loads:
            if load.is_eta_stale:
                staleness_hours = load.eta_staleness_hours or 0

                stale_loads.append({
                    "load_id": load.id,
                    "po_number": load.po_number,
                    "carrier_name": load.carrier.carrier_name if load.carrier else 'N/A',
                    "destination": load.destination_site.consignee_code if load.destination_site else 'N/A',
                    "staleness_hours": staleness_hours,
                    "last_update": load.last_eta_update_at,
                    "threshold_hours": load.eta_staleness_threshold_hours
                })

                # Create escalation if needed
                self._create_eta_staleness_escalation(load, staleness_hours)

        return stale_loads

    def _create_inventory_staleness_escalation(self, site: Site, staleness_hours: float):
        """Create an escalation for stale inventory data."""
        # Check if we already have an open escalation for this
        existing = self.db.query(Escalation).filter(
            Escalation.site_id == site.id,
            Escalation.escalation_type == 'stale_inventory',
            Escalation.status == EscalationStatus.OPEN
        ).first()

        if existing:
            # Update existing escalation with latest staleness
            existing.description = (
                f"Inventory data for {site.consignee_code} is stale. "
                f"No updates received for {staleness_hours:.1f} hours "
                f"(threshold: {site.inventory_staleness_threshold_hours}h). "
                f"Last update: {site.last_inventory_update_at.strftime('%Y-%m-%d %H:%M') if site.last_inventory_update_at else 'Never'}."
            )
            self.db.commit()
            return

        # Determine priority based on staleness severity
        if staleness_hours > site.inventory_staleness_threshold_hours * 2:
            priority = EscalationPriority.CRITICAL
        elif staleness_hours > site.inventory_staleness_threshold_hours * 1.5:
            priority = EscalationPriority.HIGH
        else:
            priority = EscalationPriority.MEDIUM

        escalation = Escalation(
            escalation_type='stale_inventory',
            priority=priority,
            site_id=site.id,
            load_id=None,
            description=(
                f"Inventory data for {site.consignee_code} is stale. "
                f"No updates received for {staleness_hours:.1f} hours "
                f"(threshold: {site.inventory_staleness_threshold_hours}h). "
                f"Last update: {site.last_inventory_update_at.strftime('%Y-%m-%d %H:%M') if site.last_inventory_update_at else 'Never'}."
            ),
            recommended_action=(
                f"1. Check ERP system connectivity for {site.customer or 'this customer'}\n"
                f"2. Verify snapshot ingestion API is receiving data\n"
                f"3. Contact site operations to verify fuel level\n"
                f"4. Consider manual data entry if ERP is down"
            ),
            status=EscalationStatus.OPEN
        )

        self.db.add(escalation)
        self.db.commit()
        logger.info(f"Created inventory staleness escalation for site {site.consignee_code}")

    def _create_eta_staleness_escalation(self, load: Load, staleness_hours: float):
        """Create an escalation for stale ETA data."""
        # Check if we already have an open escalation for this
        existing = self.db.query(Escalation).filter(
            Escalation.load_id == load.id,
            Escalation.escalation_type == 'stale_eta',
            Escalation.status == EscalationStatus.OPEN
        ).first()

        if existing:
            # Update existing escalation with latest staleness
            existing.description = (
                f"ETA for load {load.po_number} is stale. "
                f"No updates received for {staleness_hours:.1f} hours "
                f"(threshold: {load.eta_staleness_threshold_hours}h). "
                f"Last update: {load.last_eta_update_at.strftime('%Y-%m-%d %H:%M') if load.last_eta_update_at else 'Never'}."
            )
            self.db.commit()
            return

        # Determine priority based on staleness and destination urgency
        if load.destination_site and load.destination_site.hours_to_runout < 24:
            priority = EscalationPriority.CRITICAL
        elif staleness_hours > load.eta_staleness_threshold_hours * 1.5:
            priority = EscalationPriority.HIGH
        else:
            priority = EscalationPriority.MEDIUM

        carrier_name = load.carrier.carrier_name if load.carrier else 'Unknown Carrier'
        destination = load.destination_site.consignee_code if load.destination_site else 'Unknown'

        escalation = Escalation(
            escalation_type='stale_eta',
            priority=priority,
            site_id=load.destination_site_id,
            load_id=load.id,
            description=(
                f"ETA for load {load.po_number} is stale. "
                f"No updates received for {staleness_hours:.1f} hours "
                f"(threshold: {load.eta_staleness_threshold_hours}h). "
                f"Carrier: {carrier_name}, Destination: {destination}. "
                f"Last update: {load.last_eta_update_at.strftime('%Y-%m-%d %H:%M') if load.last_eta_update_at else 'Never'}."
            ),
            recommended_action=(
                f"1. Contact {carrier_name} dispatcher for status update\n"
                f"2. Check if Macropoint tracking is functioning\n"
                f"3. Verify carrier email integration\n"
                f"4. Consider calling driver directly if urgent"
            ),
            status=EscalationStatus.OPEN
        )

        self.db.add(escalation)
        self.db.commit()
        logger.info(f"Created ETA staleness escalation for load {load.po_number}")

    def run_staleness_check(self) -> Dict:
        """
        Run complete staleness check for all sites and loads.

        Returns:
            Summary of staleness findings
        """
        logger.info("Running staleness check...")

        stale_sites = self.check_inventory_staleness()
        stale_loads = self.check_eta_staleness()

        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "stale_inventory_count": len(stale_sites),
            "stale_eta_count": len(stale_loads),
            "stale_sites": stale_sites,
            "stale_loads": stale_loads
        }

        logger.info(
            f"Staleness check complete: "
            f"{len(stale_sites)} sites with stale inventory, "
            f"{len(stale_loads)} loads with stale ETAs"
        )

        return summary


def create_staleness_monitor(db: Session) -> StalenessMonitor:
    """Factory function to create a staleness monitor."""
    return StalenessMonitor(db)
