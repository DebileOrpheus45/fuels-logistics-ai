"""
Knowledge Graph Service — Passive intelligence from operational data.

Updates carrier reliability and site consumption stats after events:
- Load delivered → update carrier on-time stats
- Escalation resolved → update site false alarm rate
- Email received → update carrier responsiveness
- Non-ETA email → flag and log anomaly

Zero LLM tokens — pure SQL aggregation.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    CarrierStats, SiteStats, Carrier, Site, Load, Escalation, InboundEmail,
    LoadStatus, EscalationStatus, EscalationPriority
)

logger = logging.getLogger(__name__)


def _ensure_carrier_stats(db: Session, carrier_id: int) -> CarrierStats:
    """Get or create CarrierStats for a carrier."""
    stats = db.query(CarrierStats).filter(CarrierStats.carrier_id == carrier_id).first()
    if not stats:
        stats = CarrierStats(carrier_id=carrier_id)
        db.add(stats)
        db.commit()
        db.refresh(stats)
    return stats


def _ensure_site_stats(db: Session, site_id: int) -> SiteStats:
    """Get or create SiteStats for a site."""
    stats = db.query(SiteStats).filter(SiteStats.site_id == site_id).first()
    if not stats:
        stats = SiteStats(site_id=site_id)
        db.add(stats)
        db.commit()
        db.refresh(stats)
    return stats


def _compute_reliability_score(stats: CarrierStats) -> float:
    """Compute reliability score from 0 (worst) to 1 (best)."""
    if stats.total_deliveries == 0:
        return 0.5  # No data → neutral

    on_time_rate = stats.on_time_deliveries / stats.total_deliveries

    # Factor in response rate
    response_rate = 1.0
    if stats.total_eta_requests > 0:
        response_rate = stats.eta_responses_received / stats.total_eta_requests

    # Weighted: 70% delivery, 30% responsiveness
    score = (on_time_rate * 0.7) + (response_rate * 0.3)
    return round(min(1.0, max(0.0, score)), 3)


def on_load_delivered(load_id: int, actual_delivery_time: Optional[datetime] = None):
    """
    Called when a load is marked as delivered.
    Updates carrier stats and site delivery patterns.
    """
    db = SessionLocal()
    try:
        load = db.query(Load).filter(Load.id == load_id).first()
        if not load:
            return

        actual = actual_delivery_time or datetime.utcnow()

        # ── Update carrier stats ──
        cs = _ensure_carrier_stats(db, load.carrier_id)
        cs.total_deliveries += 1

        was_late = False
        delay_hours = 0.0
        if load.current_eta and actual > load.current_eta:
            was_late = True
            delay_hours = (actual - load.current_eta).total_seconds() / 3600
            cs.late_deliveries += 1
            # Running average delay
            if cs.avg_delay_hours > 0:
                cs.avg_delay_hours = (cs.avg_delay_hours * (cs.late_deliveries - 1) + delay_hours) / cs.late_deliveries
            else:
                cs.avg_delay_hours = delay_hours
            cs.worst_delay_hours = max(cs.worst_delay_hours, delay_hours)
        else:
            cs.on_time_deliveries += 1

        # Update recent deliveries (keep last 10)
        recent = cs.recent_deliveries or []
        recent.append({
            "on_time": not was_late,
            "delay_hours": round(delay_hours, 1),
            "date": actual.isoformat(),
            "load_id": load_id,
            "po_number": load.po_number
        })
        cs.recent_deliveries = recent[-10:]

        # Recompute reliability
        cs.reliability_score = _compute_reliability_score(cs)
        cs.flagged_unreliable = cs.reliability_score < 0.4

        # ── Update site stats ──
        ss = _ensure_site_stats(db, load.destination_site_id)
        ss.total_deliveries_received += 1

        # Add to recent events
        events = ss.recent_events or []
        events.append({
            "type": "delivery",
            "date": actual.isoformat(),
            "details": f"PO {load.po_number} delivered {'late' if was_late else 'on time'}",
            "carrier": load.carrier_id
        })
        ss.recent_events = events[-10:]

        db.commit()
        logger.info(f"[KnowledgeGraph] Load {load_id} delivered: carrier {'LATE' if was_late else 'ON TIME'}, score={cs.reliability_score}")

    except Exception as e:
        logger.error(f"[KnowledgeGraph] Error on load delivered: {e}")
        db.rollback()
    finally:
        db.close()


def on_escalation_resolved(escalation_id: int, was_false_alarm: bool = False):
    """
    Called when an escalation is resolved.
    Updates site false alarm rate.
    """
    db = SessionLocal()
    try:
        esc = db.query(Escalation).filter(Escalation.id == escalation_id).first()
        if not esc or not esc.site_id:
            return

        ss = _ensure_site_stats(db, esc.site_id)
        ss.total_escalations += 1
        if was_false_alarm:
            ss.false_alarm_count += 1
        ss.false_alarm_rate = round(ss.false_alarm_count / ss.total_escalations, 3) if ss.total_escalations > 0 else 0.0

        # Recompute risk score
        if ss.total_escalations > 0:
            real_escalation_rate = (ss.total_escalations - ss.false_alarm_count) / max(ss.total_deliveries_received, 1)
            ss.risk_score = round(min(1.0, real_escalation_rate), 3)

        events = ss.recent_events or []
        events.append({
            "type": "escalation_resolved",
            "date": datetime.utcnow().isoformat(),
            "details": f"{'False alarm' if was_false_alarm else 'Real issue'}: {esc.description[:80]}",
            "priority": esc.priority.value
        })
        ss.recent_events = events[-10:]

        db.commit()
        logger.info(f"[KnowledgeGraph] Escalation {escalation_id} resolved: false_alarm={was_false_alarm}, site false_alarm_rate={ss.false_alarm_rate}")

    except Exception as e:
        logger.error(f"[KnowledgeGraph] Error on escalation resolved: {e}")
        db.rollback()
    finally:
        db.close()


def on_eta_email_response(carrier_id: int, request_sent_at: Optional[datetime] = None):
    """
    Called when a carrier responds to an ETA request email.
    Updates carrier responsiveness stats.
    """
    db = SessionLocal()
    try:
        cs = _ensure_carrier_stats(db, carrier_id)
        cs.eta_responses_received += 1

        if request_sent_at:
            response_hours = (datetime.utcnow() - request_sent_at).total_seconds() / 3600
            if cs.avg_response_time_hours is not None:
                # Running average
                n = cs.eta_responses_received
                cs.avg_response_time_hours = (cs.avg_response_time_hours * (n - 1) + response_hours) / n
            else:
                cs.avg_response_time_hours = response_hours

        cs.reliability_score = _compute_reliability_score(cs)
        db.commit()
        logger.info(f"[KnowledgeGraph] Carrier {carrier_id} responded to ETA request, score={cs.reliability_score}")

    except Exception as e:
        logger.error(f"[KnowledgeGraph] Error on ETA response: {e}")
        db.rollback()
    finally:
        db.close()


def on_eta_request_sent(carrier_id: int):
    """Called when an ETA request email is sent to a carrier."""
    db = SessionLocal()
    try:
        cs = _ensure_carrier_stats(db, carrier_id)
        cs.total_eta_requests += 1
        db.commit()
    except Exception as e:
        logger.error(f"[KnowledgeGraph] Error on ETA request sent: {e}")
        db.rollback()
    finally:
        db.close()


def on_unparseable_email(from_email: str, subject: str, body: str, load_id: Optional[int] = None):
    """
    Called when an inbound email can't be parsed as an ETA.
    Checks for important non-ETA content (supplier issues, refusals, etc.)
    and creates escalation if needed.
    """
    db = SessionLocal()
    try:
        # Check for keywords indicating important non-ETA content
        body_lower = body.lower()
        important_keywords = {
            "out of stock": ("terminal_out_of_stock", "critical", "Terminal out of stock reported"),
            "ran out": ("terminal_out_of_stock", "critical", "Supplier reports fuel shortage"),
            "shortage": ("terminal_out_of_stock", "high", "Fuel shortage reported by carrier"),
            "cannot deliver": ("driver_issue", "high", "Carrier cannot complete delivery"),
            "can't deliver": ("driver_issue", "high", "Carrier cannot complete delivery"),
            "truck broke": ("driver_issue", "high", "Carrier reports vehicle breakdown"),
            "breakdown": ("driver_issue", "medium", "Carrier reports breakdown"),
            "cancelled": ("other", "high", "Carrier indicates load cancellation"),
            "canceled": ("other", "high", "Carrier indicates load cancellation"),
            "refuse": ("other", "high", "Carrier refusal detected"),
            "accident": ("driver_issue", "critical", "Accident reported by carrier"),
        }

        matched_issue = None
        for keyword, (issue_type, priority, description) in important_keywords.items():
            if keyword in body_lower:
                matched_issue = (issue_type, priority, description)
                break

        if matched_issue:
            issue_type, priority, desc = matched_issue
            from app.models import IssueType, EscalationPriority, Escalation

            # Get site from load if available
            site_id = None
            if load_id:
                load = db.query(Load).filter(Load.id == load_id).first()
                if load:
                    site_id = load.destination_site_id

            escalation = Escalation(
                issue_type=IssueType(issue_type),
                description=f"{desc}. Email from {from_email}: \"{subject}\" — {body[:200]}",
                priority=EscalationPriority(priority),
                site_id=site_id,
                load_id=load_id
            )
            db.add(escalation)
            db.commit()
            logger.warning(f"[KnowledgeGraph] Non-ETA email escalated: {desc} (from {from_email})")

            return {"escalated": True, "issue_type": issue_type, "priority": priority}

        return {"escalated": False}

    except Exception as e:
        logger.error(f"[KnowledgeGraph] Error processing unparseable email: {e}")
        db.rollback()
        return {"escalated": False, "error": str(e)}
    finally:
        db.close()


def get_carrier_intelligence(carrier_id: int) -> Optional[Dict[str, Any]]:
    """Get carrier intelligence summary for Tier 2 context."""
    db = SessionLocal()
    try:
        cs = db.query(CarrierStats).filter(CarrierStats.carrier_id == carrier_id).first()
        carrier = db.query(Carrier).filter(Carrier.id == carrier_id).first()
        if not cs or not carrier:
            return None

        return {
            "carrier_name": carrier.carrier_name,
            "reliability_score": cs.reliability_score,
            "flagged_unreliable": cs.flagged_unreliable,
            "total_deliveries": cs.total_deliveries,
            "late_rate": round(cs.late_deliveries / max(cs.total_deliveries, 1), 2),
            "avg_delay_hours": round(cs.avg_delay_hours, 1),
            "avg_response_time_hours": round(cs.avg_response_time_hours, 1) if cs.avg_response_time_hours else None,
            "recent_deliveries": cs.recent_deliveries or [],
        }
    finally:
        db.close()


def get_site_intelligence(site_id: int) -> Optional[Dict[str, Any]]:
    """Get site intelligence summary for Tier 2 context."""
    db = SessionLocal()
    try:
        ss = db.query(SiteStats).filter(SiteStats.site_id == site_id).first()
        site = db.query(Site).filter(Site.id == site_id).first()
        if not ss or not site:
            return None

        return {
            "site_code": site.consignee_code,
            "risk_score": ss.risk_score,
            "false_alarm_rate": ss.false_alarm_rate,
            "total_escalations": ss.total_escalations,
            "total_deliveries": ss.total_deliveries_received,
            "avg_daily_consumption": ss.avg_daily_consumption,
            "recent_events": ss.recent_events or [],
        }
    finally:
        db.close()


def rebuild_knowledge_graph() -> Dict[str, Any]:
    """
    Rebuild all carrier and site stats from existing data.
    Useful when KG hooks were added after data already existed.
    """
    db = SessionLocal()
    try:
        carriers_updated = 0
        sites_updated = 0

        # ── Rebuild carrier stats from delivered loads ──
        from sqlalchemy import func
        carriers = db.query(Carrier).all()
        for carrier in carriers:
            delivered = db.query(Load).filter(
                Load.carrier_id == carrier.id,
                Load.status == LoadStatus.DELIVERED
            ).all()
            if not delivered:
                continue

            cs = _ensure_carrier_stats(db, carrier.id)
            cs.total_deliveries = len(delivered)
            cs.late_deliveries = 0
            cs.on_time_deliveries = 0
            cs.avg_delay_hours = 0.0
            cs.worst_delay_hours = 0.0
            total_delay = 0.0
            recent = []

            for load in delivered:
                was_late = False
                delay_hours = 0.0
                if load.current_eta and load.updated_at and load.updated_at > load.current_eta:
                    was_late = True
                    delay_hours = (load.updated_at - load.current_eta).total_seconds() / 3600
                    cs.late_deliveries += 1
                    total_delay += delay_hours
                    cs.worst_delay_hours = max(cs.worst_delay_hours, delay_hours)
                else:
                    cs.on_time_deliveries += 1

                recent.append({
                    "on_time": not was_late,
                    "delay_hours": round(delay_hours, 1),
                    "date": (load.updated_at or load.created_at).isoformat() if (load.updated_at or load.created_at) else None,
                    "load_id": load.id,
                    "po_number": load.po_number
                })

            cs.recent_deliveries = recent[-10:]
            if cs.late_deliveries > 0:
                cs.avg_delay_hours = total_delay / cs.late_deliveries
            cs.reliability_score = _compute_reliability_score(cs)
            cs.flagged_unreliable = cs.reliability_score < 0.4
            carriers_updated += 1

        # ── Rebuild site stats from escalations ──
        all_sites = db.query(Site).all()
        for site in all_sites:
            escalations = db.query(Escalation).filter(
                Escalation.site_id == site.id,
                Escalation.status == EscalationStatus.RESOLVED
            ).all()

            delivered_to_site = db.query(Load).filter(
                Load.destination_site_id == site.id,
                Load.status == LoadStatus.DELIVERED
            ).count()

            if not escalations and delivered_to_site == 0:
                continue

            ss = _ensure_site_stats(db, site.id)
            ss.total_escalations = len(escalations)
            ss.total_deliveries_received = delivered_to_site

            # Count false alarms from resolution notes
            false_alarms = 0
            events = []
            for esc in escalations:
                notes = (esc.resolution_notes or '').lower()
                is_false = any(kw in notes for kw in ['false alarm', 'resolved itself', 'no action needed', 'not needed'])
                if is_false:
                    false_alarms += 1
                events.append({
                    "type": "escalation_resolved",
                    "date": (esc.resolved_at or esc.updated_at or esc.created_at).isoformat() if (esc.resolved_at or esc.updated_at or esc.created_at) else None,
                    "details": f"{'False alarm' if is_false else 'Real issue'}: {esc.description[:80]}",
                    "priority": esc.priority.value if esc.priority else "medium"
                })

            ss.false_alarm_count = false_alarms
            ss.false_alarm_rate = round(false_alarms / len(escalations), 3) if escalations else 0.0
            if ss.total_escalations > 0:
                real_rate = (ss.total_escalations - ss.false_alarm_count) / max(ss.total_deliveries_received, 1)
                ss.risk_score = round(min(1.0, real_rate), 3)
            ss.recent_events = events[-10:]
            sites_updated += 1

        db.commit()
        logger.info(f"[KnowledgeGraph] Rebuilt: {carriers_updated} carriers, {sites_updated} sites")
        return {
            "carriers_updated": carriers_updated,
            "sites_updated": sites_updated,
        }
    except Exception as e:
        logger.error(f"[KnowledgeGraph] Rebuild failed: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


def generate_status_summary() -> str:
    """
    Generate a short executive status summary from current data + knowledge graph.
    Pure template — zero LLM tokens.
    """
    db = SessionLocal()
    try:
        from app.models import AIAgent, AgentStatus

        # Current state
        total_sites = db.query(Site).count()
        at_risk = db.query(Site).filter(
            Site.hours_to_runout.isnot(None),
            Site.hours_to_runout <= Site.runout_threshold_hours
        ).count()
        critical = db.query(Site).filter(
            Site.hours_to_runout.isnot(None),
            Site.hours_to_runout <= 12
        ).count()

        active_loads = db.query(Load).filter(
            Load.status.in_([LoadStatus.SCHEDULED, LoadStatus.IN_TRANSIT])
        ).count()
        delayed_loads = db.query(Load).filter(
            Load.status == LoadStatus.DELAYED
        ).count()

        open_esc = db.query(Escalation).filter(
            Escalation.status != EscalationStatus.RESOLVED
        ).count()
        critical_esc = db.query(Escalation).filter(
            Escalation.status != EscalationStatus.RESOLVED,
            Escalation.priority == EscalationPriority.CRITICAL
        ).count()

        active_agents = db.query(AIAgent).filter(AIAgent.status == AgentStatus.ACTIVE).count()

        # Knowledge graph highlights
        unreliable_carriers = db.query(CarrierStats).filter(CarrierStats.flagged_unreliable == True).all()
        high_risk_sites = db.query(SiteStats).filter(SiteStats.risk_score >= 0.7).all()

        # Build summary
        now = datetime.utcnow().strftime("%b %d, %H:%M UTC")
        lines = [f"Status Update — {now}"]
        lines.append("")

        # Overall health
        if critical == 0 and delayed_loads == 0 and critical_esc == 0:
            lines.append("All systems nominal. No critical issues detected.")
        elif critical > 0:
            lines.append(f"ALERT: {critical} site(s) within 12h of runout.")
        elif at_risk > 0:
            lines.append(f"Monitoring {at_risk} site(s) approaching runout thresholds.")

        lines.append(f"{total_sites} sites monitored, {active_loads} active loads, {active_agents} agent(s) running.")

        if delayed_loads > 0:
            lines.append(f"{delayed_loads} load(s) currently delayed — ETA requests sent.")

        if open_esc > 0:
            esc_detail = f"{open_esc} open escalation(s)"
            if critical_esc > 0:
                esc_detail += f" ({critical_esc} critical)"
            lines.append(f"{esc_detail} awaiting resolution.")

        # Knowledge graph insights
        if unreliable_carriers:
            names = [db.query(Carrier).filter(Carrier.id == cs.carrier_id).first()
                     for cs in unreliable_carriers]
            carrier_names = [c.carrier_name for c in names if c]
            if carrier_names:
                lines.append(f"Carrier watch: {', '.join(carrier_names)} flagged for low reliability.")

        if high_risk_sites:
            site_codes = []
            for ss in high_risk_sites:
                site = db.query(Site).filter(Site.id == ss.site_id).first()
                if site:
                    site_codes.append(site.consignee_code)
            if site_codes:
                lines.append(f"High-risk sites (escalation history): {', '.join(site_codes)}.")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"[KnowledgeGraph] Status summary failed: {e}")
        return f"Status update unavailable: {str(e)}"
    finally:
        db.close()


def generate_knowledge_graph_summary() -> str:
    """
    Generate a comprehensive narrative summary covering every carrier and site
    in the knowledge graph. Pure template — zero LLM tokens.
    """
    db = SessionLocal()
    try:
        carriers = db.query(CarrierStats).all()
        sites = db.query(SiteStats).all()

        now = datetime.utcnow().strftime("%b %d, %Y %H:%M UTC")
        lines = [f"# Knowledge Graph Intelligence Report", f"Generated: {now}", ""]

        # ── Overview ──
        total_carriers = len(carriers)
        total_sites = len(sites)
        flagged_count = sum(1 for c in carriers if c.flagged_unreliable)
        high_risk_count = sum(1 for s in sites if s.risk_score >= 0.7)
        total_deliveries = sum(c.total_deliveries for c in carriers)
        total_late = sum(c.late_deliveries for c in carriers)
        overall_on_time = ((total_deliveries - total_late) / max(total_deliveries, 1)) * 100

        lines.append("## Overview")
        lines.append(f"Tracking {total_carriers} carrier(s) and {total_sites} site(s).")
        lines.append(f"Total deliveries recorded: {total_deliveries} ({overall_on_time:.1f}% on-time fleet-wide).")
        if flagged_count > 0:
            lines.append(f"{flagged_count} carrier(s) flagged as unreliable.")
        if high_risk_count > 0:
            lines.append(f"{high_risk_count} site(s) classified as high risk.")
        if flagged_count == 0 and high_risk_count == 0:
            lines.append("No carriers flagged and no high-risk sites detected.")
        lines.append("")

        # ── Carrier Profiles ──
        lines.append("## Carrier Reliability Profiles")
        if not carriers:
            lines.append("No carrier data available.")
        else:
            sorted_carriers = sorted(carriers, key=lambda c: c.reliability_score)
            for cs in sorted_carriers:
                carrier = db.query(Carrier).filter(Carrier.id == cs.carrier_id).first()
                if not carrier:
                    continue
                name = carrier.carrier_name
                score_pct = f"{cs.reliability_score * 100:.0f}%"

                if cs.reliability_score >= 0.7:
                    rating = "Reliable"
                elif cs.reliability_score >= 0.4:
                    rating = "At Risk"
                else:
                    rating = "Unreliable"

                on_time_rate = (cs.on_time_deliveries / max(cs.total_deliveries, 1)) * 100

                lines.append(f"### {name} — {rating} ({score_pct})")
                lines.append(f"- {cs.total_deliveries} deliveries: {cs.on_time_deliveries} on-time, {cs.late_deliveries} late ({on_time_rate:.1f}% on-time rate)")

                if cs.avg_delay_hours > 0:
                    lines.append(f"- When late, average delay: {cs.avg_delay_hours:.1f}h (worst: {cs.worst_delay_hours:.1f}h)")

                if cs.total_eta_requests > 0:
                    resp_rate = (cs.eta_responses_received / cs.total_eta_requests) * 100
                    resp_time = f", avg response time {cs.avg_response_time_hours:.1f}h" if cs.avg_response_time_hours else ""
                    lines.append(f"- ETA responsiveness: {cs.eta_responses_received}/{cs.total_eta_requests} requests answered ({resp_rate:.0f}%{resp_time})")

                recent = cs.recent_deliveries or []
                if recent:
                    recent_on_time = sum(1 for d in recent if d.get("on_time"))
                    recent_total = len(recent)
                    trend_dir = "improving" if recent_on_time >= recent_total * 0.7 else (
                        "declining" if recent_on_time < recent_total * 0.4 else "mixed"
                    )
                    lines.append(f"- Recent trend ({recent_total} deliveries): {recent_on_time} on-time — {trend_dir}")

                if cs.primary_dispatcher:
                    lines.append(f"- Primary contact: {cs.primary_dispatcher} (prefers {cs.communication_preference or 'email'})")
                if cs.behavioral_notes:
                    lines.append(f"- Notes: {cs.behavioral_notes}")

                if cs.flagged_unreliable:
                    lines.append(f"- **FLAGGED**: Unreliable performance — receives Tier 2 scrutiny.")
                lines.append("")

        # ── Site Profiles ──
        lines.append("## Site Risk Profiles")
        if not sites:
            lines.append("No site data available.")
        else:
            sorted_sites = sorted(sites, key=lambda s: s.risk_score, reverse=True)
            for ss in sorted_sites:
                site = db.query(Site).filter(Site.id == ss.site_id).first()
                if not site:
                    continue
                code = site.consignee_code
                name = site.consignee_name or ""
                risk_pct = f"{ss.risk_score * 100:.0f}%"

                if ss.risk_score >= 0.7:
                    risk_label = "High Risk"
                elif ss.risk_score >= 0.4:
                    risk_label = "Medium Risk"
                else:
                    risk_label = "Low Risk"

                lines.append(f"### {code} ({name}) — {risk_label} ({risk_pct})")
                lines.append(f"- {ss.total_deliveries_received} deliveries received")

                if ss.total_escalations > 0:
                    real_count = ss.total_escalations - ss.false_alarm_count
                    lines.append(f"- {ss.total_escalations} escalation(s): {real_count} real issues, {ss.false_alarm_count} false alarms ({ss.false_alarm_rate * 100:.0f}% false alarm rate)")

                if ss.avg_daily_consumption:
                    lines.append(f"- Average daily consumption: {ss.avg_daily_consumption:.0f} gal/day")

                recent_events = ss.recent_events or []
                if recent_events:
                    delivery_events = [e for e in recent_events if e.get("type") == "delivery"]
                    esc_events = [e for e in recent_events if e.get("type") == "escalation_resolved"]
                    parts = []
                    if delivery_events:
                        parts.append(f"{len(delivery_events)} recent deliveries")
                    if esc_events:
                        parts.append(f"{len(esc_events)} resolved escalations")
                    if parts:
                        lines.append(f"- Recent activity: {', '.join(parts)}")

                if ss.primary_contact:
                    lines.append(f"- Primary contact: {ss.primary_contact}")
                if ss.access_notes:
                    lines.append(f"- Access: {ss.access_notes}")
                if ss.operational_notes:
                    lines.append(f"- Notes: {ss.operational_notes}")

                if ss.risk_score >= 0.7:
                    lines.append(f"- **HIGH RISK**: Elevated escalation history. Warrants close monitoring.")
                lines.append("")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"[KnowledgeGraph] Full summary failed: {e}")
        return f"Knowledge graph summary unavailable: {str(e)}"
    finally:
        db.close()


def get_all_intelligence() -> Dict[str, Any]:
    """Get full knowledge graph summary for the UI."""
    db = SessionLocal()
    try:
        carriers = db.query(CarrierStats).all()
        sites = db.query(SiteStats).all()

        carrier_data = []
        for cs in carriers:
            carrier = db.query(Carrier).filter(Carrier.id == cs.carrier_id).first()
            if carrier:
                carrier_data.append({
                    "carrier_id": cs.carrier_id,
                    "carrier_name": carrier.carrier_name,
                    "reliability_score": cs.reliability_score,
                    "flagged_unreliable": cs.flagged_unreliable,
                    "total_deliveries": cs.total_deliveries,
                    "late_deliveries": cs.late_deliveries,
                    "on_time_deliveries": cs.on_time_deliveries,
                    "avg_delay_hours": round(cs.avg_delay_hours, 1),
                    "total_eta_requests": cs.total_eta_requests,
                    "eta_responses_received": cs.eta_responses_received,
                    "avg_response_time_hours": round(cs.avg_response_time_hours, 1) if cs.avg_response_time_hours else None,
                    "recent_deliveries": cs.recent_deliveries or [],
                    "primary_dispatcher": cs.primary_dispatcher,
                    "communication_preference": cs.communication_preference,
                    "behavioral_notes": cs.behavioral_notes,
                })

        site_data = []
        for ss in sites:
            site = db.query(Site).filter(Site.id == ss.site_id).first()
            if site:
                site_data.append({
                    "site_id": ss.site_id,
                    "site_code": site.consignee_code,
                    "site_name": site.consignee_name,
                    "risk_score": ss.risk_score,
                    "false_alarm_rate": ss.false_alarm_rate,
                    "total_escalations": ss.total_escalations,
                    "false_alarm_count": ss.false_alarm_count,
                    "total_deliveries": ss.total_deliveries_received,
                    "avg_daily_consumption": ss.avg_daily_consumption,
                    "recent_events": ss.recent_events or [],
                    "primary_contact": ss.primary_contact,
                    "access_notes": ss.access_notes,
                    "operational_notes": ss.operational_notes,
                })

        return {
            "carriers": carrier_data,
            "sites": site_data,
            "last_updated": datetime.utcnow().isoformat()
        }
    finally:
        db.close()
