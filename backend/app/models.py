from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Enum, JSON, ARRAY
)
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class LoadStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class AgentStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


class AgentExecutionMode(str, enum.Enum):
    """
    Agent execution modes for graduated autonomy.

    DRAFT_ONLY: Agent analyzes and creates draft actions but doesn't execute (safest)
    AUTO_EMAIL: Agent can send emails automatically but requires approval for escalations
    FULL_AUTO: Agent can send emails and create escalations automatically (highest autonomy)
    """
    DRAFT_ONLY = "draft_only"
    AUTO_EMAIL = "auto_email"
    FULL_AUTO = "full_auto"


class EscalationPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class IssueType(str, enum.Enum):
    RUNOUT_RISK = "runout_risk"
    TERMINAL_OUT_OF_STOCK = "terminal_out_of_stock"
    SITE_CLOSED = "site_closed"
    DRIVER_ISSUE = "driver_issue"
    DELAYED_SHIPMENT = "delayed_shipment"
    NO_CARRIER_RESPONSE = "no_carrier_response"
    OTHER = "other"


class ActivityType(str, enum.Enum):
    EMAIL_SENT = "email_sent"
    DASHBOARD_UPDATED = "dashboard_updated"
    ESCALATION_CREATED = "escalation_created"
    INVENTORY_CHECKED = "inventory_checked"
    LOAD_STATUS_UPDATED = "load_status_updated"
    ETA_UPDATED = "eta_updated"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"


class Customer(str, enum.Enum):
    STARK_INDUSTRIES = "stark_industries"
    WAYNE_ENTERPRISES = "wayne_enterprises"
    LUTHOR_CORP = "luthor_corp"


class ERPSource(str, enum.Enum):
    FUEL_SHEPHERD = "fuel_shepherd"
    FUELQUEST = "fuelquest"
    MANUAL = "manual"


class ServiceType(str, enum.Enum):
    INVENTORY_AND_TRACKING = "inventory_and_tracking"
    TRACKING_ONLY = "tracking_only"


class Site(Base):
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    consignee_code = Column(String(50), unique=True, index=True)
    consignee_name = Column(String(255), nullable=False)
    address = Column(Text)
    tank_capacity = Column(Float)
    current_inventory = Column(Float, default=0)
    consumption_rate = Column(Float, nullable=True)  # gallons per hour
    hours_to_runout = Column(Float)
    runout_threshold_hours = Column(Float, default=48.0)
    min_delivery_quantity = Column(Float, nullable=True)  # minimum gallons per delivery
    notes = Column(Text, nullable=True)  # Coordinator notes about the site
    customer = Column(Enum(Customer), nullable=True)  # Which customer owns this site
    erp_source = Column(Enum(ERPSource), nullable=True)  # Which ERP system data came from
    service_type = Column(Enum(ServiceType), default=ServiceType.TRACKING_ONLY)  # Service level
    assigned_agent_id = Column(Integer, ForeignKey("ai_agents.id"), nullable=True)

    # Staleness tracking
    last_inventory_update_at = Column(DateTime, nullable=True)
    inventory_staleness_threshold_hours = Column(Integer, default=2)  # Alert if no update

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assigned_agent = relationship("AIAgent", back_populates="assigned_sites")
    lanes = relationship("Lane", back_populates="site")
    loads = relationship("Load", back_populates="destination_site")
    escalations = relationship("Escalation", back_populates="site")

    @property
    def is_inventory_stale(self):
        """Check if inventory data is stale based on threshold."""
        if not self.last_inventory_update_at:
            return True
        staleness = datetime.utcnow() - self.last_inventory_update_at
        return staleness.total_seconds() / 3600 > self.inventory_staleness_threshold_hours

    @property
    def inventory_staleness_hours(self):
        """Get how many hours since last inventory update."""
        if not self.last_inventory_update_at:
            return None
        staleness = datetime.utcnow() - self.last_inventory_update_at
        return staleness.total_seconds() / 3600


class Carrier(Base):
    __tablename__ = "carriers"

    id = Column(Integer, primary_key=True, index=True)
    carrier_name = Column(String(255), nullable=False)
    dispatcher_email = Column(String(255))
    dispatcher_phone = Column(String(50))
    response_time_sla_hours = Column(Integer, default=4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lanes = relationship("Lane", back_populates="carrier")
    loads = relationship("Load", back_populates="carrier")
    email_logs = relationship("EmailLog", back_populates="carrier")


class Lane(Base):
    __tablename__ = "lanes"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    carrier_id = Column(Integer, ForeignKey("carriers.id"), nullable=False)
    origin_terminal = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    site = relationship("Site", back_populates="lanes")
    carrier = relationship("Carrier", back_populates="lanes")
    loads = relationship("Load", back_populates="lane")


class Load(Base):
    __tablename__ = "loads"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(100), unique=True, index=True)
    tms_load_number = Column(String(100), index=True)
    lane_id = Column(Integer, ForeignKey("lanes.id"), nullable=True)
    carrier_id = Column(Integer, ForeignKey("carriers.id"), nullable=False)
    destination_site_id = Column(Integer, ForeignKey("sites.id"), nullable=False)
    origin_terminal = Column(String(255))
    product_type = Column(String(50))  # gas, diesel, etc.
    volume = Column(Float)
    status = Column(Enum(LoadStatus), default=LoadStatus.SCHEDULED)
    current_eta = Column(DateTime, nullable=True)
    last_eta_update = Column(DateTime, nullable=True)
    has_macropoint_tracking = Column(Boolean, default=False)
    driver_name = Column(String(255), nullable=True)
    driver_phone = Column(String(50), nullable=True)
    last_email_sent = Column(DateTime, nullable=True)

    # Staleness tracking
    last_eta_update_at = Column(DateTime, nullable=True)
    eta_staleness_threshold_hours = Column(Integer, default=4)  # Alert if ETA unchanged

    # Collaborative notes (JSON array of note objects)
    notes = Column(JSON, default=list)  # [{"author": "Agent 1", "type": "ai", "text": "...", "timestamp": "..."}]

    # GPS tracking data (JSON array of tracking points)
    tracking_points = Column(JSON, default=list)  # [{"lat": 33.7, "lng": -84.4, "timestamp": "...", "speed": 65}]
    origin_address = Column(String(500), nullable=True)
    destination_address = Column(String(500), nullable=True)
    shipped_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    lane = relationship("Lane", back_populates="loads")
    carrier = relationship("Carrier", back_populates="loads")
    destination_site = relationship("Site", back_populates="loads")
    activities = relationship("Activity", back_populates="load")
    escalations = relationship("Escalation", back_populates="load")
    email_logs = relationship("EmailLog", back_populates="load")

    @property
    def is_eta_stale(self):
        """Check if ETA data is stale based on threshold."""
        if not self.last_eta_update_at:
            return True
        staleness = datetime.utcnow() - self.last_eta_update_at
        return staleness.total_seconds() / 3600 > self.eta_staleness_threshold_hours

    @property
    def eta_staleness_hours(self):
        """Get how many hours since last ETA update."""
        if not self.last_eta_update_at:
            return None
        staleness = datetime.utcnow() - self.last_eta_update_at
        return staleness.total_seconds() / 3600


class AIAgent(Base):
    __tablename__ = "ai_agents"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String(255), nullable=False)
    persona_type = Column(String(100), default="coordinator")  # coordinator, monitor, etc.
    status = Column(Enum(AgentStatus), default=AgentStatus.STOPPED)
    execution_mode = Column(Enum(AgentExecutionMode), default=AgentExecutionMode.DRAFT_ONLY, nullable=False)
    last_activity_at = Column(DateTime, nullable=True)
    check_interval_minutes = Column(Integer, default=15)
    configuration = Column(JSON, default=dict)

    # Time-aware / overnight configuration
    time_aware_escalation = Column(Boolean, default=True)  # Adjust urgency by time of day
    overnight_escalation_multiplier = Column(Float, default=1.5)  # More aggressive overnight
    overnight_start_hour = Column(Integer, default=22)  # 10 PM
    overnight_end_hour = Column(Integer, default=6)  # 6 AM
    coverage_hours = Column(String(255), nullable=True)  # e.g., "24/7", "business_hours", "overnight_only"

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assigned_sites = relationship("Site", back_populates="assigned_agent")
    activities = relationship("Activity", back_populates="agent")
    escalations = relationship("Escalation", back_populates="created_by_agent")
    sent_emails = relationship("EmailLog", foreign_keys="[EmailLog.sent_by_agent_id]", back_populates="sent_by_agent")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"), nullable=False)
    activity_type = Column(Enum(ActivityType), nullable=False)
    load_id = Column(Integer, ForeignKey("loads.id"), nullable=True)
    details = Column(JSON, default=dict)

    # Lightweight decision logging
    decision_code = Column(String(100), nullable=True)  # e.g., "STALE_ETA_LOW_INVENTORY"
    decision_metrics = Column(JSON, nullable=True)  # Key metrics that triggered this action
    reasoning_summary = Column(Text, nullable=True)  # Optional human-readable summary

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    agent = relationship("AIAgent", back_populates="activities")
    load = relationship("Load", back_populates="activities")


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, index=True)
    created_by_agent_id = Column(Integer, ForeignKey("ai_agents.id"), nullable=True)
    load_id = Column(Integer, ForeignKey("loads.id"), nullable=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=True)
    priority = Column(Enum(EscalationPriority), default=EscalationPriority.MEDIUM)
    issue_type = Column(Enum(IssueType), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(EscalationStatus), default=EscalationStatus.OPEN)
    assigned_to = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_by_agent = relationship("AIAgent", back_populates="escalations")
    load = relationship("Load", back_populates="escalations")
    site = relationship("Site", back_populates="escalations")


class UploadAuditLog(Base):
    __tablename__ = "upload_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    customer = Column(Enum(Customer), nullable=False)
    erp_source = Column(Enum(ERPSource), nullable=False)
    uploaded_by = Column(String(255), default="coordinator")  # User who uploaded
    filename = Column(String(255), nullable=True)
    records_processed = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_details = Column(JSON, nullable=True)  # List of errors if any
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.OPERATOR, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)


class EmailDeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    FAILED = "failed"
    COMPLAINED = "complained"  # Recipient marked as spam


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    recipient = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    template_id = Column(String(100), nullable=True)  # For template-based emails
    status = Column(Enum(EmailDeliveryStatus), default=EmailDeliveryStatus.PENDING, nullable=False)

    # Tracking IDs
    message_id = Column(String(255), nullable=True, index=True)  # SendGrid message ID
    load_id = Column(Integer, ForeignKey("loads.id"), nullable=True)  # Related load if applicable
    carrier_id = Column(Integer, ForeignKey("carriers.id"), nullable=True)  # Related carrier
    sent_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # User who triggered email
    sent_by_agent_id = Column(Integer, ForeignKey("ai_agents.id"), nullable=True)  # Agent who sent email

    # Delivery tracking
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    bounced_at = Column(DateTime, nullable=True)
    bounce_reason = Column(Text, nullable=True)
    complaint_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    load = relationship("Load", back_populates="email_logs")
    carrier = relationship("Carrier", back_populates="email_logs")
    sent_by_user = relationship("User", foreign_keys=[sent_by_user_id])
    sent_by_agent = relationship("AIAgent", foreign_keys=[sent_by_agent_id])


class AgentRunStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AgentRunHistory(Base):
    """
    Tracks each execution of an AI agent for observability and debugging.

    Records what the agent analyzed, what decisions it made, and outcomes.
    """
    __tablename__ = "agent_run_history"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"), nullable=False, index=True)

    # Run timing
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Run status
    status = Column(Enum(AgentRunStatus), default=AgentRunStatus.RUNNING, nullable=False)
    error_message = Column(Text, nullable=True)

    # Execution mode at time of run
    execution_mode = Column(Enum(AgentExecutionMode), nullable=False)

    # What the agent analyzed
    sites_checked = Column(Integer, default=0)
    loads_checked = Column(Integer, default=0)

    # Actions taken (or would-be taken in DRAFT_ONLY mode)
    emails_sent = Column(Integer, default=0)
    escalations_created = Column(Integer, default=0)
    draft_actions = Column(Integer, default=0)  # Actions blocked by execution mode

    # Decision summary (lightweight JSON)
    decisions = Column(JSON, default=list)  # List of decision codes/summaries

    # Claude API usage (for cost tracking)
    api_calls = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)

    # Relationships
    agent = relationship("AIAgent", backref="run_history")
