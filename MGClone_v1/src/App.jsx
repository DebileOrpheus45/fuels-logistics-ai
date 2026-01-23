import { useState } from 'react'
import { QueryClient, QueryClientProvider, useQuery, useMutation } from '@tanstack/react-query'
import {
  Truck, Package, Building2, AlertTriangle, Activity, Settings,
  ChevronRight, Clock, MapPin, User, Phone, Mail, FileText,
  TrendingUp, TrendingDown, Minus, Search, Filter, Download,
  RefreshCw, Calendar, BarChart3, Bell, CheckCircle, XCircle,
  Pause, Play, Fuel, Target, Archive
} from 'lucide-react'
import { format } from 'date-fns'
import './index.css'
import {
  getDashboardStats, getSites, getLoads, getAgents, getEscalations,
  getSentEmails, resolveMutation as resolveEscalationAPI, assignSiteToAgent,
  updateSite, batchUpdateSites, assignSitesToAgent, startAgent, stopAgent,
  pauseAgent, runAgentCheck
} from './api/client'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1
    }
  }
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  )
}

function Dashboard() {
  const [authToken, setAuthToken] = useState(localStorage.getItem('authToken'))
  const [activeView, setActiveView] = useState('control-tower')
  const [selectedLoad, setSelectedLoad] = useState(null)
  const [selectedEscalation, setSelectedEscalation] = useState(null)
  const [filterText, setFilterText] = useState('')

  // Queries
  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
    enabled: !!authToken,
    refetchInterval: 30000
  })

  const { data: sites = [] } = useQuery({
    queryKey: ['sites'],
    queryFn: getSites,
    enabled: !!authToken
  })

  const { data: loads = [] } = useQuery({
    queryKey: ['loads'],
    queryFn: getLoads,
    enabled: !!authToken
  })

  const { data: agents = [] } = useQuery({
    queryKey: ['agents'],
    queryFn: getAgents,
    enabled: !!authToken
  })

  const { data: escalations = [] } = useQuery({
    queryKey: ['escalations'],
    queryFn: getEscalations,
    enabled: !!authToken
  })

  // Mutations
  const resolveMutation = useMutation({
    mutationFn: ({ id, notes }) => resolveEscalationAPI(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries(['escalations'])
      setSelectedEscalation(null)
    }
  })

  const startAgentMutation = useMutation({
    mutationFn: (agentId) => startAgent(agentId),
    onSuccess: () => queryClient.invalidateQueries(['agents'])
  })

  const stopAgentMutation = useMutation({
    mutationFn: (agentId) => stopAgent(agentId),
    onSuccess: () => queryClient.invalidateQueries(['agents'])
  })

  const runCheckMutation = useMutation({
    mutationFn: (agentId) => runAgentCheck(agentId),
    onSuccess: () => {
      queryClient.invalidateQueries(['agents'])
      queryClient.invalidateQueries(['escalations'])
    }
  })

  if (!authToken) {
    return <LoginScreen onLogin={setAuthToken} />
  }

  // Get critical escalations for banner
  const criticalEscalations = escalations.filter(e => e.priority === 'CRITICAL' && e.status === 'OPEN')

  // Filter loads based on search
  const filteredLoads = loads.filter(load =>
    !filterText ||
    load.po_number?.toLowerCase().includes(filterText.toLowerCase()) ||
    load.consignee_name?.toLowerCase().includes(filterText.toLowerCase()) ||
    load.carrier_name?.toLowerCase().includes(filterText.toLowerCase())
  )

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar Navigation */}
      <div className="mg-sidebar">
        <div className="p-6 border-b border-white border-opacity-20">
          <div className="flex items-center gap-3">
            <Fuel className="h-8 w-8 text-white" />
            <div>
              <div className="text-white font-bold text-lg">FuelTMS</div>
              <div className="text-blue-200 text-xs">ezVision Control Tower</div>
            </div>
          </div>
        </div>

        <nav className="mt-4">
          <div
            className={`mg-sidebar-item ${activeView === 'control-tower' ? 'active' : ''}`}
            onClick={() => setActiveView('control-tower')}
          >
            <BarChart3 className="h-5 w-5" />
            <span>Control Tower</span>
          </div>
          <div
            className={`mg-sidebar-item ${activeView === 'loads' ? 'active' : ''}`}
            onClick={() => setActiveView('loads')}
          >
            <Truck className="h-5 w-5" />
            <span>Load Board</span>
          </div>
          <div
            className={`mg-sidebar-item ${activeView === 'sites' ? 'active' : ''}`}
            onClick={() => setActiveView('sites')}
          >
            <Building2 className="h-5 w-5" />
            <span>Sites</span>
          </div>
          <div
            className={`mg-sidebar-item ${activeView === 'agents' ? 'active' : ''}`}
            onClick={() => setActiveView('agents')}
          >
            <Activity className="h-5 w-5" />
            <span>AI Agents</span>
          </div>
          <div
            className={`mg-sidebar-item ${activeView === 'escalations' ? 'active' : ''}`}
            onClick={() => setActiveView('escalations')}
          >
            <AlertTriangle className="h-5 w-5" />
            <span>Escalations</span>
            {criticalEscalations.length > 0 && (
              <span className="ml-auto bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                {criticalEscalations.length}
              </span>
            )}
          </div>
        </nav>

        <div className="absolute bottom-0 w-full p-4 border-t border-white border-opacity-20">
          <div className="flex items-center gap-3 text-blue-200">
            <User className="h-5 w-5" />
            <div className="text-sm">
              <div className="text-white font-medium">Coordinator</div>
              <button
                onClick={() => {
                  localStorage.removeItem('authToken')
                  setAuthToken(null)
                }}
                className="text-xs hover:text-white"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header Bar */}
        <div className="control-tower-header">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Fuels Logistics Control Tower</h1>
              <p className="text-blue-100 text-sm mt-1">Real-time visibility and intelligent automation</p>
            </div>
            <div className="flex items-center gap-4">
              <button className="mg-button mg-button-secondary">
                <Download className="h-4 w-4" />
                Export
              </button>
              <button
                className="mg-button mg-button-primary"
                onClick={() => {
                  queryClient.invalidateQueries()
                }}
              >
                <RefreshCw className="h-4 w-4" />
                Refresh
              </button>
            </div>
          </div>
        </div>

        {/* Critical Alerts Banner */}
        {criticalEscalations.length > 0 && (
          <div className="alert-banner critical mx-6 mt-4">
            <AlertTriangle className="h-5 w-5" />
            <div className="flex-1">
              <strong>{criticalEscalations.length} Critical Escalation{criticalEscalations.length > 1 ? 's' : ''}</strong>
              {' - '}
              {criticalEscalations[0].description}
            </div>
            <button
              onClick={() => setActiveView('escalations')}
              className="text-sm underline"
            >
              View All
            </button>
          </div>
        )}

        {/* KPI Dashboard - Always visible at top */}
        <div className="px-6 py-4 bg-white border-b">
          <div className="grid grid-cols-6 gap-4">
            <KPICard
              icon={<Building2 className="h-6 w-6 text-blue-600" />}
              value={stats?.total_sites || 0}
              label="Total Sites"
              onClick={() => setActiveView('sites')}
            />
            <KPICard
              icon={<AlertTriangle className="h-6 w-6 text-orange-600" />}
              value={stats?.sites_at_risk || 0}
              label="At Risk"
              change="critical"
              onClick={() => setActiveView('sites')}
            />
            <KPICard
              icon={<Truck className="h-6 w-6 text-green-600" />}
              value={stats?.active_loads || 0}
              label="Active Loads"
              onClick={() => setActiveView('loads')}
            />
            <KPICard
              icon={<Clock className="h-6 w-6 text-amber-600" />}
              value={stats?.delayed_loads || 0}
              label="Delayed"
              change="negative"
              onClick={() => setActiveView('loads')}
            />
            <KPICard
              icon={<AlertTriangle className="h-6 w-6 text-red-600" />}
              value={stats?.open_escalations || 0}
              label="Open Issues"
              onClick={() => setActiveView('escalations')}
            />
            <KPICard
              icon={<Activity className="h-6 w-6 text-indigo-600" />}
              value={stats?.active_agents || 0}
              label="Active Agents"
              onClick={() => setActiveView('agents')}
            />
          </div>
        </div>

        {/* Main Content Views */}
        <div className="flex-1 overflow-auto p-6">
          {activeView === 'control-tower' && (
            <ControlTowerView
              loads={filteredLoads}
              sites={sites}
              escalations={escalations}
              onSelectLoad={setSelectedLoad}
            />
          )}
          {activeView === 'loads' && (
            <LoadBoardView
              loads={filteredLoads}
              filterText={filterText}
              setFilterText={setFilterText}
              onSelectLoad={setSelectedLoad}
            />
          )}
          {activeView === 'sites' && (
            <SitesView sites={sites} />
          )}
          {activeView === 'agents' && (
            <AgentsView
              agents={agents}
              onStart={startAgentMutation.mutate}
              onStop={stopAgentMutation.mutate}
              onRunCheck={runCheckMutation.mutate}
            />
          )}
          {activeView === 'escalations' && (
            <EscalationsView
              escalations={escalations}
              onSelect={setSelectedEscalation}
            />
          )}
        </div>
      </div>

      {/* Modals */}
      {selectedLoad && (
        <LoadDetailModal load={selectedLoad} onClose={() => setSelectedLoad(null)} />
      )}
      {selectedEscalation && (
        <EscalationModal
          escalation={selectedEscalation}
          onClose={() => setSelectedEscalation(null)}
          onResolve={(notes) => resolveMutation.mutate({ id: selectedEscalation.id, notes })}
        />
      )}
    </div>
  )
}

// KPI Card Component
function KPICard({ icon, value, label, change, onClick }) {
  return (
    <div className="kpi-card" onClick={onClick}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="kpi-value">{value}</div>
          <div className="kpi-label">{label}</div>
          {change && (
            <div className={`kpi-change ${change === 'critical' || change === 'negative' ? 'negative' : 'positive'}`}>
              {change === 'critical' && '⚠ Needs Attention'}
              {change === 'negative' && '↓ Review Required'}
              {change === 'positive' && '↑ On Track'}
            </div>
          )}
        </div>
        <div className="mt-1">{icon}</div>
      </div>
    </div>
  )
}

// Control Tower View - Main dashboard with prioritized view
function ControlTowerView({ loads, sites, escalations, onSelectLoad }) {
  const atRiskSites = sites.filter(s => s.hours_to_runout <= 48)
  const criticalLoads = loads.filter(l =>
    l.status === 'IN_TRANSIT' &&
    (!l.current_eta || new Date(l.current_eta) < new Date())
  )
  const openEscalations = escalations.filter(e => e.status === 'OPEN')

  return (
    <div className="space-y-6">
      {/* Priority Actions Section */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="p-4 border-b bg-gray-50">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <Target className="h-5 w-5 text-red-600" />
            Priority Actions Required
          </h2>
        </div>
        <div className="p-4">
          {openEscalations.length === 0 && atRiskSites.length === 0 && criticalLoads.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-2" />
              <p>No priority actions required - all systems operating normally</p>
            </div>
          ) : (
            <div className="space-y-3">
              {openEscalations.slice(0, 3).map(esc => (
                <div key={esc.id} className="flex items-start gap-3 p-3 bg-red-50 rounded border-l-4 border-red-500">
                  <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{esc.description}</div>
                    <div className="text-sm text-gray-600 mt-1">
                      {esc.site_name || esc.po_number} • {format(new Date(esc.created_at), 'MMM d, h:mm a')}
                    </div>
                  </div>
                  <span className={`status-badge ${esc.priority.toLowerCase()}`}>
                    {esc.priority}
                  </span>
                </div>
              ))}
              {atRiskSites.slice(0, 3).map(site => (
                <div key={site.id} className="flex items-start gap-3 p-3 bg-orange-50 rounded border-l-4 border-orange-500">
                  <Building2 className="h-5 w-5 text-orange-600 mt-0.5" />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{site.consignee_name}</div>
                    <div className="text-sm text-gray-600 mt-1">
                      {site.hours_to_runout.toFixed(1)} hours to runout • {site.current_inventory.toLocaleString()} gal remaining
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Active Loads Table */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="p-4 border-b bg-gray-50">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <Truck className="h-5 w-5 text-blue-600" />
            Active Loads ({loads.filter(l => l.status !== 'DELIVERED' && l.status !== 'CANCELLED').length})
          </h2>
        </div>
        <table className="control-tower-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>PO Number</th>
              <th>Destination</th>
              <th>Carrier</th>
              <th>Volume</th>
              <th>ETA</th>
              <th>Last Update</th>
            </tr>
          </thead>
          <tbody>
            {loads.filter(l => l.status !== 'DELIVERED' && l.status !== 'CANCELLED').slice(0, 10).map(load => (
              <tr key={load.id} onClick={() => onSelectLoad(load)}>
                <td>
                  <span className={`status-badge ${load.status.toLowerCase().replace('_', '-')}`}>
                    {load.status.replace('_', ' ')}
                  </span>
                </td>
                <td>
                  <div className="stacked-column">
                    <span className="primary">{load.po_number}</span>
                    <span className="secondary">{load.tms_load_number || 'N/A'}</span>
                  </div>
                </td>
                <td>
                  <div className="stacked-column">
                    <span className="primary">{load.consignee_name}</span>
                    <span className="secondary">{load.origin_terminal}</span>
                  </div>
                </td>
                <td>
                  <div className="stacked-column">
                    <span className="primary">{load.carrier_name}</span>
                    {load.driver_name && <span className="secondary">{load.driver_name}</span>}
                  </div>
                </td>
                <td>{load.volume?.toLocaleString()} gal</td>
                <td>
                  {load.current_eta ? (
                    <div className="stacked-column">
                      <span className="primary">{format(new Date(load.current_eta), 'MMM d, h:mm a')}</span>
                      {load.last_eta_update && (
                        <span className="secondary">
                          Updated {format(new Date(load.last_eta_update), 'h:mm a')}
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-gray-400">Not available</span>
                  )}
                </td>
                <td>
                  {load.last_email_sent ? (
                    format(new Date(load.last_email_sent), 'MMM d, h:mm a')
                  ) : (
                    <span className="text-gray-400">No contact</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Load Board View
function LoadBoardView({ loads, filterText, setFilterText, onSelectLoad }) {
  return (
    <div className="space-y-4">
      {/* Filter Bar */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 flex items-center gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search by PO, site, or carrier..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <button className="mg-button mg-button-secondary">
          <Filter className="h-4 w-4" />
          Filters
        </button>
      </div>

      {/* Loads Table */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <table className="control-tower-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>PO Number</th>
              <th>Destination</th>
              <th>Carrier</th>
              <th>Product</th>
              <th>Volume</th>
              <th>ETA</th>
              <th>Tracking</th>
            </tr>
          </thead>
          <tbody>
            {loads.map(load => (
              <tr key={load.id} onClick={() => onSelectLoad(load)}>
                <td>
                  <span className={`status-badge ${load.status.toLowerCase().replace('_', '-')}`}>
                    {load.status.replace('_', ' ')}
                  </span>
                </td>
                <td>
                  <div className="stacked-column">
                    <span className="primary">{load.po_number}</span>
                    <span className="secondary">{load.tms_load_number || 'No TMS ID'}</span>
                  </div>
                </td>
                <td>
                  <div className="stacked-column">
                    <span className="primary">{load.consignee_name}</span>
                    <span className="secondary">{load.origin_terminal}</span>
                  </div>
                </td>
                <td>
                  <div className="stacked-column">
                    <span className="primary">{load.carrier_name}</span>
                    {load.driver_name && <span className="secondary">Driver: {load.driver_name}</span>}
                  </div>
                </td>
                <td>{load.product_type}</td>
                <td>{load.volume?.toLocaleString()} gal</td>
                <td>
                  {load.current_eta ? format(new Date(load.current_eta), 'MMM d, h:mm a') : (
                    <span className="text-gray-400">TBD</span>
                  )}
                </td>
                <td>
                  {load.has_macropoint_tracking ? (
                    <span className="text-green-600 text-sm font-medium">✓ GPS Active</span>
                  ) : (
                    <span className="text-gray-400 text-sm">No tracking</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Sites View
function SitesView({ sites }) {
  const criticalSites = sites.filter(s => s.hours_to_runout < 12)
  const atRiskSites = sites.filter(s => s.hours_to_runout >= 12 && s.hours_to_runout <= 48)
  const healthySites = sites.filter(s => s.hours_to_runout > 48)

  return (
    <div className="space-y-6">
      {criticalSites.length > 0 && (
        <SiteSection title="Critical Sites" sites={criticalSites} color="red" />
      )}
      {atRiskSites.length > 0 && (
        <SiteSection title="At Risk Sites" sites={atRiskSites} color="orange" />
      )}
      {healthySites.length > 0 && (
        <SiteSection title="Healthy Sites" sites={healthySites} color="green" />
      )}
    </div>
  )
}

function SiteSection({ title, sites, color }) {
  const colorClasses = {
    red: 'border-red-500 bg-red-50',
    orange: 'border-orange-500 bg-orange-50',
    green: 'border-green-500 bg-green-50'
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="p-4 border-b bg-gray-50">
        <h2 className="font-semibold text-gray-900">{title} ({sites.length})</h2>
      </div>
      <div className="p-4 grid grid-cols-3 gap-4">
        {sites.map(site => (
          <div key={site.id} className={`border-l-4 ${colorClasses[color]} p-4 rounded`}>
            <div className="font-semibold text-gray-900">{site.consignee_name}</div>
            <div className="text-sm text-gray-600 mt-1">{site.consignee_code}</div>
            <div className="mt-3 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Inventory:</span>
                <span className="font-medium">{site.current_inventory.toLocaleString()} gal</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Capacity:</span>
                <span className="font-medium">{site.tank_capacity.toLocaleString()} gal</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Time to Runout:</span>
                <span className={`font-bold ${color === 'red' ? 'text-red-600' : color === 'orange' ? 'text-orange-600' : 'text-green-600'}`}>
                  {site.hours_to_runout.toFixed(1)} hrs
                </span>
              </div>
              <div className="data-bar">
                <div
                  className="data-bar-fill"
                  style={{
                    width: `${(site.current_inventory / site.tank_capacity * 100).toFixed(0)}%`,
                    background: color === 'red' ? '#ef4444' : color === 'orange' ? '#f97316' : '#10b981'
                  }}
                />
              </div>
            </div>
            {site.notes && (
              <div className="mt-3 pt-3 border-t text-xs text-gray-600">
                📝 {site.notes}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// Agents View
function AgentsView({ agents, onStart, onStop, onRunCheck }) {
  return (
    <div className="space-y-4">
      {agents.map(agent => (
        <div key={agent.id} className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <Activity className="h-6 w-6 text-indigo-600" />
                <div>
                  <h3 className="font-semibold text-lg text-gray-900">{agent.agent_name}</h3>
                  <p className="text-sm text-gray-600">{agent.persona_type}</p>
                </div>
                <span className={`status-badge ${agent.status.toLowerCase()}`}>
                  {agent.status}
                </span>
              </div>
              <div className="mt-4 grid grid-cols-3 gap-4">
                <div>
                  <div className="text-sm text-gray-600">Assigned Sites</div>
                  <div className="text-2xl font-bold text-gray-900">{agent.assigned_sites?.length || 0}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Check Interval</div>
                  <div className="text-2xl font-bold text-gray-900">{agent.check_interval_minutes} min</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Last Activity</div>
                  <div className="text-sm font-medium text-gray-900">
                    {agent.last_activity_at ? format(new Date(agent.last_activity_at), 'MMM d, h:mm a') : 'Never'}
                  </div>
                </div>
              </div>
            </div>
            <div className="flex flex-col gap-2">
              {agent.status === 'STOPPED' || agent.status === 'PAUSED' ? (
                <button
                  onClick={() => onStart(agent.id)}
                  className="mg-button mg-button-primary"
                >
                  <Play className="h-4 w-4" />
                  Start Agent
                </button>
              ) : (
                <button
                  onClick={() => onStop(agent.id)}
                  className="mg-button mg-button-secondary"
                >
                  <Pause className="h-4 w-4" />
                  Stop Agent
                </button>
              )}
              <button
                onClick={() => onRunCheck(agent.id)}
                className="mg-button mg-button-secondary"
              >
                <RefreshCw className="h-4 w-4" />
                Run Check Now
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// Escalations View
function EscalationsView({ escalations, onSelect }) {
  const openEscalations = escalations.filter(e => e.status === 'OPEN')
  const resolvedEscalations = escalations.filter(e => e.status === 'RESOLVED')

  return (
    <div className="space-y-6">
      {openEscalations.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="p-4 border-b bg-gray-50">
            <h2 className="font-semibold text-gray-900">Open Escalations ({openEscalations.length})</h2>
          </div>
          <div className="divide-y">
            {openEscalations.map(esc => (
              <div
                key={esc.id}
                className="p-4 hover:bg-gray-50 cursor-pointer relative"
                onClick={() => onSelect(esc)}
              >
                <div className={`priority-indicator ${esc.priority.toLowerCase()}`} />
                <div className="pl-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`status-badge ${esc.priority.toLowerCase()}`}>
                          {esc.priority}
                        </span>
                        <span className="text-sm font-medium text-gray-600">{esc.issue_type.replace('_', ' ')}</span>
                      </div>
                      <p className="mt-2 text-gray-900">{esc.description}</p>
                      <div className="mt-2 text-sm text-gray-600">
                        {esc.site_name && `Site: ${esc.site_name}`}
                        {esc.po_number && ` • Load: ${esc.po_number}`}
                        {' • '}
                        Created {format(new Date(esc.created_at), 'MMM d, h:mm a')}
                      </div>
                    </div>
                    <ChevronRight className="h-5 w-5 text-gray-400" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {resolvedEscalations.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="p-4 border-b bg-gray-50">
            <h2 className="font-semibold text-gray-900">Resolved ({resolvedEscalations.length})</h2>
          </div>
          <div className="divide-y">
            {resolvedEscalations.slice(0, 5).map(esc => (
              <div key={esc.id} className="p-4 opacity-60">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="text-sm text-gray-600">{esc.description}</span>
                  <span className="text-xs text-gray-400 ml-auto">
                    {format(new Date(esc.resolved_at), 'MMM d')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Load Detail Modal
function LoadDetailModal({ load, onClose }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full" onClick={e => e.stopPropagation()}>
        <div className="p-6 border-b flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Truck className="h-6 w-6 text-blue-600" />
            <div>
              <h2 className="text-xl font-bold">Load Details</h2>
              <p className="text-sm text-gray-600">{load.po_number}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XCircle className="h-6 w-6" />
          </button>
        </div>
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-600">Status</div>
              <span className={`status-badge ${load.status.toLowerCase().replace('_', '-')}`}>
                {load.status.replace('_', ' ')}
              </span>
            </div>
            <div>
              <div className="text-sm text-gray-600">TMS Load Number</div>
              <div className="font-medium">{load.tms_load_number || 'N/A'}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Destination</div>
              <div className="font-medium">{load.consignee_name}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Origin</div>
              <div className="font-medium">{load.origin_terminal}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Carrier</div>
              <div className="font-medium">{load.carrier_name}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Product</div>
              <div className="font-medium">{load.product_type}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Volume</div>
              <div className="font-medium">{load.volume?.toLocaleString()} gallons</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Current ETA</div>
              <div className="font-medium">
                {load.current_eta ? format(new Date(load.current_eta), 'MMM d, yyyy h:mm a') : 'Not available'}
              </div>
            </div>
            {load.driver_name && (
              <>
                <div>
                  <div className="text-sm text-gray-600">Driver</div>
                  <div className="font-medium">{load.driver_name}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-600">Driver Phone</div>
                  <div className="font-medium">{load.driver_phone || 'N/A'}</div>
                </div>
              </>
            )}
            <div>
              <div className="text-sm text-gray-600">GPS Tracking</div>
              <div className="font-medium">
                {load.has_macropoint_tracking ? '✓ Active' : 'Not available'}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Last Email Sent</div>
              <div className="font-medium">
                {load.last_email_sent ? format(new Date(load.last_email_sent), 'MMM d, h:mm a') : 'Never'}
              </div>
            </div>
          </div>
        </div>
        <div className="p-6 border-t bg-gray-50 flex justify-end">
          <button onClick={onClose} className="mg-button mg-button-primary">
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

// Escalation Modal
function EscalationModal({ escalation, onClose, onResolve }) {
  const [notes, setNotes] = useState('')

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full" onClick={e => e.stopPropagation()}>
        <div className="p-6 border-b flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-6 w-6 text-red-600" />
            <div>
              <h2 className="text-xl font-bold">Escalation Details</h2>
              <span className={`status-badge ${escalation.priority.toLowerCase()}`}>
                {escalation.priority}
              </span>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XCircle className="h-6 w-6" />
          </button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <div className="text-sm text-gray-600">Issue Type</div>
            <div className="font-medium">{escalation.issue_type.replace('_', ' ')}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Description</div>
            <div className="font-medium">{escalation.description}</div>
          </div>
          {escalation.site_name && (
            <div>
              <div className="text-sm text-gray-600">Related Site</div>
              <div className="font-medium">{escalation.site_name}</div>
            </div>
          )}
          {escalation.po_number && (
            <div>
              <div className="text-sm text-gray-600">Related Load</div>
              <div className="font-medium">{escalation.po_number}</div>
            </div>
          )}
          <div>
            <div className="text-sm text-gray-600">Created</div>
            <div className="font-medium">{format(new Date(escalation.created_at), 'MMM d, yyyy h:mm a')}</div>
          </div>
          {escalation.status === 'OPEN' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Resolution Notes
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows="4"
                placeholder="Describe how this issue was resolved..."
              />
            </div>
          )}
          {escalation.resolution_notes && (
            <div>
              <div className="text-sm text-gray-600">Resolution Notes</div>
              <div className="font-medium">{escalation.resolution_notes}</div>
            </div>
          )}
        </div>
        <div className="p-6 border-t bg-gray-50 flex justify-end gap-3">
          <button onClick={onClose} className="mg-button mg-button-secondary">
            Close
          </button>
          {escalation.status === 'OPEN' && (
            <button
              onClick={() => onResolve(notes)}
              disabled={!notes.trim()}
              className="mg-button mg-button-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CheckCircle className="h-4 w-4" />
              Resolve Escalation
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// Login Screen
function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleLogin = (e) => {
    e.preventDefault()
    if (username === 'coordinator' && password === 'fuel2024') {
      const token = 'mock-auth-token'
      localStorage.setItem('authToken', token)
      onLogin(token)
    } else {
      setError('Invalid credentials')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-blue-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl p-8 max-w-md w-full">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Fuel className="h-12 w-12 text-blue-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">FuelTMS</h1>
              <p className="text-sm text-gray-600">ezVision Control Tower</p>
            </div>
          </div>
          <p className="text-gray-600">Sign in to continue</p>
        </div>
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="coordinator"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="••••••••"
            />
          </div>
          {error && (
            <div className="text-red-600 text-sm">{error}</div>
          )}
          <button type="submit" className="w-full mg-button mg-button-primary justify-center text-base py-3">
            Sign In
          </button>
        </form>
        <div className="mt-6 text-center text-sm text-gray-600">
          Demo credentials: coordinator / fuel2024
        </div>
      </div>
    </div>
  )
}

export default App
