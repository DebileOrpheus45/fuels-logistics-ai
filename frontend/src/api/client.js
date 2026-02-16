import axios from 'axios'

// Use environment variable or fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

// Token storage key
const TOKEN_KEY = 'fuels_auth_token'
const USER_KEY = 'fuels_auth_user'

// Get stored token
const getStoredToken = () => localStorage.getItem(TOKEN_KEY)

const api = axios.create({
  baseURL: API_BASE_URL
})

// Add auth header interceptor
api.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auto-redirect to login on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

// Auth functions
export const login = async (username, password) => {
  const formData = new URLSearchParams()
  formData.append('username', username)
  formData.append('password', password)

  const response = await axios.post(`${API_BASE_URL}/auth/login`, formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })

  const { access_token } = response.data
  localStorage.setItem(TOKEN_KEY, access_token)

  const userResponse = await axios.get(`${API_BASE_URL}/auth/me`, {
    headers: { Authorization: `Bearer ${access_token}` }
  })
  localStorage.setItem(USER_KEY, JSON.stringify(userResponse.data))

  return userResponse.data
}

export const logout = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export const getStoredUser = () => {
  const user = localStorage.getItem(USER_KEY)
  return user ? JSON.parse(user) : null
}

export const isAuthenticated = () => {
  return !!getStoredToken()
}

export const getCurrentUser = () => api.get('/auth/me').then(res => res.data)

// Dashboard
export const getDashboardStats = () => api.get('/dashboard/stats').then(res => res.data)

// Sites
export const getSites = (params = {}) => {
  const queryParams = new URLSearchParams()
  if (params.customer) queryParams.append('customer', params.customer)
  if (params.service_type) queryParams.append('service_type', params.service_type)
  const query = queryParams.toString()
  return api.get(`/sites/${query ? `?${query}` : ''}`).then(res => res.data)
}
export const getSitesInventoryStatus = () => api.get('/sites/inventory-status').then(res => res.data)
export const updateSite = (id, data) => api.patch(`/sites/${id}`, data).then(res => res.data)
export const batchUpdateSites = (customer, erpSource, sites) =>
  api.post('/sites/batch-update', { customer, erp_source: erpSource, sites }).then(res => res.data)
export const exportSiteTemplate = (customer) =>
  api.get(`/sites/export-template${customer ? `?customer=${customer}` : ''}`).then(res => res.data)

// Site Metadata (Customers, ERPs, Service Types)
export const getCustomers = () => api.get('/sites/customers').then(res => res.data)
export const getErpSources = () => api.get('/sites/erp-sources').then(res => res.data)
export const getServiceTypes = () => api.get('/sites/service-types').then(res => res.data)
export const getErpTemplate = (erpSource) => api.get(`/sites/erp-templates/${erpSource}`).then(res => res.data)
export const getUploadHistory = (customer) =>
  api.get(`/sites/upload-history${customer ? `?customer=${customer}` : ''}`).then(res => res.data)

// Loads
export const getLoads = () => api.get('/loads/').then(res => res.data)
export const getActiveLoads = () => api.get('/loads/active').then(res => res.data)
export const addNoteToLoad = (loadId, noteText, author, noteType = 'human') =>
  api.post(`/loads/${loadId}/notes`, null, {
    params: { note_text: noteText, author, note_type: noteType }
  }).then(res => res.data)
export const requestEtaForLoad = (loadId) => api.post(`/loads/${loadId}/request-eta`).then(res => res.data)
export const requestEtaForAllLoads = () => api.post('/loads/request-eta-all').then(res => res.data)

// Carriers
export const getCarriers = () => api.get('/carriers/').then(res => res.data)

// Agents
export const getAgents = () => api.get('/agents/').then(res => res.data)
export const getAgent = (id) => api.get(`/agents/${id}`).then(res => res.data)
export const updateAgent = (id, data) => api.patch(`/agents/${id}`, data).then(res => res.data)
export const runAgentCheck = (id) => api.post(`/agents/${id}/run-check`).then(res => res.data)
export const startAgent = (id) => api.post(`/agents/${id}/start`).then(res => res.data)
export const stopAgent = (id) => api.post(`/agents/${id}/stop`).then(res => res.data)
export const getAgentActivities = (id) => api.get(`/agents/${id}/activities`).then(res => res.data)
export const getAllActivities = (limit = 100) => api.get(`/agents/activities/all?limit=${limit}`).then(res => res.data)
export const getAgentRunHistory = (id, limit = 20) =>
  api.get(`/agents/${id}/run-history?limit=${limit}`).then(res => res.data)
export const getRecentRunHistory = (limit = 20) =>
  api.get(`/agents/run-history/recent?limit=${limit}`).then(res => res.data)
export const assignSitesToAgent = (agentId, siteIds) =>
  api.post(`/agents/${agentId}/assign-sites`, { site_ids: siteIds }).then(res => res.data)

// Escalations
export const getEscalations = () => api.get('/escalations/').then(res => res.data)
export const getOpenEscalations = () => api.get('/escalations/open').then(res => res.data)
export const resolveEscalation = (id, notes) =>
  api.patch(`/escalations/${id}`, { status: 'resolved', resolution_notes: notes }).then(res => res.data)

// Emails
export const getSentEmails = () => api.get('/emails/sent').then(res => res.data)
export const getInboundEmails = () => api.get('/email/inbound').then(res => res.data)

// Intelligence / Knowledge Graph
export const getIntelligence = () => api.get('/intelligence/').then(res => res.data)
export const refreshKnowledgeGraph = () => api.post('/intelligence/refresh').then(res => res.data)
export const getStatusSummary = () => api.get('/intelligence/status-summary').then(res => res.data)

// Google Sheets
export const getSheetsStatus = () => api.get('/sheets/status').then(res => res.data)
export const syncToSheets = (spreadsheetUrl, sites, loads) =>
  api.post('/sheets/sync', { spreadsheet_url: spreadsheetUrl, sites, loads }).then(res => res.data)

export default api
