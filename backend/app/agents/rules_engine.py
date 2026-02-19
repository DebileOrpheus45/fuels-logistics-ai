"""
Tier 1 Rules Engine — Zero-token threshold checks.

Runs on every trigger (scheduled, email received, inventory change).
Handles ~90% of situations with simple if/then rules.
Only escalates to Tier 2 (LLM agent) when the situation is ambiguous.

Returns a list of actions to take and optionally flags for Tier 2 review.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.config import now_local
from app.database import SessionLocal
from app.models import (
    Site, Load, Carrier, AIAgent, Activity, Escalation, EmailLog,
    CarrierStats, SiteStats,
    LoadStatus, AgentStatus, ActivityType, IssueType, EscalationPriority,
    AgentExecutionMode, EscalationStatus
)
from app.services.email_service import send_eta_request

logger = logging.getLogger(__name__)


@dataclass
class RuleAction:
    """An action determined by the rules engine."""
    action_type: str  # "send_eta_email", "create_escalation", "flag_for_tier2"
    priority: str = "medium"
    site_id: Optional[int] = None
    load_id: Optional[int] = None
    carrier_id: Optional[int] = None
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RuleResult:
    """Result of running the rules engine."""
    actions: List[RuleAction] = field(default_factory=list)
    tier2_flags: List[Dict[str, Any]] = field(default_factory=list)
    sites_checked: int = 0
    loads_checked: int = 0
    summary: str = ""


def run_rules_check(agent_id: int) -> RuleResult:
    """
    Run Tier 1 rules check for all sites assigned to an agent.
    Returns actions to execute and flags for Tier 2.
    """
    db = SessionLocal()
    result = RuleResult()

    try:
        agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if not agent:
            result.summary = "Agent not found"
            return result

        sites = db.query(Site).filter(Site.assigned_agent_id == agent_id).all()
        result.sites_checked = len(sites)

        if not sites:
            result.summary = "No sites assigned"
            return result

        site_ids = [s.id for s in sites]
        active_loads = db.query(Load).filter(
            Load.destination_site_id.in_(site_ids),
            Load.status.in_([LoadStatus.SCHEDULED, LoadStatus.IN_TRANSIT, LoadStatus.DELAYED])
        ).all()
        result.loads_checked = len(active_loads)

        # Index loads by destination site
        loads_by_site = {}
        for load in active_loads:
            loads_by_site.setdefault(load.destination_site_id, []).append(load)

        # Get carrier stats for knowledge graph context
        carrier_ids = list(set(l.carrier_id for l in active_loads))
        carrier_stats = {
            cs.carrier_id: cs
            for cs in db.query(CarrierStats).filter(CarrierStats.carrier_id.in_(carrier_ids)).all()
        } if carrier_ids else {}

        # Get site stats
        site_stats = {
            ss.site_id: ss
            for ss in db.query(SiteStats).filter(SiteStats.site_id.in_(site_ids)).all()
        }

        now = now_local().replace(tzinfo=None)
        tier2_context = []

        for site in sites:
            site_loads = loads_by_site.get(site.id, [])
            ss = site_stats.get(site.id)
            hours = site.hours_to_runout or 999

            # ── Rule 1: CRITICAL runout with no active loads ──
            if hours < 12 and not site_loads:
                result.actions.append(RuleAction(
                    action_type="create_escalation",
                    priority="critical",
                    site_id=site.id,
                    description=f"{site.consignee_code} has {hours:.1f}h to runout with NO active loads. Immediate attention needed.",
                    details={"rule": "critical_no_loads", "hours_to_runout": hours}
                ))
                continue

            # ── Rule 2: HIGH risk with no active loads ──
            if hours < 24 and not site_loads:
                result.actions.append(RuleAction(
                    action_type="create_escalation",
                    priority="high",
                    site_id=site.id,
                    description=f"{site.consignee_code} has {hours:.1f}h to runout with no active loads.",
                    details={"rule": "high_risk_no_loads", "hours_to_runout": hours}
                ))
                continue

            # ── Rule 3: Below threshold — check loads ──
            if hours < site.runout_threshold_hours and site_loads:
                for load in site_loads:
                    carrier = db.query(Carrier).filter(Carrier.id == load.carrier_id).first()
                    cs = carrier_stats.get(load.carrier_id)

                    # Rule 3a: Load is DELAYED → escalate
                    if load.status == LoadStatus.DELAYED:
                        result.actions.append(RuleAction(
                            action_type="create_escalation",
                            priority="high" if hours < 24 else "medium",
                            site_id=site.id,
                            load_id=load.id,
                            description=f"Load {load.po_number} to {site.consignee_code} is DELAYED. Site has {hours:.1f}h to runout.",
                            details={"rule": "delayed_load_at_risk_site", "hours_to_runout": hours}
                        ))

                    # Rule 3b: Stale ETA (>4h since last update) → send email
                    hours_since_update = None
                    if load.last_eta_update:
                        hours_since_update = (now - load.last_eta_update).total_seconds() / 3600

                    hours_since_email = None
                    if load.last_email_sent:
                        hours_since_email = (now - load.last_email_sent).total_seconds() / 3600

                    if (hours_since_update is None or hours_since_update > 4) and \
                       (hours_since_email is None or hours_since_email > 2):
                        result.actions.append(RuleAction(
                            action_type="send_eta_email",
                            site_id=site.id,
                            load_id=load.id,
                            carrier_id=load.carrier_id,
                            description=f"Requesting ETA update for {load.po_number} (last update: {hours_since_update:.1f}h ago)" if hours_since_update else f"Requesting ETA for {load.po_number} (no ETA on file)",
                            details={"rule": "stale_eta", "hours_since_update": hours_since_update}
                        ))

                    # Rule 3c: Unreliable carrier + critical site → flag for Tier 2
                    if cs and cs.flagged_unreliable and hours < 24:
                        tier2_context.append({
                            "reason": "unreliable_carrier_critical_site",
                            "site_id": site.id,
                            "load_id": load.id,
                            "carrier_id": load.carrier_id,
                            "details": {
                                "carrier_name": carrier.carrier_name if carrier else "Unknown",
                                "late_rate": cs.reliability_score,
                                "hours_to_runout": hours,
                                "site_code": site.consignee_code
                            }
                        })

            # ── Rule 4: Site OK but load is delayed ──
            if hours >= site.runout_threshold_hours:
                for load in site_loads:
                    if load.status == LoadStatus.DELAYED:
                        # Not urgent since site has inventory, but log it
                        hours_since_email = None
                        if load.last_email_sent:
                            hours_since_email = (now - load.last_email_sent).total_seconds() / 3600

                        if hours_since_email is None or hours_since_email > 4:
                            result.actions.append(RuleAction(
                                action_type="send_eta_email",
                                site_id=site.id,
                                load_id=load.id,
                                carrier_id=load.carrier_id,
                                description=f"Load {load.po_number} is delayed to {site.consignee_code} (site OK: {hours:.0f}h inventory).",
                                details={"rule": "delayed_load_site_ok"}
                            ))

        # ── Rule 5: Multi-site correlation → Tier 2 ──
        # If multiple sites from same carrier are at risk, flag for LLM
        carrier_risk_sites = {}
        for site in sites:
            if (site.hours_to_runout or 999) < site.runout_threshold_hours:
                for load in loads_by_site.get(site.id, []):
                    carrier_risk_sites.setdefault(load.carrier_id, []).append(site.consignee_code)

        for carrier_id, risk_codes in carrier_risk_sites.items():
            if len(risk_codes) > 1:
                carrier = db.query(Carrier).filter(Carrier.id == carrier_id).first()
                tier2_context.append({
                    "reason": "multi_site_carrier_risk",
                    "carrier_id": carrier_id,
                    "details": {
                        "carrier_name": carrier.carrier_name if carrier else "Unknown",
                        "at_risk_sites": risk_codes,
                        "count": len(risk_codes)
                    }
                })

        result.tier2_flags = tier2_context

        # Build summary
        escalations = sum(1 for a in result.actions if a.action_type == "create_escalation")
        emails = sum(1 for a in result.actions if a.action_type == "send_eta_email")
        result.summary = (
            f"Checked {result.sites_checked} sites, {result.loads_checked} loads. "
            f"Actions: {escalations} escalations, {emails} ETA emails. "
            f"Tier 2 flags: {len(tier2_context)}."
        )
        logger.info(f"[Rules Engine] {result.summary}")

        return result

    finally:
        db.close()


def execute_tier1_actions(agent_id: int, actions: List[RuleAction], db: Session = None) -> List[Dict]:
    """
    Execute the actions determined by the rules engine.
    Returns list of executed action summaries.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    executed = []

    try:
        agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        if not agent:
            return executed

        for action in actions:
            if action.action_type == "send_eta_email":
                if agent.execution_mode == AgentExecutionMode.DRAFT_ONLY:
                    executed.append({
                        "type": "email_drafted",
                        "details": {"description": f"[DRAFT] {action.description}", **action.details}
                    })
                    continue

                load = db.query(Load).filter(Load.id == action.load_id).first()
                carrier = db.query(Carrier).filter(Carrier.id == action.carrier_id).first()
                if load and carrier and carrier.dispatcher_email:
                    email_log = send_eta_request(db=db, load=load, carrier=carrier, sent_by_agent_id=agent_id)
                    load.last_email_sent = now_local().replace(tzinfo=None)
                    db.commit()

                    # Log activity
                    activity = Activity(
                        agent_id=agent_id,
                        activity_type=ActivityType.EMAIL_SENT,
                        load_id=action.load_id,
                        details={"to": carrier.dispatcher_email, "po_number": load.po_number,
                                 "carrier": carrier.carrier_name, "rule": action.details.get("rule", "tier1")},
                        decision_code=action.details.get("rule", "TIER1_ETA_REQUEST")
                    )
                    db.add(activity)
                    db.commit()

                    executed.append({
                        "type": "email_sent",
                        "details": {"description": action.description, "to": carrier.dispatcher_email, **action.details}
                    })

            elif action.action_type == "create_escalation":
                if agent.execution_mode in (AgentExecutionMode.DRAFT_ONLY, AgentExecutionMode.AUTO_EMAIL):
                    executed.append({
                        "type": "escalation_drafted",
                        "details": {"description": f"[DRAFT] {action.description}", **action.details}
                    })
                    continue

                escalation = Escalation(
                    created_by_agent_id=agent_id,
                    issue_type=IssueType.RUNOUT_RISK if "runout" in action.description.lower() else IssueType.DELAYED_SHIPMENT,
                    description=action.description,
                    priority=EscalationPriority(action.priority),
                    site_id=action.site_id,
                    load_id=action.load_id
                )
                db.add(escalation)
                db.commit()

                # Log activity
                activity = Activity(
                    agent_id=agent_id,
                    activity_type=ActivityType.ESCALATION_CREATED,
                    details={"description": action.description, "priority": action.priority,
                             "rule": action.details.get("rule", "tier1")},
                    decision_code=action.details.get("rule", "TIER1_ESCALATION")
                )
                db.add(activity)
                db.commit()

                executed.append({
                    "type": "escalation_created",
                    "details": {"description": action.description, "priority": action.priority, **action.details}
                })

        return executed

    finally:
        if close_db:
            db.close()
