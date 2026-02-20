"""
Coordinator Agent - AI agent that monitors fuel sites and manages logistics.
Uses Claude API for decision-making with tool-based actions.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    Site, Load, Carrier, AIAgent, Activity, Escalation, AgentRunHistory,
    LoadStatus, AgentStatus, ActivityType, IssueType, EscalationPriority,
    AgentExecutionMode, AgentRunStatus
)
from app.integrations.claude_service import claude_service
from app.services.email_service import send_eta_request

logger = logging.getLogger(__name__)


# Tool definitions for Claude
AGENT_TOOLS = [
    {
        "name": "check_site_inventory",
        "description": "Check the current inventory status of a specific site, including hours to runout and active loads.",
        "input_schema": {
            "type": "object",
            "properties": {
                "site_id": {
                    "type": "integer",
                    "description": "The ID of the site to check"
                }
            },
            "required": ["site_id"]
        }
    },
    {
        "name": "get_load_details",
        "description": "Get detailed information about a specific load/shipment, including carrier info and ETA.",
        "input_schema": {
            "type": "object",
            "properties": {
                "load_id": {
                    "type": "integer",
                    "description": "The ID of the load to check"
                }
            },
            "required": ["load_id"]
        }
    },
    {
        "name": "send_eta_request_email",
        "description": "Send an email to the carrier dispatcher requesting an updated ETA for a load.",
        "input_schema": {
            "type": "object",
            "properties": {
                "load_id": {
                    "type": "integer",
                    "description": "The ID of the load to request ETA for"
                },
                "urgency_note": {
                    "type": "string",
                    "description": "Optional note about why this is urgent"
                }
            },
            "required": ["load_id"]
        }
    },
    {
        "name": "create_escalation",
        "description": "Create an escalation for the human supervisor to review. Use this when there's a problem you cannot resolve.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_type": {
                    "type": "string",
                    "enum": ["runout_risk", "terminal_out_of_stock", "site_closed", "driver_issue", "delayed_shipment", "no_carrier_response", "other"],
                    "description": "The type of issue"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the issue"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Priority level based on urgency"
                },
                "site_id": {
                    "type": "integer",
                    "description": "Related site ID (optional)"
                },
                "load_id": {
                    "type": "integer",
                    "description": "Related load ID (optional)"
                }
            },
            "required": ["issue_type", "description", "priority"]
        }
    },
    {
        "name": "log_observation",
        "description": "Log an observation or note about the current situation. Use this to record your reasoning.",
        "input_schema": {
            "type": "object",
            "properties": {
                "observation": {
                    "type": "string",
                    "description": "Your observation or reasoning"
                }
            },
            "required": ["observation"]
        }
    },
    {
        "name": "complete_check",
        "description": "Signal that you have completed checking all sites and loads. Call this when done.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Brief summary of actions taken during this check cycle"
                }
            },
            "required": ["summary"]
        }
    }
]

SYSTEM_PROMPT = """You are an AI fuels logistics coordinator assistant. Your job is to monitor fuel inventory at gas stations and track shipments to ensure sites don't run out of fuel.

## Your Responsibilities:
1. Monitor assigned sites for low inventory (sites with hours_to_runout below their threshold are at risk)
2. Check active loads/shipments heading to at-risk sites
3. Request ETA updates from carriers when needed (if no update in 4+ hours)
4. Escalate issues to your human supervisor when you cannot resolve them

## Decision Guidelines:
- If a site has < 24 hours to runout with no confirmed ETA: Create HIGH priority escalation
- If a site has < 12 hours to runout: Create CRITICAL priority escalation
- If a load hasn't had an ETA update in 4+ hours: Send ETA request email
- If a site has < 48 hours and a load is DELAYED: Create escalation
- Always log your reasoning before taking actions

## Important Rules:
- Be proactive but not excessive - don't spam carriers with emails
- When in doubt, escalate to your human supervisor
- Always call complete_check when you're done reviewing all sites

You will be given the current state of sites and loads. Analyze them and take appropriate actions using your tools."""


class CoordinatorAgent:
    """AI Coordinator Agent that monitors sites and manages logistics."""

    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        self.db: Optional[Session] = None
        self.actions_taken = []

    def _get_db(self) -> Session:
        """Get or create database session."""
        if self.db is None:
            self.db = SessionLocal()
        return self.db

    def _close_db(self):
        """Close database session."""
        if self.db:
            self.db.close()
            self.db = None

    def _get_agent(self) -> Optional[AIAgent]:
        """Get the agent record from database."""
        db = self._get_db()
        return db.query(AIAgent).filter(AIAgent.id == self.agent_id).first()

    def _log_activity(self, activity_type: ActivityType, details: dict, load_id: int = None):
        """Log an activity to the database."""
        db = self._get_db()
        activity = Activity(
            agent_id=self.agent_id,
            activity_type=activity_type,
            load_id=load_id,
            details=details
        )
        db.add(activity)
        db.commit()
        self.actions_taken.append({
            "type": activity_type.value,
            "details": details
        })

    def _build_context(self) -> str:
        """Build the current state context for the agent."""
        db = self._get_db()
        agent = self._get_agent()

        if not agent:
            return "Error: Agent not found"

        # Get assigned sites
        sites = db.query(Site).filter(Site.assigned_agent_id == self.agent_id).all()

        if not sites:
            return "No sites assigned to this agent."

        context_parts = ["## Current State\n"]

        # Sites summary
        context_parts.append("### Assigned Sites:")
        for site in sites:
            status = "OK"
            if site.hours_to_runout:
                if site.hours_to_runout < 12:
                    status = "CRITICAL"
                elif site.hours_to_runout < 24:
                    status = "HIGH RISK"
                elif site.hours_to_runout < site.runout_threshold_hours:
                    status = "AT RISK"

            context_parts.append(
                f"- Site {site.id} ({site.consignee_code}): {site.consignee_name}\n"
                f"  Inventory: {site.current_inventory:.0f} gal | "
                f"Hours to runout: {site.hours_to_runout:.1f}h | "
                f"Threshold: {site.runout_threshold_hours}h | "
                f"Status: {status}"
            )

        # Active loads for these sites
        site_ids = [s.id for s in sites]
        loads = db.query(Load).filter(
            Load.destination_site_id.in_(site_ids),
            Load.status.in_([LoadStatus.SCHEDULED, LoadStatus.IN_TRANSIT, LoadStatus.DELAYED])
        ).all()

        context_parts.append("\n### Active Loads:")
        if loads:
            for load in loads:
                carrier = db.query(Carrier).filter(Carrier.id == load.carrier_id).first()
                site = db.query(Site).filter(Site.id == load.destination_site_id).first()

                eta_info = "No ETA"
                if load.current_eta:
                    eta_info = f"ETA: {load.current_eta.strftime('%Y-%m-%d %H:%M')}"

                last_update = "Never"
                hours_since_update = None
                if load.last_eta_update:
                    hours_since_update = (datetime.utcnow() - load.last_eta_update).total_seconds() / 3600
                    last_update = f"{hours_since_update:.1f} hours ago"

                last_email = "Never"
                if load.last_email_sent:
                    hours_since_email = (datetime.utcnow() - load.last_email_sent).total_seconds() / 3600
                    last_email = f"{hours_since_email:.1f} hours ago"

                context_parts.append(
                    f"- Load {load.id} (PO: {load.po_number})\n"
                    f"  Carrier: {carrier.carrier_name if carrier else 'Unknown'}\n"
                    f"  Destination: {site.consignee_name if site else 'Unknown'}\n"
                    f"  Status: {load.status.value} | {eta_info}\n"
                    f"  Last ETA update: {last_update} | Last email sent: {last_email}\n"
                    f"  Macropoint: {'Yes' if load.has_macropoint_tracking else 'No'}"
                )
        else:
            context_parts.append("No active loads for assigned sites.")

        return "\n".join(context_parts)

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool and return the result."""
        db = self._get_db()

        if tool_name == "check_site_inventory":
            site_id = tool_input["site_id"]
            site = db.query(Site).filter(Site.id == site_id).first()
            if not site:
                return f"Site {site_id} not found."

            loads = db.query(Load).filter(
                Load.destination_site_id == site_id,
                Load.status.in_([LoadStatus.SCHEDULED, LoadStatus.IN_TRANSIT])
            ).all()

            return json.dumps({
                "site_id": site.id,
                "code": site.consignee_code,
                "name": site.consignee_name,
                "current_inventory": site.current_inventory,
                "hours_to_runout": site.hours_to_runout,
                "threshold_hours": site.runout_threshold_hours,
                "active_loads_count": len(loads),
                "active_load_ids": [l.id for l in loads]
            })

        elif tool_name == "get_load_details":
            load_id = tool_input["load_id"]
            load = db.query(Load).filter(Load.id == load_id).first()
            if not load:
                return f"Load {load_id} not found."

            carrier = db.query(Carrier).filter(Carrier.id == load.carrier_id).first()
            site = db.query(Site).filter(Site.id == load.destination_site_id).first()

            return json.dumps({
                "load_id": load.id,
                "po_number": load.po_number,
                "status": load.status.value,
                "carrier_name": carrier.carrier_name if carrier else None,
                "carrier_email": carrier.dispatcher_email if carrier else None,
                "destination_site": site.consignee_name if site else None,
                "product_type": load.product_type,
                "volume": load.volume,
                "current_eta": load.current_eta.isoformat() if load.current_eta else None,
                "last_eta_update": load.last_eta_update.isoformat() if load.last_eta_update else None,
                "last_email_sent": load.last_email_sent.isoformat() if load.last_email_sent else None,
                "has_macropoint": load.has_macropoint_tracking,
                "driver_name": load.driver_name
            })

        elif tool_name == "send_eta_request_email":
            # Check execution mode
            agent = self._get_agent()
            if agent.execution_mode == AgentExecutionMode.DRAFT_ONLY:
                return (
                    f"[DRAFT MODE] Would send ETA request email for Load {tool_input['load_id']}. "
                    "Agent is in DRAFT_ONLY mode - no emails will be sent. "
                    "Upgrade to AUTO_EMAIL or FULL_AUTO to enable automatic email sending."
                )

            load_id = tool_input["load_id"]
            load = db.query(Load).filter(Load.id == load_id).first()
            if not load:
                return f"Load {load_id} not found."

            carrier = db.query(Carrier).filter(Carrier.id == load.carrier_id).first()
            site = db.query(Site).filter(Site.id == load.destination_site_id).first()

            if not carrier or not carrier.dispatcher_email:
                return "Cannot send email: No dispatcher email on file for carrier."

            # Send email via Resend HTTP API
            # This executes only in AUTO_EMAIL or FULL_AUTO mode
            email_log = send_eta_request(
                db=db,
                load=load,
                carrier=carrier,
                sent_by_agent_id=self.agent_id
            )

            # Update load
            load.last_email_sent = datetime.utcnow()
            db.commit()

            # Log activity
            self._log_activity(
                ActivityType.EMAIL_SENT,
                {
                    "to": carrier.dispatcher_email,
                    "po_number": load.po_number,
                    "carrier": carrier.carrier_name,
                    "email_log_id": email_log.id,
                    "status": email_log.status.value
                },
                load_id=load_id
            )

            if email_log.status.value == "sent":
                return f"Email sent successfully to {carrier.dispatcher_email} (Message ID: {email_log.message_id})"
            elif email_log.status.value == "failed":
                return f"Email failed to send to {carrier.dispatcher_email}: {email_log.bounce_reason}"
            else:
                return f"Email logged (Resend not configured) - would send to {carrier.dispatcher_email}"

        elif tool_name == "create_escalation":
            # Check execution mode
            agent = self._get_agent()
            issue_type = IssueType(tool_input["issue_type"])
            priority = EscalationPriority(tool_input["priority"])

            if agent.execution_mode == AgentExecutionMode.DRAFT_ONLY:
                return (
                    f"[DRAFT MODE] Would create {priority.value} escalation: {tool_input['description']}. "
                    "Agent is in DRAFT_ONLY mode - no escalations will be created automatically. "
                    "Upgrade to AUTO_EMAIL or FULL_AUTO to enable automatic escalations."
                )

            if agent.execution_mode == AgentExecutionMode.AUTO_EMAIL:
                return (
                    f"[AUTO_EMAIL MODE] Would create {priority.value} escalation: {tool_input['description']}. "
                    "Agent is in AUTO_EMAIL mode - escalations require manual approval. "
                    "Upgrade to FULL_AUTO to enable automatic escalation creation."
                )

            # Only execute in FULL_AUTO mode
            escalation = Escalation(
                created_by_agent_id=self.agent_id,
                issue_type=issue_type,
                description=tool_input["description"],
                priority=priority,
                site_id=tool_input.get("site_id"),
                load_id=tool_input.get("load_id")
            )
            db.add(escalation)
            db.commit()

            # Log activity
            self._log_activity(
                ActivityType.ESCALATION_CREATED,
                {
                    "issue_type": issue_type.value,
                    "priority": priority.value,
                    "description": tool_input["description"],
                    "escalation_id": escalation.id
                }
            )

            return f"Escalation created with ID {escalation.id} (Priority: {priority.value})"

        elif tool_name == "log_observation":
            logger.info(f"[Agent {self.agent_id}] Observation: {tool_input['observation']}")
            return "Observation logged."

        elif tool_name == "complete_check":
            logger.info(f"[Agent {self.agent_id}] Check completed: {tool_input['summary']}")
            return "Check cycle completed."

        else:
            return f"Unknown tool: {tool_name}"

    def run_check_cycle(self, override_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Run one check cycle - analyze all assigned sites and take actions.

        Args:
            override_context: If provided, use this instead of building full context.
                             Used by Tier 2 to pass only flagged situations.

        Returns:
            Summary of actions taken during this cycle
        """
        try:
            self.actions_taken = []

            # Build context (or use override for Tier 2)
            context = override_context or self._build_context()
            logger.info(f"[Agent {self.agent_id}] Starting check cycle {'(Tier 2)' if override_context else '(full)'}")
            logger.info(f"Context:\n{context}")

            # Initial message to Claude
            messages = [
                {"role": "user", "content": f"Please review the current state and take appropriate actions.\n\n{context}"}
            ]

            # Agentic loop - let Claude use tools until done
            max_iterations = 10
            iteration = 0
            completed = False

            while iteration < max_iterations and not completed:
                iteration += 1

                # Get Claude's response
                response = claude_service.chat(
                    messages=messages,
                    system_prompt=SYSTEM_PROMPT,
                    tools=AGENT_TOOLS
                )

                # Extract tool calls
                tool_calls = claude_service.extract_tool_calls(response)
                text_response = claude_service.extract_text(response)

                if text_response:
                    logger.info(f"[Agent {self.agent_id}] Claude: {text_response}")

                # If no tool calls, we're done
                if not tool_calls:
                    break

                # Process each tool call
                # Add assistant's response to messages
                messages.append({"role": "assistant", "content": response["content"]})

                tool_results = []
                for tool_call in tool_calls:
                    logger.info(f"[Agent {self.agent_id}] Executing tool: {tool_call['name']}")
                    result = self._execute_tool(tool_call["name"], tool_call["input"])
                    logger.info(f"[Agent {self.agent_id}] Tool result: {result}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call["id"],
                        "content": result
                    })

                    if tool_call["name"] == "complete_check":
                        completed = True

                # Add tool results to messages
                messages.append({"role": "user", "content": tool_results})

            # Update agent last activity
            db = self._get_db()
            agent = self._get_agent()
            if agent:
                agent.last_activity_at = datetime.utcnow()
                db.commit()

            return {
                "success": True,
                "iterations": iteration,
                "actions_taken": self.actions_taken,
                "completed": completed
            }

        except Exception as e:
            logger.error(f"[Agent {self.agent_id}] Error in check cycle: {e}")
            return {
                "success": False,
                "error": str(e),
                "actions_taken": self.actions_taken
            }

        finally:
            self._close_db()


def run_agent_check(agent_id: int) -> Dict[str, Any]:
    """
    Run a tiered check cycle for an agent, recording run history.

    Tier 1: Rules engine (zero tokens) handles threshold checks, template emails
    Tier 2: LLM agent (tokens) fires ONLY when Tier 1 flags ambiguous situations
    """
    from app.agents.rules_engine import run_rules_check, execute_tier1_actions
    from app.services.knowledge_graph import get_carrier_intelligence, get_site_intelligence

    db = SessionLocal()
    started_at = datetime.utcnow()

    try:
        # Get agent info for the run record
        db_agent = db.query(AIAgent).filter(AIAgent.id == agent_id).first()
        execution_mode = db_agent.execution_mode if db_agent else AgentExecutionMode.DRAFT_ONLY

        # Count sites and loads for this agent
        sites_count = db.query(Site).filter(Site.assigned_agent_id == agent_id).count()
        site_ids = [s.id for s in db.query(Site.id).filter(Site.assigned_agent_id == agent_id).all()]
        loads_count = db.query(Load).filter(
            Load.destination_site_id.in_(site_ids),
            Load.status.in_([LoadStatus.SCHEDULED, LoadStatus.IN_TRANSIT, LoadStatus.DELAYED])
        ).count() if site_ids else 0

        # Create run history record
        run_record = AgentRunHistory(
            agent_id=agent_id,
            started_at=started_at,
            status=AgentRunStatus.RUNNING,
            execution_mode=execution_mode,
            sites_checked=sites_count,
            loads_checked=loads_count,
        )
        db.add(run_record)
        db.commit()
        db.refresh(run_record)
        run_record_id = run_record.id
        db.close()

        all_actions = []
        api_calls = 0
        tier2_used = False

        # ── TIER 1: Rules Engine (zero tokens) ──
        logger.info(f"[Agent {agent_id}] Running Tier 1 rules engine...")
        rules_result = run_rules_check(agent_id)
        tier1_executed = execute_tier1_actions(agent_id, rules_result.actions)
        all_actions.extend(tier1_executed)

        # ── TIER 2: LLM Agent (only if Tier 1 flagged ambiguity) ──
        if rules_result.tier2_flags:
            logger.info(f"[Agent {agent_id}] Tier 1 flagged {len(rules_result.tier2_flags)} items for Tier 2 LLM review")
            tier2_used = True

            # Build enriched context with knowledge graph data
            tier2_context = "## Tier 2 Review — Situations requiring nuanced judgment\n\n"
            tier2_context += "The rules engine has already handled routine actions. "
            tier2_context += "Please review these flagged situations that may need your judgment:\n\n"

            for flag in rules_result.tier2_flags:
                tier2_context += f"### Flag: {flag['reason']}\n"
                for k, v in flag.get('details', {}).items():
                    tier2_context += f"- {k}: {v}\n"

                # Enrich with knowledge graph
                if 'carrier_id' in flag:
                    intel = get_carrier_intelligence(flag['carrier_id'])
                    if intel:
                        tier2_context += f"- **Carrier intelligence**: reliability={intel['reliability_score']}, "
                        tier2_context += f"late_rate={intel['late_rate']}, avg_delay={intel['avg_delay_hours']}h\n"
                if 'site_id' in flag:
                    intel = get_site_intelligence(flag['site_id'])
                    if intel:
                        tier2_context += f"- **Site intelligence**: risk={intel['risk_score']}, "
                        tier2_context += f"false_alarm_rate={intel['false_alarm_rate']}\n"
                tier2_context += "\n"

            try:
                agent = CoordinatorAgent(agent_id)
                # Override context to only include flagged items (not full site scan)
                tier2_result = agent.run_check_cycle(override_context=tier2_context)
                api_calls = tier2_result.get("iterations", 0)
                all_actions.extend(tier2_result.get("actions_taken", []))
            except Exception as e:
                logger.error(f"[Agent {agent_id}] Tier 2 failed (non-fatal): {e}")
        else:
            logger.info(f"[Agent {agent_id}] No Tier 2 flags — rules engine handled everything")

        # Update run record with results
        db = SessionLocal()
        run_record = db.query(AgentRunHistory).filter(AgentRunHistory.id == run_record_id).first()
        completed_at = datetime.utcnow()
        run_record.completed_at = completed_at
        run_record.duration_seconds = (completed_at - started_at).total_seconds()
        run_record.api_calls = api_calls

        run_record.status = AgentRunStatus.COMPLETED
        run_record.emails_sent = sum(1 for a in all_actions if a["type"] in ("email_sent", "email_drafted"))
        run_record.escalations_created = sum(1 for a in all_actions if a["type"] in ("escalation_created", "escalation_drafted"))
        run_record.decisions = [
            {
                "type": a["type"],
                "summary": str(a.get("details", {}).get("description", str(a.get("details", {}))))[:120],
                "tier": "tier2" if tier2_used and i >= len(tier1_executed) else "tier1"
            }
            for i, a in enumerate(all_actions)
        ]

        db.commit()
        db.close()

        return {
            "success": True,
            "iterations": api_calls,
            "actions_taken": all_actions,
            "tier1_actions": len(tier1_executed),
            "tier2_flags": len(rules_result.tier2_flags),
            "tier2_used": tier2_used,
            "summary": rules_result.summary
        }

    except Exception as e:
        # Mark as failed if something went wrong
        try:
            db = SessionLocal()
            run_record = db.query(AgentRunHistory).filter(
                AgentRunHistory.agent_id == agent_id,
                AgentRunHistory.started_at == started_at
            ).first()
            if run_record:
                run_record.status = AgentRunStatus.FAILED
                run_record.completed_at = datetime.utcnow()
                run_record.duration_seconds = (datetime.utcnow() - started_at).total_seconds()
                run_record.error_message = str(e)
                db.commit()
            db.close()
        except Exception:
            pass
        raise
