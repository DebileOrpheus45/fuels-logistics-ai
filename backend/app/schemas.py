from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.models import (
    LoadStatus, AgentStatus, EscalationPriority,
    EscalationStatus, IssueType, ActivityType,
    Customer, ERPSource, ServiceType
)


# ============== Site Schemas ==============

class SiteBase(BaseModel):
    consignee_code: str
    consignee_name: str
    address: Optional[str] = None
    tank_capacity: Optional[float] = None
    current_inventory: Optional[float] = 0
    consumption_rate: Optional[float] = None  # gallons per hour
    hours_to_runout: Optional[float] = None
    runout_threshold_hours: Optional[float] = 48.0
    min_delivery_quantity: Optional[float] = None
    notes: Optional[str] = None
    customer: Optional[Customer] = None
    erp_source: Optional[ERPSource] = None
    service_type: Optional[ServiceType] = ServiceType.TRACKING_ONLY


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    consignee_name: Optional[str] = None
    address: Optional[str] = None
    tank_capacity: Optional[float] = None
    current_inventory: Optional[float] = None
    consumption_rate: Optional[float] = None
    hours_to_runout: Optional[float] = None
    runout_threshold_hours: Optional[float] = None
    min_delivery_quantity: Optional[float] = None
    notes: Optional[str] = None
    customer: Optional[Customer] = None
    erp_source: Optional[ERPSource] = None
    service_type: Optional[ServiceType] = None
    assigned_agent_id: Optional[int] = None


class SiteConstraintsUpdate(BaseModel):
    """Schema for batch updating site constraints"""
    consignee_code: str  # Used to identify the site
    tank_capacity: Optional[float] = None
    consumption_rate: Optional[float] = None
    runout_threshold_hours: Optional[float] = None
    min_delivery_quantity: Optional[float] = None
    notes: Optional[str] = None
    service_type: Optional[ServiceType] = None


class SiteBatchUpdate(BaseModel):
    """Schema for batch updating multiple sites"""
    customer: Customer  # Which customer owns these sites
    erp_source: ERPSource  # Which ERP the data came from
    sites: List[SiteConstraintsUpdate]


class SiteResponse(SiteBase):
    id: int
    assigned_agent_id: Optional[int] = None
    customer: Optional[Customer] = None
    erp_source: Optional[ERPSource] = None
    service_type: Optional[ServiceType] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SiteWithLoads(SiteResponse):
    loads: List["LoadResponse"] = []


# ============== Carrier Schemas ==============

class CarrierBase(BaseModel):
    carrier_name: str
    dispatcher_email: Optional[str] = None
    dispatcher_phone: Optional[str] = None
    response_time_sla_hours: Optional[int] = 4


class CarrierCreate(CarrierBase):
    pass


class CarrierUpdate(BaseModel):
    carrier_name: Optional[str] = None
    dispatcher_email: Optional[str] = None
    dispatcher_phone: Optional[str] = None
    response_time_sla_hours: Optional[int] = None


class CarrierResponse(CarrierBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============== Lane Schemas ==============

class LaneBase(BaseModel):
    site_id: int
    carrier_id: int
    origin_terminal: Optional[str] = None
    is_active: Optional[bool] = True


class LaneCreate(LaneBase):
    pass


class LaneUpdate(BaseModel):
    origin_terminal: Optional[str] = None
    is_active: Optional[bool] = None


class LaneResponse(LaneBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============== Load Schemas ==============

class LoadBase(BaseModel):
    po_number: str
    tms_load_number: Optional[str] = None
    lane_id: Optional[int] = None
    carrier_id: int
    destination_site_id: int
    origin_terminal: Optional[str] = None
    product_type: Optional[str] = None
    volume: Optional[float] = None
    status: Optional[LoadStatus] = LoadStatus.SCHEDULED
    has_macropoint_tracking: Optional[bool] = False
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None


class LoadCreate(LoadBase):
    pass


class LoadUpdate(BaseModel):
    tms_load_number: Optional[str] = None
    status: Optional[LoadStatus] = None
    current_eta: Optional[datetime] = None
    has_macropoint_tracking: Optional[bool] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None


class LoadResponse(LoadBase):
    id: int
    current_eta: Optional[datetime] = None
    last_eta_update: Optional[datetime] = None
    last_email_sent: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoadWithDetails(LoadResponse):
    carrier: Optional[CarrierResponse] = None
    destination_site: Optional[SiteResponse] = None


# ============== AI Agent Schemas ==============

class AIAgentBase(BaseModel):
    agent_name: str
    persona_type: Optional[str] = "coordinator"
    check_interval_minutes: Optional[int] = 15
    configuration: Optional[Dict[str, Any]] = {}


class AIAgentCreate(AIAgentBase):
    pass


class AIAgentUpdate(BaseModel):
    agent_name: Optional[str] = None
    persona_type: Optional[str] = None
    status: Optional[AgentStatus] = None
    check_interval_minutes: Optional[int] = None
    configuration: Optional[Dict[str, Any]] = None


class AIAgentSiteAssignment(BaseModel):
    """Schema for assigning multiple sites to an agent"""
    site_ids: List[int]


class AIAgentResponse(AIAgentBase):
    id: int
    status: AgentStatus
    last_activity_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIAgentWithSites(AIAgentResponse):
    assigned_sites: List[SiteResponse] = []


# ============== Activity Schemas ==============

class ActivityBase(BaseModel):
    agent_id: int
    activity_type: ActivityType
    load_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = {}


class ActivityCreate(ActivityBase):
    pass


class ActivityResponse(ActivityBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============== Escalation Schemas ==============

class EscalationBase(BaseModel):
    issue_type: IssueType
    description: str
    priority: Optional[EscalationPriority] = EscalationPriority.MEDIUM
    load_id: Optional[int] = None
    site_id: Optional[int] = None


class EscalationCreate(EscalationBase):
    created_by_agent_id: Optional[int] = None


class EscalationUpdate(BaseModel):
    status: Optional[EscalationStatus] = None
    priority: Optional[EscalationPriority] = None
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None


class EscalationResponse(EscalationBase):
    id: int
    created_by_agent_id: Optional[int] = None
    status: EscalationStatus
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EscalationWithDetails(EscalationResponse):
    load: Optional[LoadResponse] = None
    site: Optional[SiteResponse] = None


# ============== Dashboard Schemas ==============

class DashboardStats(BaseModel):
    total_sites: int
    sites_at_risk: int  # Sites below runout threshold
    active_loads: int
    delayed_loads: int
    open_escalations: int
    active_agents: int


class SiteInventoryStatus(BaseModel):
    site_id: int
    consignee_code: str
    consignee_name: str
    current_inventory: float
    hours_to_runout: Optional[float]
    is_at_risk: bool
    active_loads_count: int


# ============== Upload Audit Log Schemas ==============

class UploadAuditLogCreate(BaseModel):
    customer: Customer
    erp_source: ERPSource
    uploaded_by: Optional[str] = "coordinator"
    filename: Optional[str] = None
    records_processed: int = 0
    records_updated: int = 0
    records_created: int = 0
    records_failed: int = 0
    error_details: Optional[List[Dict[str, Any]]] = None


class UploadAuditLogResponse(UploadAuditLogCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchUploadResponse(BaseModel):
    """Response for batch upload operations"""
    updated: int
    created: int
    not_found: List[str]
    errors: List[Dict[str, Any]]
    total_processed: int
    audit_log_id: int


# ============== ERP Template Schemas ==============

class ERPTemplateInfo(BaseModel):
    """Information about an ERP template"""
    erp_source: ERPSource
    display_name: str
    columns: List[str]
    required_columns: List[str]
    sample_data: List[Dict[str, Any]]


# ============== Snapshot Ingestion Schemas ==============

class SiteSnapshotState(BaseModel):
    """Current state data for a single site (from hourly export)"""
    site_id: str  # consignee_code
    current_inventory: Optional[float] = None
    hours_to_runout: Optional[float] = None


class LoadSnapshotState(BaseModel):
    """Current state data for a single load (from hourly export)"""
    po_number: str
    destination_site_id: str  # consignee_code
    current_eta: Optional[datetime] = None
    status: Optional[LoadStatus] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    volume: Optional[float] = None


class SnapshotIngestion(BaseModel):
    """Schema for hourly snapshot ingestion"""
    snapshot_time: datetime
    source: str  # e.g., "fuel_shepherd_export", "manual_update", "google_sheets"
    customer: Customer
    erp_source: ERPSource
    notes: Optional[str] = None

    # State updates
    sites: List[SiteSnapshotState] = []
    loads: List[LoadSnapshotState] = []


class SnapshotIngestionResponse(BaseModel):
    """Response after snapshot ingestion"""
    success: bool
    snapshot_time: datetime
    source: str
    sites_updated: int
    sites_not_found: List[str]
    loads_updated: int
    loads_not_found: List[str]
    errors: List[Dict[str, Any]]


# Forward reference updates
SiteWithLoads.model_rebuild()
LoadWithDetails.model_rebuild()
EscalationWithDetails.model_rebuild()
