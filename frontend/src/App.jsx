import { useState, useMemo, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import {
  getDashboardStats,
  getSites,
  getActiveLoads,
  getOpenEscalations,
  getEscalations,
  getAgents,
  updateAgent,
  runAgentCheck,
  getAgentActivities,
  getAllActivities,
  getAgentRunHistory,
  getRecentRunHistory,
  getSentEmails,
  getInboundEmails,
  resolveEscalation,
  updateSite,
  batchUpdateSites,
  exportSiteTemplate,
  assignSitesToAgent,
  getCustomers,
  getErpSources,
  getErpTemplate,
  addNoteToLoad,
  login as apiLogin,
  logout as apiLogout,
  getStoredUser,
  isAuthenticated,
  syncToSheets,
  getSheetsStatus,
  getIntelligence,
  refreshKnowledgeGraph,
  getStatusSummary,
  requestEtaForLoad,
  requestEtaForAllLoads
} from './api/client'
import {
  Fuel,
  Truck,
  AlertTriangle,
  Bot,
  Activity,
  Mail,
  Play,
  RefreshCw,
  CheckCircle,
  Clock,
  Bell,
  X,
  ChevronRight,
  LogOut,
  User,
  Lock,
  FileSpreadsheet,
  Download,
  ExternalLink,
  Eye,
  Filter,
  Terminal,
  Zap,
  History,
  Edit3,
  Save,
  Upload,
  Settings,
  StickyNote,
  Users,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  Send,
  MapPin,
  Navigation,
  Phone,
  Package,
  Calendar,
  ArrowRight,
  ArrowUp,
  ArrowDown,
  ArrowUpDown,
  Search,
  XCircle,
  AlertCircle,
  Brain,
  Shield,
  TrendingUp,
  Target,
  Layers
} from 'lucide-react'

// ============== Login Page ==============
function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      // Call real API login
      const user = await apiLogin(username, password)
      onLogin({
        username: user.username,
        role: user.role,
        name: user.full_name || user.username,
        email: user.email,
        id: user.id
      })
    } catch (err) {
      // Handle login error
      if (err.response?.status === 401) {
        setError('Invalid username or password')
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail)
      } else {
        setError('Login failed. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-100 flex items-center justify-center p-4">
      <div className="relative w-full max-w-md">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-slate-900 rounded-xl mb-4">
            <Fuel className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-semibold text-slate-900">Fuels Logistics</h1>
          <p className="text-slate-500 mt-1">AI Coordinator</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8">
          <h2 className="text-lg font-semibold text-slate-900 mb-6">Sign in to your account</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Username
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-500 focus:border-transparent transition"
                  placeholder="Enter username"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-slate-500 focus:border-transparent transition"
                  placeholder="Enter password"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 bg-slate-900 text-white font-medium rounded-lg hover:bg-slate-800 transition disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-100">
            <p className="text-xs text-slate-400 text-center mb-2">
              Demo credentials
            </p>
            <div className="flex flex-col gap-1 items-center">
              <code className="px-2 py-1 bg-slate-50 border border-slate-100 rounded text-xs text-slate-600">admin / admin123</code>
              <code className="px-2 py-1 bg-slate-50 border border-slate-100 rounded text-xs text-slate-600">coordinator / fuel2024</code>
            </div>
          </div>
        </div>

        <p className="text-center text-slate-400 text-xs mt-6">
          Powered by Claude AI
        </p>
      </div>
    </div>
  )
}

// ============== Fuel Gauge Component ==============
function FuelGauge({ percentage, size = 120, critical = 25, warning = 50 }) {
  const radius = (size - 20) / 2
  const circumference = radius * Math.PI
  const fillPercentage = Math.min(Math.max(percentage, 0), 100)
  const offset = circumference - (fillPercentage / 100) * circumference

  let color = '#22c55e'
  if (percentage <= critical) {
    color = '#ef4444'
  } else if (percentage <= warning) {
    color = '#f59e0b'
  }

  return (
    <div className="relative" style={{ width: size, height: size / 2 + 20 }}>
      <svg width={size} height={size / 2 + 10}>
        <path
          d={`M 10 ${size / 2} A ${radius} ${radius} 0 0 1 ${size - 10} ${size / 2}`}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="12"
          strokeLinecap="round"
        />
        <path
          d={`M 10 ${size / 2} A ${radius} ${radius} 0 0 1 ${size - 10} ${size / 2}`}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-500"
        />
      </svg>
      <div className="absolute inset-0 flex items-end justify-center pb-1">
        <span className="text-2xl font-bold" style={{ color }}>{Math.round(percentage)}%</span>
      </div>
    </div>
  )
}

// ============== Site Card with Gauge ==============
function SiteCard({ site, onAssign, agents, onEdit }) {
  const percentage = site.tank_capacity > 0
    ? (site.current_inventory / site.tank_capacity) * 100
    : 0

  const getStatusColor = () => {
    if (!site.hours_to_runout) return 'border-gray-200'
    if (site.hours_to_runout < 12) return 'border-red-500 bg-red-50'
    if (site.hours_to_runout < 24) return 'border-orange-500 bg-orange-50'
    if (site.hours_to_runout < 48) return 'border-yellow-500 bg-yellow-50'
    return 'border-green-500 bg-green-50'
  }

  const getStatusBadge = () => {
    if (!site.hours_to_runout) return null
    if (site.hours_to_runout < 12) {
      return <span className="px-2 py-1 text-xs font-bold bg-red-500 text-white rounded-full animate-pulse">CRITICAL</span>
    }
    if (site.hours_to_runout < 24) {
      return <span className="px-2 py-1 text-xs font-bold bg-orange-500 text-white rounded-full">HIGH RISK</span>
    }
    if (site.hours_to_runout < 48) {
      return <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">AT RISK</span>
    }
    return <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">OK</span>
  }

  const getCustomerLabel = (customer) => {
    if (!customer) return null
    const labels = {
      stark_industries: 'Stark',
      wayne_enterprises: 'Wayne',
      luthor_corp: 'Luthor'
    }
    return labels[customer] || customer
  }

  return (
    <div className={`border-2 rounded-xl p-4 ${getStatusColor()} transition-all hover:shadow-lg`}>
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="font-bold text-lg">{site.consignee_code}</h3>
          <p className="text-sm text-gray-600 truncate max-w-[150px]">{site.consignee_name}</p>
          {/* Customer and Service Type badges */}
          <div className="flex gap-1 mt-1 flex-wrap">
            {site.customer && (
              <span className="px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                {getCustomerLabel(site.customer)}
              </span>
            )}
            {site.service_type === 'inventory_and_tracking' && (
              <span className="px-1.5 py-0.5 text-xs bg-purple-100 text-purple-700 rounded">
                Inventory
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {getStatusBadge()}
          <button
            onClick={() => onEdit?.(site)}
            className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition"
            title="Edit site constraints"
          >
            <Edit3 className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="flex justify-center my-2">
        <FuelGauge percentage={percentage} size={100} />
      </div>

      <div className="space-y-1 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">Inventory:</span>
          <span className="font-medium">{site.current_inventory?.toLocaleString()} gal</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Hours to Runout:</span>
          <span className={`font-bold ${site.hours_to_runout < 24 ? 'text-red-600' : ''}`}>
            {site.hours_to_runout?.toFixed(1)}h
          </span>
        </div>
        <div className="flex justify-between items-center pt-2 border-t mt-2">
          <span className="text-gray-500 text-xs">Assigned Agent:</span>
          <select
            className="text-xs border rounded px-2 py-1"
            value={site.assigned_agent_id || ''}
            onChange={(e) => onAssign(site.id, e.target.value ? parseInt(e.target.value) : null)}
          >
            <option value="">None</option>
            {agents?.map(agent => (
              <option key={agent.id} value={agent.id}>{agent.agent_name}</option>
            ))}
          </select>
        </div>
        {site.notes && (
          <div className="mt-2 pt-2 border-t">
            <div className="flex items-start gap-1 text-xs text-gray-500">
              <StickyNote className="h-3 w-3 mt-0.5 flex-shrink-0" />
              <span className="truncate">{site.notes}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ============== Escalation Alert Banner ==============
function EscalationBanner({ escalations, onViewAll }) {
  const criticalCount = escalations?.filter(e => e.priority === 'critical').length || 0
  const highCount = escalations?.filter(e => e.priority === 'high').length || 0

  if (!escalations?.length) return null

  return (
    <div className={`mb-4 p-4 rounded-lg flex items-center justify-between animate-slideInRight ${
      criticalCount > 0 ? 'bg-red-600 text-white animate-pulseGlow' : 'bg-orange-500 text-white'
    }`}>
      <div className="flex items-center gap-3">
        <Bell className="h-6 w-6 animate-bounce" />
        <div>
          <p className="font-bold">
            {criticalCount > 0 && `${criticalCount} CRITICAL `}
            {highCount > 0 && `${highCount} High Priority `}
            Escalation{escalations.length > 1 ? 's' : ''} Requiring Attention
          </p>
          <p className="text-sm opacity-90">
            {escalations[0]?.description?.substring(0, 80)}...
          </p>
        </div>
      </div>
      <button
        onClick={onViewAll}
        className="flex items-center gap-1 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-smooth hover:scale-105"
      >
        View All <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  )
}

// ============== Escalation Detail Modal ==============
function EscalationModal({ escalation, onClose, onResolve }) {
  const [notes, setNotes] = useState('')

  if (!escalation) return null

  const getPriorityStyles = (priority) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 border-red-500 text-red-800'
      case 'high': return 'bg-orange-100 border-orange-500 text-orange-800'
      case 'medium': return 'bg-yellow-100 border-yellow-500 text-yellow-800'
      default: return 'bg-gray-100 border-gray-500 text-gray-800'
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full mx-4 overflow-hidden">
        <div className={`p-4 border-l-4 ${getPriorityStyles(escalation.priority)}`}>
          <div className="flex justify-between items-start">
            <div>
              <span className="text-xs font-bold uppercase">{escalation.priority} Priority</span>
              <h2 className="text-lg font-bold mt-1">{escalation.issue_type?.replace(/_/g, ' ')}</h2>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-black/10 rounded">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="p-6">
          <div className="mb-4">
            <h3 className="text-sm font-medium text-gray-500 mb-1">Description</h3>
            <p className="text-gray-900">{escalation.description}</p>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
            <div>
              <span className="text-gray-500">Created:</span>
              <p className="font-medium">{new Date(escalation.created_at).toLocaleString()}</p>
            </div>
            <div>
              <span className="text-gray-500">Status:</span>
              <p className={`font-medium capitalize ${escalation.status === 'resolved' ? 'text-green-600' : ''}`}>{escalation.status}</p>
            </div>
            {escalation.status === 'resolved' && escalation.resolved_at && (
              <div>
                <span className="text-gray-500">Resolved:</span>
                <p className="font-medium">{new Date(escalation.resolved_at).toLocaleString()}</p>
              </div>
            )}
          </div>

          {escalation.status === 'resolved' ? (
            <>
              {escalation.resolution_notes && (
                <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                  <h3 className="text-sm font-medium text-green-800 mb-1">Resolution Notes</h3>
                  <p className="text-sm text-green-700">{escalation.resolution_notes}</p>
                </div>
              )}
              <button
                onClick={onClose}
                className="w-full py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Close
              </button>
            </>
          ) : (
            <>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Resolution Notes
                </label>
                <textarea
                  className="w-full border rounded-lg p-2 text-sm"
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Enter notes about how this was resolved..."
                />
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => onResolve(escalation.id, notes)}
                  className="flex-1 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
                >
                  Mark as Resolved
                </button>
                <button
                  onClick={onClose}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

// ============== Email Detail Modal ==============
function EmailDetailModal({ email, onClose }) {
  if (!email) return null

  const isInbound = email._type === 'inbound'

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full mx-4 overflow-hidden">
        <div className={`p-4 ${isInbound ? 'bg-slate-800' : 'bg-slate-700'} text-white`}>
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-2">
              {isInbound ? <Mail className="h-5 w-5" /> : <Send className="h-5 w-5" />}
              <span className="font-medium">{isInbound ? 'Inbound Email' : 'Sent Email'}</span>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-white/20 rounded">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="p-6">
          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase">
                {isInbound ? 'From' : 'To'}
              </label>
              <p className="font-medium text-gray-900">{isInbound ? email.from_email : email.to}</p>
            </div>

            <div>
              <label className="text-xs font-medium text-gray-500 uppercase">Subject</label>
              <p className="font-medium text-gray-900">{email.subject}</p>
            </div>

            <div>
              <label className="text-xs font-medium text-gray-500 uppercase">
                {isInbound ? 'Received At' : 'Sent At'}
              </label>
              <p className="text-gray-700">
                {new Date(isInbound ? email.received_at : email.sent_at).toLocaleString()}
              </p>
            </div>

            <div>
              <label className="text-xs font-medium text-gray-500 uppercase">Message</label>
              <div className="mt-1 p-4 bg-gray-50 rounded-lg border text-sm whitespace-pre-wrap font-mono max-h-48 overflow-y-auto">
                {email.body || 'No body content available'}
              </div>
            </div>

            {/* Inbound-specific: parse results */}
            {isInbound && (
              <div className="border-t pt-4 space-y-3">
                <h4 className="text-xs font-medium text-gray-500 uppercase">Parse Results</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="text-xs text-gray-500">PO Number</span>
                    <p className="text-sm font-medium text-gray-900">{email.po_number || '(not found)'}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Parse Method</span>
                    <p className="text-sm font-medium text-gray-900">{email.parse_method?.toUpperCase() || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Parsed ETA</span>
                    <p className="text-sm font-medium text-gray-900">
                      {email.parsed_eta ? new Date(email.parsed_eta).toLocaleString() : '(none)'}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500">Status</span>
                    <span className={`inline-block text-xs px-2 py-0.5 rounded-full font-medium ${
                      email.parse_success ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
                    }`}>
                      {email.parse_success ? 'Success' : 'Needs Review'}
                    </span>
                  </div>
                </div>
                {email.parse_message && (
                  <p className="text-xs text-gray-500 italic">{email.parse_message}</p>
                )}
              </div>
            )}

            {/* Sent-specific: mock warning */}
            {!isInbound && email.mock && (
              <div className="flex items-center gap-2 text-amber-600 text-sm">
                <AlertTriangle className="h-4 w-4" />
                This was a mock email (Gmail not configured)
              </div>
            )}
          </div>

          <button
            onClick={onClose}
            className="mt-6 w-full py-2 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

// ============== Site Details Modal (Notes & Constraints) ==============
function SiteDetailsModal({ site, onClose, onSave }) {
  const [formData, setFormData] = useState({
    tank_capacity: site?.tank_capacity || '',
    consumption_rate: site?.consumption_rate || '',
    runout_threshold_hours: site?.runout_threshold_hours || 48,
    min_delivery_quantity: site?.min_delivery_quantity || '',
    notes: site?.notes || ''
  })
  const [isSaving, setIsSaving] = useState(false)

  if (!site) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSaving(true)
    try {
      await onSave(site.id, {
        tank_capacity: formData.tank_capacity ? parseFloat(formData.tank_capacity) : null,
        consumption_rate: formData.consumption_rate ? parseFloat(formData.consumption_rate) : null,
        runout_threshold_hours: formData.runout_threshold_hours ? parseFloat(formData.runout_threshold_hours) : 48,
        min_delivery_quantity: formData.min_delivery_quantity ? parseFloat(formData.min_delivery_quantity) : null,
        notes: formData.notes || null
      })
      onClose()
    } catch (error) {
      console.error('Error saving site:', error)
    }
    setIsSaving(false)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-lg w-full mx-4 overflow-hidden">
        <div className="p-4 bg-gradient-to-r from-blue-600 to-cyan-600 text-white">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-lg font-bold">{site.consignee_code}</h2>
              <p className="text-sm text-blue-100">{site.consignee_name}</p>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-white/20 rounded">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Constraints Section */}
          <div>
            <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
              <Settings className="h-4 w-4" /> Site Constraints
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Tank Capacity (gal)
                </label>
                <input
                  type="number"
                  value={formData.tank_capacity}
                  onChange={(e) => setFormData({ ...formData, tank_capacity: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                  placeholder="e.g., 10000"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Consumption Rate (gal/hr)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.consumption_rate}
                  onChange={(e) => setFormData({ ...formData, consumption_rate: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                  placeholder="e.g., 50"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Runout Threshold (hrs)
                </label>
                <input
                  type="number"
                  value={formData.runout_threshold_hours}
                  onChange={(e) => setFormData({ ...formData, runout_threshold_hours: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                  placeholder="e.g., 48"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Min Delivery Qty (gal)
                </label>
                <input
                  type="number"
                  value={formData.min_delivery_quantity}
                  onChange={(e) => setFormData({ ...formData, min_delivery_quantity: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                  placeholder="e.g., 5000"
                />
              </div>
            </div>
          </div>

          {/* Notes Section */}
          <div>
            <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-2">
              <StickyNote className="h-4 w-4" /> Coordinator Notes
            </h3>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm"
              rows={4}
              placeholder="Add notes about this site (e.g., 'Site often understaffed on weekends', 'Requires 24hr notice for deliveries')"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={isSaving}
              className="flex-1 flex items-center justify-center gap-2 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
            >
              {isSaving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Save Changes
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ============== Batch Upload Modal ==============
function BatchUploadModal({ onClose, onUpload }) {
  const fileInputRef = useRef(null)
  const [csvData, setCsvData] = useState(null)
  const [preview, setPreview] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [selectedCustomer, setSelectedCustomer] = useState('')
  const [selectedErp, setSelectedErp] = useState('')
  const [erpTemplate, setErpTemplate] = useState(null)

  // Fetch customers and ERP sources
  const { data: customers = [] } = useQuery({
    queryKey: ['customers'],
    queryFn: getCustomers
  })

  const { data: erpSources = [] } = useQuery({
    queryKey: ['erp-sources'],
    queryFn: getErpSources
  })

  // Column mapping for different ERPs
  const erpColumnMappings = {
    fuel_shepherd: {
      consignee_code: 'site_id',
      consignee_name: 'site_name',
      tank_capacity: 'tank_size_gal',
      consumption_rate: 'usage_rate_gph',
      runout_threshold_hours: 'alert_threshold_hrs',
      min_delivery_quantity: 'min_drop_gal',
      notes: 'comments',
      service_type: 'service_level'
    },
    fuelquest: {
      consignee_code: 'location_code',
      consignee_name: 'location_name',
      tank_capacity: 'capacity',
      consumption_rate: 'consumption',
      runout_threshold_hours: 'threshold',
      min_delivery_quantity: 'minimum_delivery',
      notes: 'notes',
      service_type: 'tracking_type'
    },
    manual: {
      consignee_code: 'consignee_code',
      consignee_name: 'consignee_name',
      tank_capacity: 'tank_capacity',
      consumption_rate: 'consumption_rate',
      runout_threshold_hours: 'runout_threshold_hours',
      min_delivery_quantity: 'min_delivery_quantity',
      notes: 'notes',
      service_type: 'service_type'
    }
  }

  // Load ERP template when selection changes
  const loadErpTemplate = async (erp) => {
    if (!erp) {
      setErpTemplate(null)
      return
    }
    try {
      const template = await getErpTemplate(erp)
      setErpTemplate(template)
    } catch (error) {
      console.error('Error loading ERP template:', error)
    }
  }

  const handleErpChange = (erp) => {
    setSelectedErp(erp)
    loadErpTemplate(erp)
    // Clear any existing data when ERP changes
    setCsvData(null)
    setPreview([])
  }

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      const text = event.target.result
      const lines = text.split('\n').filter(line => line.trim())
      const headers = lines[0].split(',').map(h => h.trim().toLowerCase().replace(/['"]/g, ''))

      // Get the column mapping for the selected ERP
      const mapping = erpColumnMappings[selectedErp] || erpColumnMappings.manual
      const reverseMapping = Object.fromEntries(
        Object.entries(mapping).map(([k, v]) => [v.toLowerCase(), k])
      )

      const data = lines.slice(1).map(line => {
        // Handle CSV with quoted values
        const values = line.match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g) || line.split(',')
        const obj = {}
        headers.forEach((header, idx) => {
          const normalizedHeader = header.toLowerCase().replace(/['"]/g, '')
          const standardField = reverseMapping[normalizedHeader] || normalizedHeader
          let value = values[idx]?.trim().replace(/^["']|["']$/g, '') || null
          // Convert numeric fields
          if (['tank_capacity', 'consumption_rate', 'runout_threshold_hours', 'min_delivery_quantity'].includes(standardField)) {
            value = value ? parseFloat(value) : null
          }
          obj[standardField] = value
        })
        return obj
      }).filter(row => row.consignee_code)

      setCsvData(data)
      setPreview(data.slice(0, 5))
    }
    reader.readAsText(file)
  }

  const handleUpload = async () => {
    if (!csvData || !selectedCustomer || !selectedErp) return

    setIsUploading(true)
    try {
      const result = await onUpload(selectedCustomer, selectedErp, csvData)
      setResult(result)
    } catch (error) {
      setResult({ error: error.message })
    }
    setIsUploading(false)
  }

  const downloadTemplate = async () => {
    if (!selectedErp) {
      alert('Please select an ERP system first')
      return
    }

    try {
      const template = erpTemplate || await getErpTemplate(selectedErp)
      const csv = [
        template.columns.join(','),
        ...template.sample_data.map(row => template.columns.map(col => row[col] ?? '').join(','))
      ].join('\n')

      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${template.display_name.replace(/\s+/g, '-').toLowerCase()}-template.csv`
      a.click()
    } catch (error) {
      console.error('Error downloading template:', error)
    }
  }

  const canUpload = csvData && selectedCustomer && selectedErp && !isUploading

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full mx-4 overflow-hidden">
        <div className="p-4 bg-gradient-to-r from-green-600 to-emerald-600 text-white">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              <span className="font-bold">Batch Upload Site Data</span>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-white/20 rounded">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {!result ? (
            <>
              {/* Customer and ERP Selection */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Customer <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={selectedCustomer}
                    onChange={(e) => setSelectedCustomer(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    <option value="">Select Customer...</option>
                    {customers.map(c => (
                      <option key={c.value} value={c.value}>{c.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ERP System <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={selectedErp}
                    onChange={(e) => handleErpChange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    <option value="">Select ERP...</option>
                    {erpSources.map(e => (
                      <option key={e.value} value={e.value}>{e.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* ERP Template Info */}
              {erpTemplate && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm">
                  <p className="font-medium text-blue-800">
                    {erpTemplate.display_name} Format
                  </p>
                  <p className="text-blue-600 text-xs mt-1">
                    Expected columns: {erpTemplate.columns.join(', ')}
                  </p>
                  <p className="text-blue-600 text-xs">
                    Required: {erpTemplate.required_columns.join(', ')}
                  </p>
                </div>
              )}

              {/* File Upload Buttons */}
              <div className="flex gap-4">
                <button
                  onClick={downloadTemplate}
                  disabled={!selectedErp}
                  className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Download className="h-4 w-4" />
                  Download {selectedErp ? erpTemplate?.display_name || 'ERP' : ''} Template
                </button>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={!selectedErp}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Upload className="h-4 w-4" />
                  Select CSV File
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>

              {/* Preview Table */}
              {preview.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">
                    Preview ({csvData.length} sites found)
                  </h3>
                  <div className="overflow-x-auto border rounded-lg">
                    <table className="min-w-full text-xs">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 py-2 text-left">Code</th>
                          <th className="px-3 py-2 text-left">Name</th>
                          <th className="px-3 py-2 text-left">Tank Cap</th>
                          <th className="px-3 py-2 text-left">Consumption</th>
                          <th className="px-3 py-2 text-left">Threshold</th>
                          <th className="px-3 py-2 text-left">Service Type</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {preview.map((row, idx) => (
                          <tr key={idx}>
                            <td className="px-3 py-2 font-medium">{row.consignee_code}</td>
                            <td className="px-3 py-2">{row.consignee_name || '-'}</td>
                            <td className="px-3 py-2">{row.tank_capacity || '-'}</td>
                            <td className="px-3 py-2">{row.consumption_rate || '-'}</td>
                            <td className="px-3 py-2">{row.runout_threshold_hours || '-'}</td>
                            <td className="px-3 py-2">
                              {row.service_type ? (
                                <span className={`px-2 py-0.5 rounded text-xs ${
                                  row.service_type === 'inventory_and_tracking'
                                    ? 'bg-purple-100 text-purple-700'
                                    : 'bg-gray-100 text-gray-700'
                                }`}>
                                  {row.service_type.replace(/_/g, ' ')}
                                </span>
                              ) : '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  {csvData.length > 5 && (
                    <p className="text-xs text-gray-500 mt-1">...and {csvData.length - 5} more</p>
                  )}
                </div>
              )}

              {/* Upload Button */}
              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleUpload}
                  disabled={!canUpload}
                  className="flex-1 flex items-center justify-center gap-2 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  {isUploading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
                  Upload {csvData?.length || 0} Sites to {selectedCustomer ? customers.find(c => c.value === selectedCustomer)?.label : ''}
                </button>
                <button
                  onClick={onClose}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
              </div>

              {/* Validation Message */}
              {(!selectedCustomer || !selectedErp) && (
                <p className="text-xs text-amber-600 text-center">
                  Please select both Customer and ERP System before uploading
                </p>
              )}
            </>
          ) : (
            <div className="text-center py-4">
              {result.error ? (
                <div className="text-red-600">
                  <X className="h-12 w-12 mx-auto mb-2" />
                  <p className="font-medium">Upload Failed</p>
                  <p className="text-sm">{result.error}</p>
                </div>
              ) : (
                <div className="text-green-600">
                  <CheckCircle className="h-12 w-12 mx-auto mb-2" />
                  <p className="font-medium">Upload Complete</p>
                  <p className="text-sm">{result.updated} sites updated for {customers.find(c => c.value === selectedCustomer)?.label}</p>
                  {result.not_found?.length > 0 && (
                    <p className="text-xs text-amber-600 mt-2">
                      {result.not_found.length} codes not found: {result.not_found.slice(0, 3).join(', ')}
                      {result.not_found.length > 3 && '...'}
                    </p>
                  )}
                </div>
              )}
              <button
                onClick={onClose}
                className="mt-4 px-6 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
              >
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ============== Agent Site Assignment Modal ==============
function AgentAssignmentModal({ agent, sites, onClose, onSave }) {
  const [selectedSites, setSelectedSites] = useState(
    new Set(sites?.filter(s => s.assigned_agent_id === agent?.id).map(s => s.id) || [])
  )
  const [isSaving, setIsSaving] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  if (!agent) return null

  const filteredSites = sites?.filter(site =>
    site.consignee_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    site.consignee_name.toLowerCase().includes(searchTerm.toLowerCase())
  ) || []

  const toggleSite = (siteId) => {
    const newSelected = new Set(selectedSites)
    if (newSelected.has(siteId)) {
      newSelected.delete(siteId)
    } else {
      newSelected.add(siteId)
    }
    setSelectedSites(newSelected)
  }

  const selectAll = () => {
    setSelectedSites(new Set(filteredSites.map(s => s.id)))
  }

  const selectNone = () => {
    setSelectedSites(new Set())
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await onSave(agent.id, Array.from(selectedSites))
      onClose()
    } catch (error) {
      console.error('Error assigning sites:', error)
    }
    setIsSaving(false)
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full mx-4 overflow-hidden max-h-[80vh] flex flex-col">
        <div className="p-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white">
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-3">
              <Bot className="h-6 w-6" />
              <div>
                <h2 className="font-bold">Assign Sites to {agent.agent_name}</h2>
                <p className="text-sm text-purple-200">{selectedSites.size} sites selected</p>
              </div>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-white/20 rounded">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        <div className="p-4 border-b">
          <input
            type="text"
            placeholder="Search sites..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg text-sm"
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={selectAll}
              className="text-xs text-blue-600 hover:underline"
            >
              Select All
            </button>
            <button
              onClick={selectNone}
              className="text-xs text-gray-600 hover:underline"
            >
              Clear All
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {filteredSites.map(site => {
              const isSelected = selectedSites.has(site.id)
              const isAtRisk = site.hours_to_runout && site.hours_to_runout < 48

              return (
                <div
                  key={site.id}
                  onClick={() => toggleSite(site.id)}
                  className={`p-3 rounded-lg border-2 cursor-pointer transition ${
                    isSelected
                      ? 'border-purple-500 bg-purple-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => {}}
                      className="h-4 w-4 text-purple-600 rounded"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{site.consignee_code}</p>
                      <p className="text-xs text-gray-500 truncate">{site.consignee_name}</p>
                    </div>
                    {isAtRisk && (
                      <span className="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded-full">
                        {site.hours_to_runout?.toFixed(0)}h
                      </span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="p-4 border-t bg-gray-50 flex gap-3">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex-1 flex items-center justify-center gap-2 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition"
          >
            {isSaving ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Users className="h-4 w-4" />}
            Assign {selectedSites.size} Sites
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}

// ============== Google Sheets Sync Panel ==============
function GoogleSheetsPanel({ sites, loads }) {
  const [sheetUrl, setSheetUrl] = useState(localStorage.getItem('sheetsUrl') || '')
  const [isSyncing, setIsSyncing] = useState(false)
  const [lastSync, setLastSync] = useState(localStorage.getItem('lastSync') || null)

  const handleSync = async () => {
    if (!sheetUrl) return

    setIsSyncing(true)
    localStorage.setItem('sheetsUrl', sheetUrl)

    try {
      // Call backend to sync with Google Sheets
      const result = await syncToSheets(sheetUrl, sites, loads)

      if (result.success) {
        const now = new Date().toLocaleString()
        setLastSync(now)
        localStorage.setItem('lastSync', now)
      }
    } catch (error) {
      console.error('Sync error:', error)
    }

    setIsSyncing(false)
  }

  const exportToCsv = () => {
    // Generate CSV of current status
    const headers = ['Site Code', 'Site Name', 'Inventory (gal)', 'Hours to Runout', 'Status', 'Active Loads']
    const rows = sites?.map(site => {
      const status = site.hours_to_runout < 12 ? 'CRITICAL' :
        site.hours_to_runout < 24 ? 'HIGH RISK' :
        site.hours_to_runout < 48 ? 'AT RISK' : 'OK'
      const activeLoads = loads?.filter(l => l.destination_site_id === site.id).length || 0
      return [
        site.consignee_code,
        site.consignee_name,
        site.current_inventory,
        site.hours_to_runout?.toFixed(1),
        status,
        activeLoads
      ]
    }) || []

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `fuel-status-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
      <div className="px-5 py-4 bg-slate-50 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <FileSpreadsheet className="h-5 w-5 text-slate-600" />
          <h3 className="text-base font-semibold text-slate-900">Google Sheets Dashboard</h3>
        </div>
      </div>

      <div className="p-4 space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Spreadsheet URL
          </label>
          <input
            type="url"
            value={sheetUrl}
            onChange={(e) => setSheetUrl(e.target.value)}
            placeholder="https://docs.google.com/spreadsheets/d/..."
            className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-slate-500 focus:border-transparent"
          />
          <p className="text-xs text-slate-400 mt-1">
            Share the sheet with the service account email
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleSync}
            disabled={!sheetUrl || isSyncing}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 disabled:opacity-50 transition"
          >
            {isSyncing ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Sync to Sheets
          </button>

          <button
            onClick={exportToCsv}
            className="flex items-center gap-2 px-4 py-2 border border-slate-200 rounded-lg hover:bg-slate-50 transition text-slate-600"
          >
            <Download className="h-4 w-4" />
            Export CSV
          </button>
        </div>

        {lastSync && (
          <p className="text-xs text-slate-400 text-center">
            Last synced: {lastSync}
          </p>
        )}

        {sheetUrl && (
          <a
            href={sheetUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 text-sm text-green-600 hover:text-green-700"
          >
            <ExternalLink className="h-4 w-4" />
            Open Spreadsheet
          </a>
        )}
      </div>
    </div>
  )
}

// ============== Agent Monitor Tab (HITL) ==============
function AgentMonitorTab({ agents, sites, emails, onViewEmail, onManageSites }) {
  const queryClient = useQueryClient()
  const [selectedAgentId, setSelectedAgentId] = useState(null)
  const [activityFilter, setActivityFilter] = useState('all')
  const [showRunHistory, setShowRunHistory] = useState(true)
  const [expandedRunId, setExpandedRunId] = useState(null)
  const [statusSummary, setStatusSummary] = useState(null)

  const statusSummaryMutation = useMutation({
    mutationFn: getStatusSummary,
    onSuccess: (data) => setStatusSummary(data.summary)
  })

  // Fetch run history for all agents
  const { data: runHistory, isLoading: runHistoryLoading } = useQuery({
    queryKey: ['agent-run-history'],
    queryFn: () => getRecentRunHistory(30),
    refetchInterval: 30000 // Refresh every 30 seconds
  })

  const { data: allActivities } = useQuery({
    queryKey: ['all-activities'],
    queryFn: async () => {
      const activities = await getAllActivities(100)
      // Enrich with agent info
      return (activities || []).map(act => ({
        ...act,
        agent: (agents || []).find(a => a.id === act.agent_id) || null
      }))
    },
    refetchInterval: 15000,
  })

  const runCheckMutation = useMutation({
    mutationFn: runAgentCheck,
    onSuccess: () => {
      queryClient.invalidateQueries()
    }
  })

  const filteredActivities = useMemo(() => {
    let activities = allActivities || []

    if (selectedAgentId) {
      activities = activities.filter(a => a.agent_id === selectedAgentId)
    }

    if (activityFilter !== 'all') {
      activities = activities.filter(a => a.activity_type === activityFilter)
    }

    return activities
  }, [allActivities, selectedAgentId, activityFilter])

  const getActivityIcon = (type) => {
    switch (type) {
      case 'email_sent': return <Send className="h-4 w-4 text-blue-600" />
      case 'email_received': return <Mail className="h-4 w-4 text-emerald-600" />
      case 'eta_updated': return <Clock className="h-4 w-4 text-cyan-600" />
      case 'escalation_created': return <AlertTriangle className="h-4 w-4 text-red-600" />
      case 'observation': return <Eye className="h-4 w-4 text-gray-600" />
      case 'check_started': return <Play className="h-4 w-4 text-green-600" />
      case 'check_completed': return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'inventory_checked': return <Fuel className="h-4 w-4 text-amber-600" />
      default: return <Activity className="h-4 w-4 text-gray-600" />
    }
  }

  const getActivityStyles = (type) => {
    switch (type) {
      case 'email_sent': return 'border-l-blue-500 bg-blue-50'
      case 'email_received': return 'border-l-emerald-500 bg-emerald-50'
      case 'eta_updated': return 'border-l-cyan-500 bg-cyan-50'
      case 'escalation_created': return 'border-l-red-500 bg-red-50'
      case 'check_started': return 'border-l-green-500 bg-green-50'
      case 'check_completed': return 'border-l-green-500 bg-green-50'
      case 'inventory_checked': return 'border-l-amber-500 bg-amber-50'
      default: return 'border-l-gray-300 bg-gray-50'
    }
  }

  return (
    <div className="space-y-6">
      {/* Agent Status Strip */}
      <div className="space-y-2">
        {agents?.map(agent => {
          const agentSites = sites?.filter(s => s.assigned_agent_id === agent.id) || []
          const criticalSites = agentSites.filter(s => s.hours_to_runout < 24)
          const recentActivities = (allActivities || []).filter(a => a.agent_id === agent.id).slice(0, 5)

          return (
            <div
              key={agent.id}
              className={`bg-white rounded-lg border border-slate-200 px-4 py-3 flex items-center gap-4 cursor-pointer hover:shadow-sm transition ${
                selectedAgentId === agent.id ? 'ring-2 ring-purple-500' : ''
              }`}
              onClick={() => setSelectedAgentId(selectedAgentId === agent.id ? null : agent.id)}
            >
              {/* Agent identity */}
              <div className="flex items-center gap-3 min-w-[200px]">
                <div className="p-2 bg-purple-600 rounded-lg">
                  <Bot className="h-4 w-4 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-slate-900">{agent.agent_name}</h3>
                  <div className="flex items-center gap-1.5">
                    <div className={`w-2 h-2 rounded-full ${
                      agent.status === 'active' ? 'bg-emerald-500 animate-pulse' : 'bg-slate-300'
                    }`} />
                    <span className="text-xs text-slate-500">{agent.persona_type}</span>
                  </div>
                </div>
              </div>

              {/* Stats */}
              <div className="flex items-center gap-6 flex-1">
                <div className="text-center">
                  <p className="text-lg font-bold text-slate-900">{agentSites.length}</p>
                  <p className="text-[10px] text-slate-400 uppercase tracking-wide">Sites</p>
                </div>
                <div className="text-center">
                  <p className={`text-lg font-bold ${criticalSites.length > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                    {criticalSites.length}
                  </p>
                  <p className="text-[10px] text-slate-400 uppercase tracking-wide">Critical</p>
                </div>

                {/* Last activity */}
                {recentActivities.length > 0 && (
                  <div className="flex items-center gap-2 text-xs text-slate-500 ml-4 border-l pl-4 border-slate-200">
                    {getActivityIcon(recentActivities[0].activity_type)}
                    <span>{recentActivities[0].activity_type.replace(/_/g, ' ')}</span>
                    <span className="text-slate-400">
                      {new Date(recentActivities[0].created_at).toLocaleTimeString()}
                    </span>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    runCheckMutation.mutate(agent.id)
                  }}
                  disabled={runCheckMutation.isPending}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-purple-600 text-white text-xs font-medium rounded-md hover:bg-purple-700 disabled:opacity-50 transition"
                >
                  {runCheckMutation.isPending ? (
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Zap className="h-3.5 w-3.5" />
                  )}
                  Run Check
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onManageSites?.(agent)
                  }}
                  className="flex items-center gap-1 px-2 py-1.5 border border-slate-200 text-slate-500 text-xs rounded-md hover:bg-slate-50 transition"
                  title="Manage assigned sites"
                >
                  <Users className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {/* Status Update */}
      <div className="bg-white rounded-lg border border-slate-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-slate-600" />
            <h3 className="text-sm font-semibold text-slate-800">Executive Summary</h3>
          </div>
          <button
            onClick={() => statusSummaryMutation.mutate()}
            disabled={statusSummaryMutation.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-slate-800 text-white rounded-lg hover:bg-slate-700 disabled:opacity-50 transition"
          >
            {statusSummaryMutation.isPending ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Zap className="h-3.5 w-3.5" />
            )}
            Generate Update
          </button>
        </div>
        {statusSummary && (
          <div className="mt-3 bg-slate-50 rounded-lg p-4 border border-slate-100">
            <pre className="text-sm text-slate-700 whitespace-pre-wrap font-sans leading-relaxed">{statusSummary}</pre>
            <div className="mt-2 text-[11px] text-slate-400 text-right">Generated from live data + knowledge graph</div>
          </div>
        )}
      </div>

      {/* Run History Panel */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <div
          className="px-5 py-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between cursor-pointer"
          onClick={() => setShowRunHistory(!showRunHistory)}
        >
          <div className="flex items-center gap-2">
            <History className="h-5 w-5 text-slate-600" />
            <h3 className="text-base font-semibold text-slate-900">Agent Run History</h3>
            <span className="ml-2 px-2 py-0.5 bg-slate-200 text-slate-600 rounded-full text-xs">
              {runHistory?.length || 0} runs
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation()
                if (!runHistory?.length) return
                // Convert to CSV
                const headers = ['ID', 'Agent', 'Started At', 'Duration (s)', 'Status', 'Mode', 'Sites', 'Loads', 'Emails', 'Escalations', 'API Calls', 'Tokens']
                const rows = runHistory.map(run => [
                  run.id,
                  agents?.find(a => a.id === run.agent_id)?.agent_name || run.agent_id,
                  new Date(run.started_at).toISOString(),
                  run.duration_seconds?.toFixed(1) || '',
                  run.status,
                  run.execution_mode,
                  run.sites_checked || 0,
                  run.loads_checked || 0,
                  run.emails_sent || 0,
                  run.escalations_created || 0,
                  run.api_calls || 0,
                  run.tokens_used || 0
                ])
                const csv = [headers, ...rows].map(row => row.join(',')).join('\n')
                const blob = new Blob([csv], { type: 'text/csv' })
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `agent-run-history-${new Date().toISOString().split('T')[0]}.csv`
                a.click()
                URL.revokeObjectURL(url)
              }}
              className="p-1.5 text-slate-500 hover:bg-slate-200 rounded"
              title="Export to CSV"
            >
              <Download className="h-4 w-4" />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); queryClient.invalidateQueries(['agent-run-history']) }}
              className="p-1.5 text-slate-500 hover:bg-slate-200 rounded"
              title="Refresh"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
            {showRunHistory ? <ChevronUp className="h-5 w-5 text-slate-500" /> : <ChevronDown className="h-5 w-5 text-slate-500" />}
          </div>
        </div>

        {showRunHistory && (
          <div className="max-h-[400px] overflow-y-auto">
            {runHistoryLoading ? (
              <div className="p-8 text-center text-slate-400">
                <RefreshCw className="h-6 w-6 mx-auto mb-2 animate-spin text-slate-400" />
                <p className="text-sm">Loading run history...</p>
              </div>
            ) : !runHistory?.length ? (
              <div className="p-8 text-center text-slate-400 text-sm">
                <History className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No agent runs recorded yet.</p>
                <p className="text-sm mt-1">Run an agent check to see execution metrics.</p>
              </div>
            ) : (
              <div className="divide-y">
                {runHistory.map((run) => {
                  const agent = agents?.find(a => a.id === run.agent_id)
                  const statusColors = {
                    running: 'bg-blue-100 text-blue-700 border-blue-300',
                    completed: 'bg-green-100 text-green-700 border-green-300',
                    failed: 'bg-red-100 text-red-700 border-red-300',
                    timeout: 'bg-orange-100 text-orange-700 border-orange-300'
                  }

                  const isExpanded = expandedRunId === run.id

                  return (
                    <div
                      key={run.id}
                      className={`p-4 cursor-pointer transition ${isExpanded ? 'bg-slate-50' : 'hover:bg-gray-50'}`}
                      onClick={() => setExpandedRunId(isExpanded ? null : run.id)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            run.status === 'completed' ? 'bg-green-100' :
                            run.status === 'running' ? 'bg-blue-100' :
                            run.status === 'failed' ? 'bg-red-100' : 'bg-gray-100'
                          }`}>
                            {run.status === 'running' ? (
                              <RefreshCw className="h-5 w-5 text-blue-600 animate-spin" />
                            ) : run.status === 'completed' ? (
                              <CheckCircle className="h-5 w-5 text-green-600" />
                            ) : run.status === 'failed' ? (
                              <XCircle className="h-5 w-5 text-red-600" />
                            ) : (
                              <Clock className="h-5 w-5 text-orange-600" />
                            )}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-gray-900">
                                {agent?.agent_name || `Agent #${run.agent_id}`}
                              </span>
                              <span className={`px-2 py-0.5 text-xs font-medium rounded border ${statusColors[run.status] || statusColors.completed}`}>
                                {run.status?.toUpperCase()}
                              </span>
                              <span className={`px-2 py-0.5 text-xs rounded ${
                                run.execution_mode === 'full_auto' ? 'bg-green-100 text-green-700' :
                                run.execution_mode === 'auto_email' ? 'bg-blue-100 text-blue-700' :
                                'bg-gray-100 text-gray-700'
                              }`}>
                                {run.execution_mode?.replace(/_/g, ' ')}
                              </span>
                            </div>
                            <p className="text-sm text-gray-500 mt-0.5">
                              Started {new Date(run.started_at).toLocaleString()}
                              {run.duration_seconds && ` • ${run.duration_seconds.toFixed(1)}s`}
                              {run.decisions?.length > 0 && ` • ${run.decisions.length} decision(s)`}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {/* Compact metrics */}
                          <div className="flex items-center gap-3 text-xs text-slate-500">
                            <span>{run.sites_checked || 0} sites</span>
                            <span>{run.loads_checked || 0} loads</span>
                            {(run.emails_sent || 0) > 0 && <span className="text-blue-600">{run.emails_sent} emails</span>}
                            {(run.escalations_created || 0) > 0 && <span className="text-red-600">{run.escalations_created} escalations</span>}
                          </div>
                          {isExpanded ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
                        </div>
                      </div>

                      {/* Expanded Details */}
                      {isExpanded && (
                        <div className="mt-3 ml-13 space-y-3" onClick={(e) => e.stopPropagation()}>
                          {/* Run Metrics Grid */}
                          <div className="grid grid-cols-6 gap-2">
                            <div className="text-center p-2 bg-gray-50 rounded">
                              <p className="text-lg font-bold text-gray-900">{run.sites_checked || 0}</p>
                              <p className="text-xs text-gray-500">Sites</p>
                            </div>
                            <div className="text-center p-2 bg-gray-50 rounded">
                              <p className="text-lg font-bold text-gray-900">{run.loads_checked || 0}</p>
                              <p className="text-xs text-gray-500">Loads</p>
                            </div>
                            <div className="text-center p-2 bg-blue-50 rounded">
                              <p className="text-lg font-bold text-blue-600">{run.emails_sent || 0}</p>
                              <p className="text-xs text-gray-500">Emails</p>
                            </div>
                            <div className="text-center p-2 bg-red-50 rounded">
                              <p className="text-lg font-bold text-red-600">{run.escalations_created || 0}</p>
                              <p className="text-xs text-gray-500">Escalations</p>
                            </div>
                            <div className="text-center p-2 bg-purple-50 rounded">
                              <p className="text-lg font-bold text-purple-600">{run.api_calls || 0}</p>
                              <p className="text-xs text-gray-500">API Calls</p>
                            </div>
                            <div className="text-center p-2 bg-amber-50 rounded">
                              <p className="text-lg font-bold text-amber-600">{run.tokens_used || 0}</p>
                              <p className="text-xs text-gray-500">Tokens</p>
                            </div>
                          </div>

                          {/* Error Message */}
                          {run.error_message && (
                            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                              <span className="font-medium">Error:</span> {run.error_message}
                            </div>
                          )}

                          {/* Decisions Detail */}
                          {run.decisions?.length > 0 && (
                            <div className="space-y-2">
                              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Decisions Made</h4>
                              {run.decisions.map((decision, idx) => (
                                <div key={idx} className="flex items-start gap-3 p-3 bg-white border border-slate-200 rounded-lg">
                                  <div className={`mt-0.5 p-1.5 rounded ${
                                    decision.type === 'escalation_created' ? 'bg-red-100' :
                                    decision.type === 'email_sent' ? 'bg-blue-100' :
                                    'bg-slate-100'
                                  }`}>
                                    {decision.type === 'escalation_created' ? (
                                      <AlertTriangle className="h-3.5 w-3.5 text-red-600" />
                                    ) : decision.type === 'email_sent' ? (
                                      <Send className="h-3.5 w-3.5 text-blue-600" />
                                    ) : (
                                      <Eye className="h-3.5 w-3.5 text-slate-600" />
                                    )}
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                      <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                                        decision.type === 'escalation_created' ? 'bg-red-100 text-red-700' :
                                        decision.type === 'email_sent' ? 'bg-blue-100 text-blue-700' :
                                        'bg-slate-100 text-slate-700'
                                      }`}>
                                        {decision.type?.replace(/_/g, ' ')}
                                      </span>
                                    </div>
                                    <p className="mt-1 text-sm text-slate-700 leading-relaxed">
                                      {decision.summary}
                                    </p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}

                          {/* No decisions message */}
                          {(!run.decisions || run.decisions.length === 0) && !run.error_message && (
                            <p className="text-sm text-slate-400 italic">No notable decisions recorded for this run.</p>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Activity Stream */}
      <div className="bg-white rounded-xl shadow-lg overflow-hidden">
        <div className="px-6 py-4 bg-gradient-to-r from-gray-800 to-gray-900 text-white flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="h-6 w-6" />
            <h3 className="text-lg font-bold">Agent Activity Stream</h3>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={selectedAgentId || ''}
              onChange={(e) => setSelectedAgentId(e.target.value ? parseInt(e.target.value) : null)}
              className="text-sm bg-gray-700 border-gray-600 rounded px-2 py-1 text-white"
            >
              <option value="">All Agents</option>
              {agents?.map(a => (
                <option key={a.id} value={a.id}>{a.agent_name}</option>
              ))}
            </select>
            <select
              value={activityFilter}
              onChange={(e) => setActivityFilter(e.target.value)}
              className="text-sm bg-gray-700 border-gray-600 rounded px-2 py-1 text-white"
            >
              <option value="all">All Types</option>
              <option value="email_sent">Emails Sent</option>
              <option value="email_received">Emails Received</option>
              <option value="eta_updated">ETA Updated</option>
              <option value="escalation_created">Escalations</option>
              <option value="inventory_checked">Inventory Checked</option>
            </select>
          </div>
        </div>

        <div className="max-h-[500px] overflow-y-auto">
          {filteredActivities.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <History className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No activities yet. Run an agent check to see activity.</p>
            </div>
          ) : (
            <div className="divide-y">
              {filteredActivities.map((activity) => {
                const d = activity.details || {}
                const getDescription = () => {
                  switch (activity.activity_type) {
                    case 'email_sent':
                      return `Sent ETA request to ${d.to || d.carrier_name || 'carrier'}${d.po_number ? ` for ${d.po_number}` : ''}`
                    case 'email_received':
                      return `Received reply from ${d.from_email || 'carrier'}${d.po_number ? ` for ${d.po_number}` : ''}${d.parse_success ? ` — ETA parsed: ${d.parsed_eta ? new Date(d.parsed_eta).toLocaleString() : ''}` : ' — needs review'}`
                    case 'eta_updated':
                      return d.message || 'ETA updated'
                    case 'escalation_created':
                      return d.description || 'Escalation created'
                    case 'inventory_checked':
                      return d.message || 'Inventory checked'
                    default:
                      return d.message || d.description || activity.activity_type.replace(/_/g, ' ')
                  }
                }
                return (
                <div
                  key={activity.id}
                  className={`p-4 border-l-4 ${getActivityStyles(activity.activity_type)} hover:bg-opacity-75 transition`}
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 mt-1">
                      {getActivityIcon(activity.activity_type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-gray-900 text-sm">
                          {activity.activity_type.replace(/_/g, ' ').toUpperCase()}
                        </span>
                        {activity.agent && (
                          <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full">
                            {activity.agent.agent_name}
                          </span>
                        )}
                        {!activity.agent_id && (
                          <span className="text-xs px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full">
                            System
                          </span>
                        )}
                        {d.po_number && (
                          <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                            {d.po_number}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {getDescription()}
                      </p>
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <p className="text-xs text-gray-500">
                        {new Date(activity.created_at).toLocaleDateString()}
                      </p>
                      <p className="text-xs font-medium text-gray-700">
                        {new Date(activity.created_at).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
              )})}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ============== Agent Management Panel ==============
function AgentManagementPanel({ agents, sites }) {
  const queryClient = useQueryClient()
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [showActivities, setShowActivities] = useState(false)

  const { data: activities } = useQuery({
    queryKey: ['agent-activities', selectedAgent],
    queryFn: () => getAgentActivities(selectedAgent),
    enabled: !!selectedAgent && showActivities
  })

  const runCheckMutation = useMutation({
    mutationFn: runAgentCheck,
    onSuccess: () => {
      queryClient.invalidateQueries()
    }
  })

  const updateModeMutation = useMutation({
    mutationFn: ({ agentId, executionMode }) => updateAgent(agentId, { execution_mode: executionMode }),
    onSuccess: () => {
      queryClient.invalidateQueries(['agents'])
    }
  })

  const getAgentSites = (agentId) => {
    return sites?.filter(s => s.assigned_agent_id === agentId) || []
  }

  const getExecutionModeLabel = (mode) => {
    switch (mode) {
      case 'draft_only': return 'Draft Only'
      case 'auto_email': return 'Auto Email'
      case 'full_auto': return 'Full Auto'
      default: return mode
    }
  }

  const getExecutionModeColor = (mode) => {
    switch (mode) {
      case 'draft_only': return 'bg-gray-100 text-gray-700 border-gray-300'
      case 'auto_email': return 'bg-blue-100 text-blue-700 border-blue-300'
      case 'full_auto': return 'bg-green-100 text-green-700 border-green-300'
      default: return 'bg-gray-100 text-gray-700 border-gray-300'
    }
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
      <div className="px-5 py-4 bg-slate-50 border-b border-slate-100">
        <div className="flex items-center gap-2 text-slate-900">
          <Bot className="h-5 w-5 text-slate-600" />
          <h3 className="text-base font-semibold">AI Agent Control</h3>
        </div>
      </div>

      <div className="p-4 space-y-3">
        {agents?.map((agent) => {
          const agentSites = getAgentSites(agent.id)
          const isSelected = selectedAgent === agent.id

          return (
            <div key={agent.id} className="border border-slate-200 rounded-lg overflow-hidden">
              <div
                className={`p-4 cursor-pointer transition ${isSelected ? 'bg-slate-50' : 'hover:bg-slate-50'}`}
                onClick={() => setSelectedAgent(isSelected ? null : agent.id)}
              >
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-3">
                    <div className={`w-2.5 h-2.5 rounded-full ${
                      agent.status === 'active' ? 'bg-emerald-500' : 'bg-slate-300'
                    }`} />
                    <div>
                      <h4 className="font-medium text-slate-900">{agent.agent_name}</h4>
                      <p className="text-xs text-slate-500">
                        {agentSites.length} sites assigned • {agent.status}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {/* Execution Mode Dropdown */}
                    <select
                      value={agent.execution_mode || 'draft_only'}
                      onChange={(e) => {
                        e.stopPropagation()
                        updateModeMutation.mutate({ agentId: agent.id, executionMode: e.target.value })
                      }}
                      onClick={(e) => e.stopPropagation()}
                      className={`text-xs font-medium px-2 py-1 rounded border cursor-pointer ${getExecutionModeColor(agent.execution_mode)}`}
                      title="Execution Mode - Controls agent autonomy level"
                    >
                      <option value="draft_only">Draft Only (Safe)</option>
                      <option value="auto_email">Auto Email</option>
                      <option value="full_auto">Full Auto</option>
                    </select>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setShowActivities(!showActivities)
                        setSelectedAgent(agent.id)
                      }}
                      className="p-2 text-gray-500 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition"
                      title="View Activities"
                    >
                      <Activity className="h-5 w-5" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        runCheckMutation.mutate(agent.id)
                      }}
                      disabled={runCheckMutation.isPending}
                      className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition"
                    >
                      {runCheckMutation.isPending ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                      Run Check
                    </button>
                  </div>
                </div>

                {agentSites.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {agentSites.map(site => (
                      <span
                        key={site.id}
                        className={`px-2 py-1 text-xs rounded-full ${
                          site.hours_to_runout < 24
                            ? 'bg-red-100 text-red-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {site.consignee_code}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {isSelected && showActivities && activities && (
                <div className="border-t bg-gray-50 p-4 max-h-64 overflow-y-auto">
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Recent Activities</h5>
                  {activities.length === 0 ? (
                    <p className="text-sm text-gray-500">No activities yet</p>
                  ) : (
                    <div className="space-y-2">
                      {activities.slice(0, 15).map((act) => (
                        <div key={act.id} className="flex items-start gap-2 text-xs">
                          <span className={`px-2 py-0.5 rounded-full font-medium ${
                            act.activity_type === 'email_sent' ? 'bg-blue-100 text-blue-700' :
                            act.activity_type === 'escalation_created' ? 'bg-red-100 text-red-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {act.activity_type.replace(/_/g, ' ')}
                          </span>
                          <span className="text-gray-500">
                            {new Date(act.created_at).toLocaleTimeString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ============== Load Details Sidebar ==============
function LoadDetailsSidebar({ load: initialLoad, onClose }) {
  if (!initialLoad) return null

  // BYPASS CACHE - Fetch fresh data directly from API
  const [freshLoad, setFreshLoad] = useState(initialLoad)

  useEffect(() => {
    // Fetch fresh data on mount
    fetch('http://localhost:8000/api/loads/active')
      .then(res => res.json())
      .then(loads => {
        const fresh = loads.find(l => l.id === initialLoad.id)
        console.log('🔥 FRESH LOAD DATA FROM API:', {
          po: fresh?.po_number,
          tracking_count: fresh?.tracking_points?.length,
          origin: fresh?.origin_address,
          dest: fresh?.destination_address,
          raw: fresh
        })
        if (fresh) {
          setFreshLoad(fresh)
        }
      })
      .catch(err => console.error('Failed to fetch fresh load:', err))
  }, [initialLoad.id])

  const load = freshLoad

  // Debug: Log tracking data
  useEffect(() => {
    console.log('LoadDetailsSidebar - Load Data:', {
      po_number: load.po_number,
      status: load.status,
      tracking_points_count: load.tracking_points?.length || 0,
      has_tracking_points: !!load.tracking_points,
      first_point: load.tracking_points?.[0],
      origin_address: load.origin_address,
      destination_address: load.destination_address,
      all_load_keys: Object.keys(load)
    })
  }, [load])

  // Fix Leaflet default icon issue
  useEffect(() => {
    delete L.Icon.Default.prototype._getIconUrl
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    })
  }, [])

  // Calculate center point between origin and destination
  const getMapCenter = () => {
    if (load.tracking_points?.length > 0) {
      const lastPoint = load.tracking_points[load.tracking_points.length - 1]
      return [lastPoint.lat, lastPoint.lng]
    }
    return [33.7490, -84.3880] // Default to Atlanta
  }

  const getStatusColor = () => {
    switch (load.status) {
      case 'in_transit': return 'text-blue-600 bg-blue-100'
      case 'scheduled': return 'text-gray-600 bg-gray-100'
      case 'delayed': return 'text-red-600 bg-red-100'
      case 'delivered': return 'text-green-600 bg-green-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const formatDate = (date) => {
    if (!date) return 'N/A'
    return new Date(date).toLocaleString()
  }

  // Create route line from tracking points
  const routeLine = load.tracking_points?.map(p => [p.lat, p.lng]) || []

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-30 z-40 animate-fadeIn"
        onClick={onClose}
      />

      {/* Sidebar */}
      <div className="fixed right-0 top-0 h-full w-1/3 bg-white shadow-2xl z-50 flex flex-col animate-slideInRight">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-cyan-600 text-white p-6 flex-shrink-0 z-20">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-2xl font-bold">Load Details</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition"
            >
              <X className="h-6 w-6" />
            </button>
          </div>
          <div className="flex items-center gap-3 mb-3">
            <p className="text-blue-100 text-lg font-mono">{load.po_number}</p>
            {load.destination_site?.customer && (
              <span className={`px-2.5 py-1 text-xs font-semibold rounded border ${
                load.destination_site.customer === 'stark_industries'
                  ? 'bg-red-100 text-red-700 border-red-200'
                  : load.destination_site.customer === 'wayne_enterprises'
                  ? 'bg-gray-800 text-white border-gray-900'
                  : 'bg-green-100 text-green-700 border-green-200'
              }`}>
                {load.destination_site.customer === 'stark_industries' ? 'Stark' :
                 load.destination_site.customer === 'wayne_enterprises' ? 'Wayne' :
                 'Luthor'}
              </span>
            )}
          </div>
          <div>
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor()}`}>
              {load.status?.replace(/_/g, ' ').toUpperCase()}
            </span>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Current Status & ETA */}
          <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-5 border border-blue-200">
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Clock className="h-5 w-5 text-blue-600" />
              Current Status
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Current ETA:</span>
                <span className="font-bold text-gray-900">{formatDate(load.current_eta)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Last Update:</span>
                <span className="text-sm text-gray-500">{formatDate(load.last_eta_update)}</span>
              </div>
              {load.shipped_at && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Shipped:</span>
                  <span className="text-sm text-gray-500">{formatDate(load.shipped_at)}</span>
                </div>
              )}
            </div>
          </div>

          {/* Route Map */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <h3 className="font-bold text-gray-900 flex items-center gap-2">
                <MapPin className="h-5 w-5 text-green-600" />
                Route Tracking {load.tracking_points?.length > 0 && `(${load.tracking_points.length} points)`}
              </h3>
            </div>
            {load.tracking_points?.length > 0 ? (
              <div className="h-64" style={{ position: 'relative', zIndex: 1 }}>
                <MapContainer
                  key={load.id}
                  center={getMapCenter()}
                  zoom={6}
                  style={{ height: '100%', width: '100%', zIndex: 1 }}
                  scrollWheelZoom={false}
                >
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  />

                  {/* Route line */}
                  {routeLine.length > 0 && (
                    <Polyline positions={routeLine} color="blue" weight={3} opacity={0.7} />
                  )}

                  {/* Tracking points */}
                  {load.tracking_points.map((point, idx) => (
                    <Marker key={idx} position={[point.lat, point.lng]}>
                      <Popup>
                        <div className="text-sm">
                          <p className="font-bold">Tracking Point {idx + 1}</p>
                          <p>Time: {new Date(point.timestamp).toLocaleString()}</p>
                          <p>Speed: {point.speed} mph</p>
                        </div>
                      </Popup>
                    </Marker>
                  ))}
                </MapContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center bg-gray-50">
                <div className="text-center text-gray-500">
                  <MapPin className="h-12 w-12 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">No tracking data available yet</p>
                </div>
              </div>
            )}
          </div>

          {/* Origin & Destination */}
          <div className="space-y-3">
            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-green-600 rounded-lg">
                  <Navigation className="h-5 w-5 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">Origin</p>
                  <p className="text-sm text-gray-600">{load.origin_terminal}</p>
                  <p className="text-xs text-gray-500 mt-1">{load.origin_address || 'Address not available'}</p>
                </div>
              </div>
            </div>

            <div className="flex justify-center">
              <ArrowRight className="h-6 w-6 text-gray-400" />
            </div>

            <div className="bg-red-50 rounded-lg p-4 border border-red-200">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-red-600 rounded-lg">
                  <MapPin className="h-5 w-5 text-white" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">Destination</p>
                  <p className="text-sm text-gray-600">
                    {load.destination_site?.consignee_name || 'N/A'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">{load.destination_address || 'Address not available'}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Carrier & Driver Info */}
          <div className="bg-purple-50 rounded-xl p-5 border border-purple-200">
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Truck className="h-5 w-5 text-purple-600" />
              Carrier Information
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Carrier:</span>
                <span className="font-semibold text-gray-900">{load.carrier?.carrier_name || 'N/A'}</span>
              </div>
              {load.driver_name && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Driver:</span>
                  <span className="font-semibold text-gray-900">{load.driver_name}</span>
                </div>
              )}
              {load.driver_phone && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Contact:</span>
                  <a href={`tel:${load.driver_phone}`} className="flex items-center gap-1 text-blue-600 hover:text-blue-700">
                    <Phone className="h-4 w-4" />
                    {load.driver_phone}
                  </a>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-gray-600">Macropoint:</span>
                <span className={`text-sm px-2 py-1 rounded ${load.has_macropoint_tracking ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                  {load.has_macropoint_tracking ? 'Active' : 'Not Active'}
                </span>
              </div>
            </div>
          </div>

          {/* Product Details */}
          <div className="bg-orange-50 rounded-xl p-5 border border-orange-200">
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Package className="h-5 w-5 text-orange-600" />
              Product Details
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Product Type:</span>
                <span className="font-semibold text-gray-900 capitalize">{load.product_type || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Volume:</span>
                <span className="font-semibold text-gray-900">{load.volume?.toLocaleString()} gal</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">TMS Load #:</span>
                <span className="text-sm text-gray-600 font-mono">{load.tms_load_number || 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* Collaborative Notes */}
          <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-5 border-2 border-purple-200">
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-purple-600" />
              Collaborative Notes {load.notes?.length > 0 && `(${load.notes.length})`}
            </h3>
            <div className="bg-white rounded-lg p-3 border border-purple-100 shadow-inner max-h-80 overflow-y-auto custom-scrollbar">
              {load.notes?.length > 0 ? (
                <div className="space-y-3">
                  {load.notes.map((note, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg shadow-sm ${
                        note.type === 'ai'
                          ? 'bg-gradient-to-r from-purple-50 to-purple-100 border-l-4 border-purple-400'
                          : 'bg-gradient-to-r from-green-50 to-green-100 border-l-4 border-green-400'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        {note.type === 'ai' ? (
                          <Bot className="h-4 w-4 text-purple-600" />
                        ) : (
                          <User className="h-4 w-4 text-green-600" />
                        )}
                        <span className={`text-xs font-bold ${
                          note.type === 'ai' ? 'text-purple-700' : 'text-green-700'
                        }`}>
                          {note.author}
                        </span>
                        <span className="text-xs text-gray-500 ml-auto">
                          {new Date(note.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-800 leading-relaxed">{note.text}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-400">
                  <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">No notes yet</p>
                  <p className="text-xs mt-1">Add notes from the table view</p>
                </div>
              )}
            </div>
          </div>

          {/* Timeline */}
          <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-5 border border-gray-200">
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Calendar className="h-5 w-5 text-gray-600" />
              Timeline
            </h3>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-gray-900">Created</p>
                  <p className="text-xs text-gray-500">{formatDate(load.created_at)}</p>
                </div>
              </div>
              {load.shipped_at && (
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-gray-900">Shipped</p>
                    <p className="text-xs text-gray-500">{formatDate(load.shipped_at)}</p>
                  </div>
                </div>
              )}
              {load.current_eta && (
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-gray-900">Expected Delivery</p>
                    <p className="text-xs text-gray-500">{formatDate(load.current_eta)}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

// ============== Loads Table ==============
function LoadsTable({ loads, statusFilter = 'all', onFilterChange, onLoadClick }) {
  const queryClient = useQueryClient()
  const [expandedLoadId, setExpandedLoadId] = useState(null)
  const [noteText, setNoteText] = useState('')
  const [noteAuthor, setNoteAuthor] = useState('')
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' })
  const [searchQuery, setSearchQuery] = useState('')

  const addNoteMutation = useMutation({
    mutationFn: ({ loadId, text, author }) => addNoteToLoad(loadId, text, author, 'human'),
    onSuccess: () => {
      queryClient.invalidateQueries(['loads'])
      setNoteText('')
      setNoteAuthor('')
    }
  })

  const emailOneMutation = useMutation({
    mutationFn: (loadId) => requestEtaForLoad(loadId),
    onSuccess: () => queryClient.invalidateQueries(['loads'])
  })

  const emailAllMutation = useMutation({
    mutationFn: () => requestEtaForAllLoads(),
    onSuccess: () => queryClient.invalidateQueries(['loads'])
  })

  // Sorting function
  const handleSort = (key) => {
    let direction = 'asc'
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc'
    }
    setSortConfig({ key, direction })
  }

  const getSortIcon = (columnKey) => {
    if (sortConfig.key !== columnKey) {
      return null // Don't show any icon on unsorted columns
    }
    return sortConfig.direction === 'asc'
      ? <ArrowUp className="h-4 w-4 text-slate-700" />
      : <ArrowDown className="h-4 w-4 text-slate-700" />
  }

  const clearAllFilters = () => {
    setSortConfig({ key: null, direction: 'asc' })
    setSearchQuery('')
    onFilterChange?.('all')
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'in_transit':
        return <span className="flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs">
          <Truck className="h-3 w-3" /> In Transit
        </span>
      case 'scheduled':
        return <span className="flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs">
          <Clock className="h-3 w-3" /> Scheduled
        </span>
      case 'delayed':
        return <span className="flex items-center gap-1 px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs animate-pulse">
          <AlertTriangle className="h-3 w-3" /> Delayed
        </span>
      case 'delivered':
        return <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs">
          <CheckCircle className="h-3 w-3" /> Delivered
        </span>
      default:
        return null
    }
  }

  // Filter, search, and sort loads
  const filteredAndSortedLoads = useMemo(() => {
    // First filter by status
    let filtered = loads?.filter(load => {
      if (statusFilter === 'all') return true
      return load.status?.toLowerCase() === statusFilter.toLowerCase()
    }) || []

    // Then filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(load => {
        return (
          load.po_number?.toLowerCase().includes(query) ||
          load.carrier?.carrier_name?.toLowerCase().includes(query) ||
          load.destination_site?.consignee_code?.toLowerCase().includes(query) ||
          load.destination_site?.consignee_name?.toLowerCase().includes(query) ||
          load.status?.toLowerCase().includes(query) ||
          load.volume?.toString().includes(query)
        )
      })
    }

    // Then sort
    if (sortConfig.key) {
      filtered = [...filtered].sort((a, b) => {
        let aValue, bValue

        switch (sortConfig.key) {
          case 'po_number':
            aValue = a.po_number || ''
            bValue = b.po_number || ''
            break
          case 'carrier':
            aValue = a.carrier?.carrier_name || ''
            bValue = b.carrier?.carrier_name || ''
            break
          case 'destination':
            aValue = a.destination_site?.consignee_code || ''
            bValue = b.destination_site?.consignee_code || ''
            break
          case 'volume':
            aValue = a.volume || 0
            bValue = b.volume || 0
            break
          case 'eta':
            aValue = a.current_eta ? new Date(a.current_eta).getTime() : 0
            bValue = b.current_eta ? new Date(b.current_eta).getTime() : 0
            break
          case 'status':
            aValue = a.status || ''
            bValue = b.status || ''
            break
          default:
            return 0
        }

        // Compare values
        if (typeof aValue === 'string') {
          const comparison = aValue.localeCompare(bValue)
          return sortConfig.direction === 'asc' ? comparison : -comparison
        } else {
          return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue
        }
      })
    }

    return filtered
  }, [loads, statusFilter, sortConfig, searchQuery])

  const handleAddNote = (loadId) => {
    if (!noteText.trim() || !noteAuthor.trim()) return
    addNoteMutation.mutate({ loadId, text: noteText, author: noteAuthor })
  }

  const getCustomerBadge = (customer) => {
    const customerConfig = {
      'stark_industries': { label: 'Stark', color: 'bg-red-100 text-red-700 border-red-200' },
      'wayne_enterprises': { label: 'Wayne', color: 'bg-gray-800 text-white border-gray-900' },
      'luthor_corp': { label: 'Luthor', color: 'bg-green-100 text-green-700 border-green-200' }
    }

    const config = customerConfig[customer] || { label: customer, color: 'bg-gray-100 text-gray-700 border-gray-200' }

    return (
      <span className={`px-2 py-0.5 text-xs font-semibold rounded border ${config.color}`}>
        {config.label}
      </span>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 bg-slate-50">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Truck className="h-5 w-5 text-slate-600" />
            <h3 className="text-base font-semibold text-slate-900">Active Shipments</h3>
            {statusFilter !== 'all' && (
              <span className="text-xs bg-slate-200 text-slate-700 px-2 py-0.5 rounded">
                {statusFilter === 'DELAYED' ? 'Delayed Only' : statusFilter}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            {onFilterChange && (
              <div className="flex gap-1.5">
                <button
                  onClick={() => onFilterChange('all')}
                  className={`text-xs px-3 py-1.5 rounded-md font-medium transition ${
                    statusFilter === 'all'
                      ? 'bg-slate-900 text-white'
                      : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  All
                </button>
                <button
                  onClick={() => onFilterChange('DELAYED')}
                  className={`text-xs px-3 py-1.5 rounded-md font-medium transition ${
                    statusFilter === 'DELAYED'
                      ? 'bg-red-600 text-white'
                      : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  Delayed
                </button>
              </div>
            )}
            <button
              onClick={() => emailAllMutation.mutate()}
              disabled={emailAllMutation.isPending}
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-300 transition"
              title="Send ETA request emails to all active load carriers"
            >
              <Mail className="h-3.5 w-3.5" />
              {emailAllMutation.isPending ? 'Sending...' : 'Email All Carriers'}
            </button>
            {emailAllMutation.isSuccess && (
              <span className="text-xs text-green-600 font-medium">
                Sent {emailAllMutation.data?.sent_count || 0} emails
              </span>
            )}
          </div>
        </div>

        {/* Search and Clear Filters Row */}
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by PO#, carrier, destination, status..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-10 py-2 bg-white border border-slate-200 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-transparent transition"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-600 transition"
              >
                <XCircle className="h-4 w-4" />
              </button>
            )}
          </div>
          {(sortConfig.key || searchQuery || statusFilter !== 'all') && (
            <button
              onClick={clearAllFilters}
              className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-100 transition text-sm font-medium"
            >
              <XCircle className="h-4 w-4" />
              Clear
            </button>
          )}
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead className="bg-slate-50 border-b border-slate-100">
            <tr>
              <th className="px-5 py-3 text-left text-xs font-medium text-slate-400 uppercase w-12"></th>
              <th
                className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase cursor-pointer hover:bg-slate-100 transition-colors select-none"
                onClick={() => handleSort('po_number')}
              >
                <div className="flex items-center gap-2">
                  <span>PO #</span>
                  {getSortIcon('po_number')}
                </div>
              </th>
              <th
                className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase cursor-pointer hover:bg-slate-100 transition-colors select-none"
                onClick={() => handleSort('carrier')}
              >
                <div className="flex items-center gap-2">
                  <span>Carrier</span>
                  {getSortIcon('carrier')}
                </div>
              </th>
              <th
                className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase cursor-pointer hover:bg-slate-100 transition-colors select-none"
                onClick={() => handleSort('destination')}
              >
                <div className="flex items-center gap-2">
                  <span>Destination</span>
                  {getSortIcon('destination')}
                </div>
              </th>
              <th
                className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase cursor-pointer hover:bg-slate-100 transition-colors select-none"
                onClick={() => handleSort('volume')}
              >
                <div className="flex items-center gap-2">
                  <span>Volume</span>
                  {getSortIcon('volume')}
                </div>
              </th>
              <th
                className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase cursor-pointer hover:bg-slate-100 transition-colors select-none"
                onClick={() => handleSort('eta')}
              >
                <div className="flex items-center gap-2">
                  <span>ETA</span>
                  {getSortIcon('eta')}
                </div>
              </th>
              <th
                className="px-5 py-3 text-left text-xs font-medium text-slate-500 uppercase cursor-pointer hover:bg-slate-100 transition-colors select-none"
                onClick={() => handleSort('status')}
              >
                <div className="flex items-center gap-2">
                  <span>Status</span>
                  {getSortIcon('status')}
                </div>
              </th>
              <th className="px-5 py-3 text-right text-xs font-medium text-slate-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filteredAndSortedLoads?.length === 0 && (
              <tr>
                <td colSpan="8" className="px-5 py-8 text-center text-slate-400">
                  No {statusFilter !== 'all' ? statusFilter.toLowerCase() : ''} loads found
                </td>
              </tr>
            )}
            {filteredAndSortedLoads?.map((load) => (
              <>
                <tr
                  key={load.id}
                  className="hover:bg-slate-50 transition-colors cursor-pointer"
                  onClick={() => onLoadClick?.(load)}
                >
                  <td className="px-5 py-4 whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => setExpandedLoadId(expandedLoadId === load.id ? null : load.id)}
                      className="text-slate-400 hover:text-slate-600 transition"
                    >
                      {expandedLoadId === load.id ? (
                        <ChevronUp className="h-5 w-5" />
                      ) : (
                        <ChevronDown className="h-5 w-5" />
                      )}
                    </button>
                  </td>
                  <td className="px-5 py-4 whitespace-nowrap text-sm font-medium text-slate-900">
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-2">
                        {load.po_number}
                        {load.notes?.length > 0 && (
                          <span className="flex items-center gap-1 px-1.5 py-0.5 bg-violet-50 text-violet-600 rounded-full text-xs">
                            <MessageSquare className="h-3 w-3" />
                            {load.notes.length}
                          </span>
                        )}
                      </div>
                      {load.destination_site?.customer && (
                        <div>
                          {getCustomerBadge(load.destination_site.customer)}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-5 py-4 whitespace-nowrap text-sm text-slate-600">
                    {load.carrier?.carrier_name || 'N/A'}
                  </td>
                  <td className="px-5 py-4 whitespace-nowrap text-sm text-slate-600">
                    {load.destination_site?.consignee_code || 'N/A'}
                  </td>
                  <td className="px-5 py-4 whitespace-nowrap text-sm text-slate-600">
                    {load.volume?.toLocaleString()} gal
                  </td>
                  <td className="px-5 py-4 whitespace-nowrap text-sm text-slate-600">
                    {load.current_eta ? new Date(load.current_eta).toLocaleString() : 'Pending'}
                  </td>
                  <td className="px-5 py-4 whitespace-nowrap">
                    {getStatusBadge(load.status)}
                  </td>
                  <td className="px-5 py-4 whitespace-nowrap text-right" onClick={(e) => e.stopPropagation()}>
                    {(load.status === 'in_transit' || load.status === 'scheduled' || load.status === 'delayed') && (
                      <button
                        onClick={() => emailOneMutation.mutate(load.id)}
                        disabled={emailOneMutation.isPending && emailOneMutation.variables === load.id}
                        className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-lg hover:bg-blue-100 disabled:opacity-50 transition"
                        title={`Request ETA from ${load.carrier?.carrier_name || 'carrier'}`}
                      >
                        <Mail className="h-3 w-3" />
                        Email
                      </button>
                    )}
                  </td>
                </tr>
                {expandedLoadId === load.id && (
                  <tr key={`${load.id}-notes`}>
                    <td colSpan="8" className="px-5 py-4 bg-slate-50 border-t border-slate-100">
                      <div className="space-y-4">
                        {/* Existing Notes */}
                        <div>
                          <h4 className="text-sm font-medium text-slate-700 mb-2 flex items-center gap-2">
                            <MessageSquare className="h-4 w-4" />
                            Collaborative Notes
                          </h4>
                          {load.notes?.length === 0 ? (
                            <p className="text-sm text-slate-400 italic">No notes yet. Add one below!</p>
                          ) : (
                            <div className="space-y-2 max-h-64 overflow-y-auto custom-scrollbar">
                              {load.notes?.map((note, idx) => (
                                <div
                                  key={idx}
                                  className={`p-3 rounded-lg border animate-slideInLeft ${
                                    note.type === 'ai'
                                      ? 'bg-purple-50 border-purple-200'
                                      : 'bg-green-50 border-green-200'
                                  }`}
                                >
                                  <div className="flex items-center justify-between mb-1">
                                    <div className="flex items-center gap-2">
                                      {note.type === 'ai' ? (
                                        <Bot className="h-4 w-4 text-purple-600" />
                                      ) : (
                                        <User className="h-4 w-4 text-green-600" />
                                      )}
                                      <span className={`text-xs font-semibold ${
                                        note.type === 'ai' ? 'text-purple-700' : 'text-green-700'
                                      }`}>
                                        {note.author}
                                      </span>
                                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                                        note.type === 'ai'
                                          ? 'bg-purple-200 text-purple-700'
                                          : 'bg-green-200 text-green-700'
                                      }`}>
                                        {note.type === 'ai' ? 'AI Agent' : 'Human'}
                                      </span>
                                    </div>
                                    <span className="text-xs text-gray-500">
                                      {new Date(note.timestamp).toLocaleString()}
                                    </span>
                                  </div>
                                  <p className="text-sm text-gray-700 ml-6">{note.text}</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>

                        {/* Add Note Form */}
                        <div className="border-t pt-4">
                          <h5 className="text-sm font-semibold text-gray-700 mb-2">Add Your Note</h5>
                          <div className="flex gap-2">
                            <input
                              type="text"
                              placeholder="Your name"
                              value={noteAuthor}
                              onChange={(e) => setNoteAuthor(e.target.value)}
                              className="px-3 py-2 border rounded-lg text-sm w-32 focus:ring-2 focus:ring-green-500 focus:border-green-500"
                            />
                            <input
                              type="text"
                              placeholder="Add a note about this load..."
                              value={noteText}
                              onChange={(e) => setNoteText(e.target.value)}
                              onKeyPress={(e) => e.key === 'Enter' && handleAddNote(load.id)}
                              className="flex-1 px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
                            />
                            <button
                              onClick={() => handleAddNote(load.id)}
                              disabled={!noteText.trim() || !noteAuthor.trim() || addNoteMutation.isLoading}
                              className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-smooth flex items-center gap-2"
                            >
                              <Send className="h-4 w-4" />
                              Add Note
                            </button>
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ============== Emails Panel ==============
function EmailsPanel({ emails, inboundEmails, onViewEmail }) {
  const [emailTab, setEmailTab] = useState('received')

  const inboundList = Array.isArray(inboundEmails) ? inboundEmails : []

  return (
    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
      <div className="px-5 py-3 bg-slate-50 border-b border-slate-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Mail className="h-5 w-5 text-slate-600" />
            <h3 className="text-base font-semibold text-slate-900">Email Communications</h3>
          </div>
          <div className="flex bg-slate-200 rounded-lg p-0.5">
            <button
              onClick={() => setEmailTab('received')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition ${
                emailTab === 'received' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Received{inboundList.length > 0 && ` (${inboundList.length})`}
            </button>
            <button
              onClick={() => setEmailTab('sent')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition ${
                emailTab === 'sent' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Sent{emails?.emails?.length > 0 && ` (${emails.emails.length})`}
            </button>
          </div>
        </div>
      </div>

      {/* Sent tab */}
      {emailTab === 'sent' && (
        <div className="p-4 space-y-2 max-h-72 overflow-y-auto">
          {emails?.emails?.length === 0 && (
            <p className="text-slate-400 text-center py-4 text-sm">No emails sent yet</p>
          )}
          {emails?.emails?.map((email, idx) => (
            <div
              key={idx}
              className="border border-slate-200 rounded-lg p-3 hover:bg-slate-50 hover:border-slate-300 transition cursor-pointer"
              onClick={() => onViewEmail?.({ ...email, _type: 'sent' })}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm">
                  <Send className="h-3.5 w-3.5 text-blue-500" />
                  <span className="font-medium text-slate-700">{email.to}</span>
                </div>
                <Eye className="h-4 w-4 text-slate-400" />
              </div>
              <p className="text-sm font-medium text-slate-900 mt-1">{email.subject}</p>
              <p className="text-xs text-slate-400 mt-1">
                {new Date(email.sent_at).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Received tab */}
      {emailTab === 'received' && (
        <div className="p-4 space-y-2 max-h-72 overflow-y-auto">
          {inboundList.length === 0 && (
            <p className="text-slate-400 text-center py-4 text-sm">No inbound emails yet</p>
          )}
          {inboundList.map((email) => (
            <div
              key={email.id}
              className="border border-slate-200 rounded-lg p-3 hover:bg-slate-50 hover:border-slate-300 transition cursor-pointer"
              onClick={() => onViewEmail?.({ ...email, _type: 'inbound' })}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm">
                  <Mail className="h-3.5 w-3.5 text-emerald-500" />
                  <span className="font-medium text-slate-700">{email.from_email}</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  email.parse_success
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'bg-amber-50 text-amber-700'
                }`}>
                  {email.parse_success ? 'Parsed' : 'Needs Review'}
                </span>
              </div>
              <p className="text-sm font-medium text-slate-900 mt-1">{email.subject}</p>
              <div className="flex items-center justify-between mt-1">
                <p className="text-xs text-slate-400">
                  {email.received_at ? new Date(email.received_at).toLocaleString() : 'Unknown'}
                </p>
                {email.parsed_eta && (
                  <p className="text-xs font-medium text-emerald-600">
                    ETA: {new Date(email.parsed_eta).toLocaleString()}
                  </p>
                )}
              </div>
              {email.po_number && (
                <p className="text-xs text-slate-500 mt-1">PO: {email.po_number}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ============== Stats Card ==============
function StatsCard({ title, value, icon: Icon, color = 'blue', onClick, clickable = false }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-emerald-50 text-emerald-600',
    yellow: 'bg-amber-50 text-amber-600',
    red: 'bg-red-50 text-red-600',
    purple: 'bg-violet-50 text-violet-600'
  }

  return (
    <div
      className={`bg-white rounded-lg border border-slate-200 p-4 transition-all ${
        clickable ? 'cursor-pointer hover:border-slate-300 hover:shadow-sm' : ''
      }`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{title}</p>
          <p className="text-2xl font-semibold text-slate-900 mt-1">{value}</p>
        </div>
        <div className={`p-2.5 rounded-lg ${colors[color]}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      {clickable && (
        <p className="text-xs text-slate-400 mt-2 flex items-center gap-1">
          <Filter className="h-3 w-3" /> Click to filter
        </p>
      )}
    </div>
  )
}

// ============== Main Dashboard ==============
function Dashboard({ user, onLogout }) {
  const queryClient = useQueryClient()
  const [selectedEscalation, setSelectedEscalation] = useState(null)
  const [escalationFilter, setEscalationFilter] = useState('open')
  const [selectedEmail, setSelectedEmail] = useState(null)
  const [selectedLoad, setSelectedLoad] = useState(null)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [siteFilter, setSiteFilter] = useState('all') // 'all', 'at-risk', 'critical', 'delayed'
  const [customerFilter, setCustomerFilter] = useState('') // filter by customer
  const [loadStatusFilter, setLoadStatusFilter] = useState('all') // 'all', 'SCHEDULED', 'IN_TRANSIT', 'DELAYED', 'DELIVERED'
  const [selectedSiteForEdit, setSelectedSiteForEdit] = useState(null)
  const [showBatchUpload, setShowBatchUpload] = useState(false)
  const [selectedAgentForAssignment, setSelectedAgentForAssignment] = useState(null)

  const { data: stats, isFetching: isStatsFetching, error: statsError, isLoading: isStatsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
    retry: 2
  })

  const { data: sites, isFetching: isSitesFetching, error: sitesError, isLoading: isSitesLoading } = useQuery({
    queryKey: ['sites'],
    queryFn: getSites,
    retry: 2
  })

  const { data: customers = [], isFetching: isCustomersFetching } = useQuery({
    queryKey: ['customers'],
    queryFn: getCustomers
  })

  const { data: loads, isFetching: isLoadsFetching, error: loadsError, isLoading: isLoadsLoading } = useQuery({
    queryKey: ['active-loads'],
    queryFn: getActiveLoads,
    refetchInterval: 30000,
    staleTime: 10000
  })

  const { data: openEscalations, isFetching: isEscalationsFetching } = useQuery({
    queryKey: ['open-escalations'],
    queryFn: getOpenEscalations
  })

  const { data: allEscalations } = useQuery({
    queryKey: ['all-escalations'],
    queryFn: getEscalations,
    enabled: escalationFilter === 'resolved'
  })

  const escalations = escalationFilter === 'open' ? openEscalations : allEscalations
  const displayedEscalations = escalationFilter === 'resolved'
    ? escalations?.filter(e => e.status === 'resolved')
    : escalations

  const { data: agents, isFetching: isAgentsFetching } = useQuery({
    queryKey: ['agents'],
    queryFn: getAgents
  })

  const { data: emails, isFetching: isEmailsFetching } = useQuery({
    queryKey: ['sent-emails'],
    queryFn: getSentEmails
  })

  const { data: inboundEmails } = useQuery({
    queryKey: ['inbound-emails'],
    queryFn: getInboundEmails,
    refetchInterval: 30000,
  })

  const { data: intelligenceData } = useQuery({
    queryKey: ['intelligence'],
    queryFn: getIntelligence,
    enabled: activeTab === 'intelligence',
  })

  const resolveMutation = useMutation({
    mutationFn: ({ id, notes }) => resolveEscalation(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries(['open-escalations'])
      queryClient.invalidateQueries(['all-escalations'])
      setSelectedEscalation(null)
    }
  })

  const refreshKgMutation = useMutation({
    mutationFn: refreshKnowledgeGraph,
    onSuccess: () => {
      queryClient.invalidateQueries(['intelligence'])
    }
  })

  const assignSiteMutation = useMutation({
    mutationFn: async ({ siteId, agentId }) => {
      const response = await fetch(`/api/sites/${siteId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ assigned_agent_id: agentId })
      })
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['sites'])
    }
  })

  const updateSiteMutation = useMutation({
    mutationFn: ({ siteId, data }) => updateSite(siteId, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['sites'])
    }
  })

  const batchUploadMutation = useMutation({
    mutationFn: ({ customer, erpSource, sites }) => batchUpdateSites(customer, erpSource, sites),
    onSuccess: () => {
      queryClient.invalidateQueries(['sites'])
    }
  })

  const assignSitesToAgentMutation = useMutation({
    mutationFn: ({ agentId, siteIds }) => assignSitesToAgent(agentId, siteIds),
    onSuccess: () => {
      queryClient.invalidateQueries(['sites'])
      queryClient.invalidateQueries(['agents'])
    }
  })

  // Filter sites based on selection
  const filteredSites = useMemo(() => {
    if (!sites) return []
    let filtered = sites

    // Filter by customer first
    if (customerFilter) {
      filtered = filtered.filter(s => s.customer === customerFilter)
    }

    // Then filter by status
    switch (siteFilter) {
      case 'at-risk':
        return filtered.filter(s => s.hours_to_runout && s.hours_to_runout <= 48)
      case 'critical':
        return filtered.filter(s => s.hours_to_runout && s.hours_to_runout < 24)
      case 'ok':
        return filtered.filter(s => !s.hours_to_runout || s.hours_to_runout > 48)
      default:
        return filtered
    }
  }, [sites, siteFilter, customerFilter])

  // Handle stat card clicks
  const handleStatClick = (filter, tab = 'sites') => {
    setSiteFilter(filter)
    setActiveTab(tab)
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-slate-900 rounded-lg">
                <Fuel className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold text-slate-900">Fuels Logistics</h1>
                <p className="text-xs text-slate-500">AI Coordinator</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {openEscalations?.length > 0 && (
                <button
                  onClick={() => { setEscalationFilter('open'); setActiveTab('escalations') }}
                  className="relative p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition"
                >
                  <Bell className="h-5 w-5" />
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                    {openEscalations.length}
                  </span>
                </button>
              )}

              <button
                onClick={() => queryClient.invalidateQueries()}
                className="flex items-center gap-2 px-3 py-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg text-sm transition"
                disabled={isLoadsFetching || isStatsFetching || isSitesFetching || isEscalationsFetching}
              >
                <RefreshCw className={`h-4 w-4 ${
                  (isLoadsFetching || isStatsFetching || isSitesFetching || isEscalationsFetching) ? 'animate-spin' : ''
                }`} />
              </button>

              <div className="flex items-center gap-3 pl-3 ml-3 border-l border-slate-200">
                <div className="text-right">
                  <p className="text-sm font-medium text-slate-900">{user.name}</p>
                  <p className="text-xs text-slate-500 capitalize">{user.role}</p>
                </div>
                <button
                  onClick={onLogout}
                  className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                  title="Sign Out"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto px-4 py-6">
        {/* Error Banner */}
        {(statsError || loadsError || sitesError) && (
          <div className="mb-6 bg-red-50 border border-red-200 p-4 rounded-lg">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-red-700">Unable to load data</p>
                <p className="text-xs text-red-600 mt-0.5">Check your connection and try refreshing.</p>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {(isStatsLoading || isLoadsLoading || isSitesLoading) && (
          <div className="mb-6 bg-slate-100 border border-slate-200 p-4 rounded-lg">
            <div className="flex items-center gap-3">
              <RefreshCw className="h-4 w-4 text-slate-500 animate-spin" />
              <p className="text-sm text-slate-600">Loading...</p>
            </div>
          </div>
        )}

        {/* Escalation Banner */}
        <EscalationBanner
          escalations={openEscalations}
          onViewAll={() => { setEscalationFilter('open'); setActiveTab('escalations') }}
        />

        {/* Stats Cards Row */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-6">
          <StatsCard
            title="Sites at Risk"
            value={stats?.sites_at_risk || 0}
            icon={AlertTriangle}
            color={stats?.sites_at_risk > 0 ? 'red' : 'green'}
            clickable
            onClick={() => handleStatClick('at-risk', 'sites')}
          />
          <StatsCard
            title="Open Escalations"
            value={stats?.open_escalations || 0}
            icon={Bell}
            color={stats?.open_escalations > 0 ? 'red' : 'green'}
            clickable
            onClick={() => { setEscalationFilter('open'); setActiveTab('escalations') }}
          />
          <StatsCard
            title="Delayed Loads"
            value={stats?.delayed_loads || 0}
            icon={Clock}
            color={stats?.delayed_loads > 0 ? 'yellow' : 'green'}
            clickable
            onClick={() => {
              setLoadStatusFilter('DELAYED')
              setActiveTab('loads')
            }}
          />
          <StatsCard
            title="Active Loads"
            value={stats?.active_loads || 0}
            icon={Truck}
            color="blue"
            clickable
            onClick={() => {
              setLoadStatusFilter('all')
              setActiveTab('loads')
            }}
          />
          <StatsCard
            title="Total Sites"
            value={stats?.total_sites || 0}
            icon={Fuel}
            color="blue"
            clickable
            onClick={() => handleStatClick('all', 'sites')}
          />
        </div>

        {/* Main Layout: Nav Sidebar + Content */}
        <div className="flex gap-6">
          {/* Left Sidebar - Tab Navigation */}
          <div className="w-48 flex-shrink-0">
            <nav className="flex flex-col gap-1 h-[360px]">
              {[
                { id: 'dashboard', label: 'Dashboard', icon: Activity },
                { id: 'sites', label: 'Sites', icon: Fuel },
                { id: 'loads', label: 'Loads', icon: Truck },
                { id: 'agent-monitor', label: 'Agent Monitor', icon: Bot },
                { id: 'escalations', label: 'Escalations', icon: Bell },
                { id: 'intelligence', label: 'System Logic', icon: Brain },
                { id: 'sheets', label: 'Google Sheets', icon: FileSpreadsheet }
              ].map(({ id, label, icon: TabIcon }) => (
                <button
                  key={id}
                  onClick={() => {
                    setActiveTab(id)
                    if (id !== 'sites') setSiteFilter('all')
                  }}
                  className={`flex-1 flex items-center gap-3 px-3 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === id
                      ? 'bg-slate-900 text-white'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <TabIcon className="h-4 w-4" />
                  {label}
                </button>
              ))}
            </nav>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 min-w-0">

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              <LoadsTable
                loads={loads}
                statusFilter={loadStatusFilter}
                onFilterChange={setLoadStatusFilter}
                onLoadClick={setSelectedLoad}
              />
            </div>
            <div className="space-y-6">
              <AgentManagementPanel agents={agents} sites={sites} />
              <EmailsPanel emails={emails} inboundEmails={inboundEmails} onViewEmail={setSelectedEmail} />
            </div>
          </div>
        )}

        {/* Sites Tab */}
        {activeTab === 'sites' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-slate-900">Site Inventory Management</h2>
              <div className="flex items-center gap-3">
                {/* Customer Filter Dropdown */}
                <select
                  value={customerFilter}
                  onChange={(e) => setCustomerFilter(e.target.value)}
                  className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-slate-500 focus:border-slate-500"
                >
                  <option value="">All Customers</option>
                  {customers.map(c => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
                {/* Batch Upload Button */}
                <button
                  onClick={() => setShowBatchUpload(true)}
                  className="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition text-sm"
                >
                  <Upload className="h-4 w-4" />
                  Batch Upload
                </button>
                {/* Filter Pills */}
                <div className="flex gap-2">
                  {[
                    { id: 'all', label: 'All', count: customerFilter ? sites?.filter(s => s.customer === customerFilter).length : sites?.length },
                    { id: 'at-risk', label: 'At Risk', count: (customerFilter ? sites?.filter(s => s.customer === customerFilter) : sites)?.filter(s => s.hours_to_runout && s.hours_to_runout <= 48).length },
                    { id: 'critical', label: 'Critical', count: (customerFilter ? sites?.filter(s => s.customer === customerFilter) : sites)?.filter(s => s.hours_to_runout && s.hours_to_runout < 24).length }
                  ].map(({ id, label, count }) => (
                    <button
                      key={id}
                      onClick={() => setSiteFilter(id)}
                      className={`px-3 py-1 rounded-full text-sm font-medium transition ${
                        siteFilter === id
                          ? id === 'critical' ? 'bg-red-600 text-white' :
                            id === 'at-risk' ? 'bg-orange-500 text-white' :
                            'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {label} ({count || 0})
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Active Filter Banner */}
            {(siteFilter !== 'all' || customerFilter) && (
              <div className={`mb-4 p-3 rounded-lg flex items-center justify-between ${
                siteFilter === 'critical' ? 'bg-red-100 text-red-800' :
                siteFilter === 'at-risk' ? 'bg-orange-100 text-orange-800' :
                'bg-blue-100 text-blue-800'
              }`}>
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4" />
                  <span className="font-medium">
                    Showing {filteredSites.length} {siteFilter === 'critical' ? 'critical' : siteFilter === 'at-risk' ? 'at-risk' : ''} sites
                    {customerFilter && ` for ${customers.find(c => c.value === customerFilter)?.label}`}
                  </span>
                </div>
                <button
                  onClick={() => { setSiteFilter('all'); setCustomerFilter(''); }}
                  className="flex items-center gap-1 text-sm hover:underline"
                >
                  <X className="h-4 w-4" /> Clear filters
                </button>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredSites?.map((site) => (
                <SiteCard
                  key={site.id}
                  site={site}
                  agents={agents}
                  onAssign={(siteId, agentId) =>
                    assignSiteMutation.mutate({ siteId, agentId })
                  }
                  onEdit={(site) => setSelectedSiteForEdit(site)}
                />
              ))}
              {filteredSites?.length === 0 && (
                <div className="col-span-full text-center py-8 text-gray-500">
                  No sites match the current filter.
                </div>
              )}
            </div>
          </div>
        )}

        {/* Agent Monitor Tab (HITL) */}
        {activeTab === 'agent-monitor' && (
          <div>
            <h2 className="text-xl font-bold mb-4">Agent Monitor - Human in the Loop</h2>
            <AgentMonitorTab
              agents={agents}
              sites={sites}
              emails={emails}
              onViewEmail={setSelectedEmail}
              onManageSites={(agent) => setSelectedAgentForAssignment(agent)}
            />
          </div>
        )}

        {/* Loads Tab */}
        {activeTab === 'loads' && (
          <div>
            <h2 className="text-xl font-bold mb-4">Shipment Management</h2>
            <LoadsTable
              loads={loads}
              statusFilter={loadStatusFilter}
              onFilterChange={setLoadStatusFilter}
              onLoadClick={setSelectedLoad}
            />
          </div>
        )}

        {/* Escalations Tab */}
        {activeTab === 'escalations' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold">Escalation Center</h2>
              <div className="flex bg-slate-100 rounded-lg p-0.5">
                <button
                  onClick={() => setEscalationFilter('open')}
                  className={`px-4 py-1.5 text-sm font-medium rounded-md transition ${
                    escalationFilter === 'open'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  Open{openEscalations?.length ? ` (${openEscalations.length})` : ''}
                </button>
                <button
                  onClick={() => setEscalationFilter('resolved')}
                  className={`px-4 py-1.5 text-sm font-medium rounded-md transition ${
                    escalationFilter === 'resolved'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  Resolved
                </button>
              </div>
            </div>
            {displayedEscalations?.length === 0 ? (
              <div className="bg-white rounded-xl p-8 text-center">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-3" />
                <p className="text-gray-500">
                  {escalationFilter === 'open'
                    ? 'No open escalations. All systems normal!'
                    : 'No resolved escalations yet.'}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {displayedEscalations?.map((esc) => (
                  <div
                    key={esc.id}
                    onClick={() => setSelectedEscalation(esc)}
                    className={`p-4 rounded-xl border-l-4 cursor-pointer transition hover:shadow-lg ${
                      esc.status === 'resolved' ? 'border-green-500 bg-green-50' :
                      esc.priority === 'critical' ? 'border-red-500 bg-red-50' :
                      esc.priority === 'high' ? 'border-orange-500 bg-orange-50' :
                      'border-yellow-500 bg-yellow-50'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <span className={`text-xs font-bold uppercase ${
                          esc.status === 'resolved' ? 'text-green-700' :
                          esc.priority === 'critical' ? 'text-red-700' :
                          esc.priority === 'high' ? 'text-orange-700' : 'text-yellow-700'
                        }`}>
                          {esc.status === 'resolved' ? 'resolved' : esc.priority} • {esc.issue_type?.replace(/_/g, ' ')}
                        </span>
                        <p className="font-medium mt-1">{esc.description}</p>
                        <div className="flex items-center gap-3 mt-2">
                          <p className="text-xs text-gray-500">
                            {new Date(esc.created_at).toLocaleString()}
                          </p>
                          {esc.status === 'resolved' && esc.resolved_at && (
                            <p className="text-xs text-green-600">
                              Resolved {new Date(esc.resolved_at).toLocaleString()}
                            </p>
                          )}
                        </div>
                        {esc.status === 'resolved' && esc.resolution_notes && (
                          <p className="text-xs text-green-700 mt-1 italic">
                            {esc.resolution_notes}
                          </p>
                        )}
                      </div>
                      <ChevronRight className="h-5 w-5 text-gray-400" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* System Logic Tab */}
        {activeTab === 'intelligence' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold">System Logic</h2>
                <p className="text-sm text-slate-500">How the AI coordinator makes decisions — architecture, rules, and learned intelligence.</p>
              </div>
              <a
                href={`${(import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace('/api', '')}/docs`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 hover:text-slate-900 transition"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                API Docs (Swagger)
              </a>
            </div>

            {/* Tier Architecture Overview */}
            <div>
              <h3 className="text-base font-semibold text-slate-800 mb-3">Decision Architecture</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Tier 1 Card */}
              <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                <div className="bg-emerald-600 px-5 py-3 flex items-center gap-2">
                  <Shield className="h-5 w-5 text-white" />
                  <h3 className="text-white font-semibold">Tier 1 — Rules Engine</h3>
                  <span className="ml-auto text-emerald-100 text-xs font-mono bg-emerald-700 px-2 py-0.5 rounded">$0 / run</span>
                </div>
                <div className="p-5 space-y-3">
                  <p className="text-sm text-slate-600">
                    Deterministic threshold checks that handle ~90% of routine situations with zero LLM tokens.
                  </p>
                  <div className="space-y-2">
                    <div className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5 flex-shrink-0" />
                      <div className="text-sm"><span className="font-medium text-slate-800">Critical runout</span> <span className="text-slate-500">— &lt;12h to runout, no active load → immediate escalation</span></div>
                    </div>
                    <div className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-orange-500 mt-1.5 flex-shrink-0" />
                      <div className="text-sm"><span className="font-medium text-slate-800">High risk</span> <span className="text-slate-500">— &lt;24h to runout, no active load → high-priority escalation</span></div>
                    </div>
                    <div className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" />
                      <div className="text-sm"><span className="font-medium text-slate-800">Stale ETA</span> <span className="text-slate-500">— Load ETA &gt;4h old → auto-send ETA request email</span></div>
                    </div>
                    <div className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" />
                      <div className="text-sm"><span className="font-medium text-slate-800">Delayed load</span> <span className="text-slate-500">— Status DELAYED → auto-send ETA request email</span></div>
                    </div>
                    <div className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 flex-shrink-0" />
                      <div className="text-sm"><span className="font-medium text-slate-800">Unreliable carrier</span> <span className="text-slate-500">— Reliability score &lt;0.4 → flag for Tier 2 review</span></div>
                    </div>
                  </div>
                  <div className="bg-emerald-50 rounded-lg p-3 mt-3">
                    <p className="text-xs text-emerald-700 font-medium">Actions: create_escalation, send_eta_email</p>
                    <p className="text-xs text-emerald-600 mt-1">Respects execution mode (Draft Only / Auto Email / Full Auto)</p>
                  </div>
                </div>
              </div>

              {/* Tier 2 Card */}
              <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                <div className="bg-violet-600 px-5 py-3 flex items-center gap-2">
                  <Brain className="h-5 w-5 text-white" />
                  <h3 className="text-white font-semibold">Tier 2 — LLM Agent</h3>
                  <span className="ml-auto text-violet-100 text-xs font-mono bg-violet-700 px-2 py-0.5 rounded">~$0.01-0.02 / call</span>
                </div>
                <div className="p-5 space-y-3">
                  <p className="text-sm text-slate-600">
                    Claude-powered analysis that only fires when Tier 1 flags ambiguous situations needing judgment.
                  </p>
                  <div className="space-y-2">
                    <div className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-violet-500 mt-1.5 flex-shrink-0" />
                      <div className="text-sm"><span className="font-medium text-slate-800">Ambiguous inventory</span> <span className="text-slate-500">— Below threshold but loads active with complications</span></div>
                    </div>
                    <div className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-violet-500 mt-1.5 flex-shrink-0" />
                      <div className="text-sm"><span className="font-medium text-slate-800">Unreliable carrier</span> <span className="text-slate-500">— Carrier flagged unreliable, LLM decides severity + wording</span></div>
                    </div>
                    <div className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-violet-500 mt-1.5 flex-shrink-0" />
                      <div className="text-sm"><span className="font-medium text-slate-800">Multi-site risk</span> <span className="text-slate-500">— Same carrier late on multiple loads simultaneously</span></div>
                    </div>
                    <div className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-violet-500 mt-1.5 flex-shrink-0" />
                      <div className="text-sm"><span className="font-medium text-slate-800">Crafted escalations</span> <span className="text-slate-500">— LLM writes context-rich descriptions with knowledge graph data</span></div>
                    </div>
                  </div>
                  <div className="bg-violet-50 rounded-lg p-3 mt-3">
                    <p className="text-xs text-violet-700 font-medium">Enriched with: carrier reliability, site history, false alarm rates</p>
                    <p className="text-xs text-violet-600 mt-1">Only invoked on Tier 1 flags — skipped entirely for routine runs</p>
                  </div>
                </div>
              </div>
              </div>
            </div>

            {/* Knowledge Graph Section */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Layers className="h-5 w-5 text-slate-700" />
                  <h3 className="text-base font-semibold text-slate-800">Knowledge Graph</h3>
                  <span className="text-xs text-slate-500">Passive intelligence from operational data — zero LLM tokens</span>
                </div>
                <button
                  onClick={() => refreshKgMutation.mutate()}
                  disabled={refreshKgMutation.isPending}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 disabled:opacity-50 transition"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${refreshKgMutation.isPending ? 'animate-spin' : ''}`} />
                  {refreshKgMutation.isPending ? 'Rebuilding...' : 'Rebuild from data'}
                </button>
              </div>

              {refreshKgMutation.data && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-2 text-xs text-emerald-700 mb-3">
                  Rebuilt: {refreshKgMutation.data.carriers_updated} carrier(s), {refreshKgMutation.data.sites_updated} site(s) updated
                </div>
              )}

              {(!intelligenceData || (intelligenceData.carriers?.length === 0 && intelligenceData.sites?.length === 0)) ? (
                <div className="bg-white rounded-xl p-8 text-center">
                  <Brain className="h-10 w-10 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500 text-sm">No intelligence data yet. Click "Rebuild from data" to scan existing deliveries and escalations, or data will accumulate automatically over time.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Carrier Reliability */}
                  <div>
                    <h4 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-3 flex items-center gap-2">
                      <Truck className="h-4 w-4" /> Carrier Reliability
                    </h4>
                    {intelligenceData.carriers?.length === 0 ? (
                      <div className="bg-white rounded-xl p-6 text-center text-sm text-slate-400">No carrier data yet</div>
                    ) : (
                      <div className="space-y-3">
                        {intelligenceData.carriers?.map((c) => (
                          <div key={c.carrier_id} className="bg-white rounded-xl border border-slate-200 p-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium text-slate-800">{c.carrier_name}</span>
                              <div className="flex items-center gap-2">
                                {c.flagged_unreliable && (
                                  <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">Unreliable</span>
                                )}
                                <div className={`text-sm font-bold ${
                                  c.reliability_score >= 0.7 ? 'text-emerald-600' :
                                  c.reliability_score >= 0.4 ? 'text-amber-600' : 'text-red-600'
                                }`}>
                                  {(c.reliability_score * 100).toFixed(0)}%
                                </div>
                              </div>
                            </div>
                            {/* Reliability Bar */}
                            <div className="w-full bg-slate-100 rounded-full h-2 mb-3">
                              <div
                                className={`h-2 rounded-full transition-all ${
                                  c.reliability_score >= 0.7 ? 'bg-emerald-500' :
                                  c.reliability_score >= 0.4 ? 'bg-amber-500' : 'bg-red-500'
                                }`}
                                style={{ width: `${c.reliability_score * 100}%` }}
                              />
                            </div>
                            <div className="grid grid-cols-3 gap-3 text-center">
                              <div>
                                <div className="text-lg font-bold text-slate-800">{c.total_deliveries}</div>
                                <div className="text-xs text-slate-500">Deliveries</div>
                              </div>
                              <div>
                                <div className="text-lg font-bold text-slate-800">{c.late_deliveries}</div>
                                <div className="text-xs text-slate-500">Late</div>
                              </div>
                              <div>
                                <div className="text-lg font-bold text-slate-800">
                                  {c.avg_delay_hours > 0 ? `${c.avg_delay_hours}h` : '—'}
                                </div>
                                <div className="text-xs text-slate-500">Avg Delay</div>
                              </div>
                            </div>
                            {c.total_eta_requests > 0 && (
                              <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                                <span>ETA Requests: {c.eta_responses_received}/{c.total_eta_requests} responded</span>
                                {c.avg_response_time_hours && (
                                  <span>Avg response: {c.avg_response_time_hours}h</span>
                                )}
                              </div>
                            )}
                            {c.recent_deliveries?.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-slate-100">
                                <div className="text-xs text-slate-500 mb-1.5">Recent deliveries</div>
                                <div className="flex gap-1">
                                  {c.recent_deliveries.map((d, i) => (
                                    <div
                                      key={i}
                                      title={`PO ${d.po_number} — ${d.on_time ? 'On time' : `Late by ${d.delay_hours}h`}`}
                                      className={`w-5 h-5 rounded text-[10px] font-bold flex items-center justify-center ${
                                        d.on_time ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
                                      }`}
                                    >
                                      {d.on_time ? '✓' : '✗'}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Site Intelligence */}
                  <div>
                    <h4 className="text-sm font-semibold text-slate-600 uppercase tracking-wide mb-3 flex items-center gap-2">
                      <Fuel className="h-4 w-4" /> Site Intelligence
                    </h4>
                    {intelligenceData.sites?.length === 0 ? (
                      <div className="bg-white rounded-xl p-6 text-center text-sm text-slate-400">No site data yet</div>
                    ) : (
                      <div className="space-y-3">
                        {intelligenceData.sites?.map((s) => (
                          <div key={s.site_id} className="bg-white rounded-xl border border-slate-200 p-4">
                            <div className="flex items-center justify-between mb-2">
                              <div>
                                <span className="font-medium text-slate-800">{s.site_code}</span>
                                {s.site_name && <span className="text-sm text-slate-500 ml-2">{s.site_name}</span>}
                              </div>
                              <div className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                                s.risk_score >= 0.7 ? 'bg-red-100 text-red-700' :
                                s.risk_score >= 0.4 ? 'bg-amber-100 text-amber-700' :
                                'bg-emerald-100 text-emerald-700'
                              }`}>
                                Risk: {(s.risk_score * 100).toFixed(0)}%
                              </div>
                            </div>
                            <div className="grid grid-cols-3 gap-3 text-center">
                              <div>
                                <div className="text-lg font-bold text-slate-800">{s.total_escalations}</div>
                                <div className="text-xs text-slate-500">Escalations</div>
                              </div>
                              <div>
                                <div className="text-lg font-bold text-slate-800">{s.false_alarm_count}</div>
                                <div className="text-xs text-slate-500">False Alarms</div>
                              </div>
                              <div>
                                <div className="text-lg font-bold text-slate-800">{s.total_deliveries}</div>
                                <div className="text-xs text-slate-500">Deliveries</div>
                              </div>
                            </div>
                            {s.false_alarm_rate > 0 && (
                              <div className="mt-3 pt-3 border-t border-slate-100">
                                <div className="flex items-center justify-between text-xs">
                                  <span className="text-slate-500">False alarm rate</span>
                                  <span className={`font-medium ${
                                    s.false_alarm_rate >= 0.5 ? 'text-amber-600' : 'text-slate-700'
                                  }`}>{(s.false_alarm_rate * 100).toFixed(0)}%</span>
                                </div>
                                <div className="w-full bg-slate-100 rounded-full h-1.5 mt-1">
                                  <div
                                    className={`h-1.5 rounded-full ${
                                      s.false_alarm_rate >= 0.5 ? 'bg-amber-400' : 'bg-slate-300'
                                    }`}
                                    style={{ width: `${s.false_alarm_rate * 100}%` }}
                                  />
                                </div>
                              </div>
                            )}
                            {s.recent_events?.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-slate-100">
                                <div className="text-xs text-slate-500 mb-1.5">Recent events</div>
                                <div className="space-y-1">
                                  {s.recent_events.slice(-3).map((evt, i) => (
                                    <div key={i} className="text-xs text-slate-600 flex items-center gap-1.5">
                                      <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                                        evt.type === 'delivery' ? 'bg-blue-500' :
                                        evt.type === 'escalation_resolved' ? 'bg-green-500' : 'bg-slate-400'
                                      }`} />
                                      <span className="truncate">{evt.details}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Event Hooks Diagram */}
            <div className="bg-white rounded-xl border border-slate-200 p-5">
              <h4 className="text-sm font-semibold text-slate-700 mb-3">How Intelligence Accumulates</h4>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <div className="bg-blue-50 rounded-lg p-3 text-center">
                  <Truck className="h-5 w-5 text-blue-600 mx-auto mb-1" />
                  <div className="text-xs font-semibold text-blue-800">Load Delivered</div>
                  <div className="text-[11px] text-blue-600 mt-1">Carrier on-time rate, site delivery count</div>
                </div>
                <div className="bg-amber-50 rounded-lg p-3 text-center">
                  <Bell className="h-5 w-5 text-amber-600 mx-auto mb-1" />
                  <div className="text-xs font-semibold text-amber-800">Escalation Resolved</div>
                  <div className="text-[11px] text-amber-600 mt-1">Site false alarm rate, risk score</div>
                </div>
                <div className="bg-violet-50 rounded-lg p-3 text-center">
                  <Mail className="h-5 w-5 text-violet-600 mx-auto mb-1" />
                  <div className="text-xs font-semibold text-violet-800">ETA Email Reply</div>
                  <div className="text-[11px] text-violet-600 mt-1">Carrier response time, reliability</div>
                </div>
                <div className="bg-red-50 rounded-lg p-3 text-center">
                  <AlertTriangle className="h-5 w-5 text-red-600 mx-auto mb-1" />
                  <div className="text-xs font-semibold text-red-800">Non-ETA Email</div>
                  <div className="text-[11px] text-red-600 mt-1">Auto-escalate: shortages, breakdowns, cancellations</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Google Sheets Tab */}
        {activeTab === 'sheets' && (
          <div className="max-w-2xl">
            <h2 className="text-xl font-bold mb-4">Google Sheets Integration</h2>
            <GoogleSheetsPanel sites={sites} loads={loads} />
          </div>
        )}

          </div> {/* End Main Content Area */}
        </div> {/* End Sidebar + Content Flex */}
      </main>

      {/* Escalation Modal */}
      <EscalationModal
        escalation={selectedEscalation}
        onClose={() => setSelectedEscalation(null)}
        onResolve={(id, notes) => resolveMutation.mutate({ id, notes })}
      />

      {/* Email Detail Modal */}
      <EmailDetailModal
        email={selectedEmail}
        onClose={() => setSelectedEmail(null)}
      />

      {/* Site Details Modal */}
      <SiteDetailsModal
        site={selectedSiteForEdit}
        onClose={() => setSelectedSiteForEdit(null)}
        onSave={(siteId, data) => updateSiteMutation.mutateAsync({ siteId, data })}
      />

      {/* Batch Upload Modal */}
      {showBatchUpload && (
        <BatchUploadModal
          onClose={() => setShowBatchUpload(false)}
          onUpload={(customer, erpSource, sites) => batchUploadMutation.mutateAsync({ customer, erpSource, sites })}
        />
      )}

      {/* Agent Site Assignment Modal */}
      <AgentAssignmentModal
        agent={selectedAgentForAssignment}
        sites={sites}
        onClose={() => setSelectedAgentForAssignment(null)}
        onSave={(agentId, siteIds) => assignSitesToAgentMutation.mutateAsync({ agentId, siteIds })}
      />

      {/* Load Details Sidebar */}
      {selectedLoad && (
        <LoadDetailsSidebar
          load={selectedLoad}
          onClose={() => setSelectedLoad(null)}
        />
      )}
    </div>
  )
}

// ============== Main App ==============
function App() {
  const [user, setUser] = useState(() => {
    // Check for stored user from real auth
    const storedUser = getStoredUser()
    if (storedUser && isAuthenticated()) {
      return {
        username: storedUser.username,
        role: storedUser.role,
        name: storedUser.full_name || storedUser.username,
        email: storedUser.email,
        id: storedUser.id
      }
    }
    return null
  })

  const handleLogin = (userData) => {
    setUser(userData)
  }

  const handleLogout = () => {
    apiLogout()
    setUser(null)
  }

  if (!user) {
    return <LoginPage onLogin={handleLogin} />
  }

  return <Dashboard user={user} onLogout={handleLogout} />
}

export default App
