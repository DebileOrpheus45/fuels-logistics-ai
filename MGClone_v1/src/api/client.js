import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

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

// Carriers
export const getCarriers = () => api.get('/carriers/').then(res => res.data)

// Agents
export const getAgents = () => api.get('/agents/').then(res => res.data)
export const getAgent = (id) => api.get(`/agents/${id}`).then(res => res.data)
export const runAgentCheck = (id) => api.post(`/agents/${id}/run-check`).then(res => res.data)
export const startAgent = (id) => api.post(`/agents/${id}/start`).then(res => res.data)
export const stopAgent = (id) => api.post(`/agents/${id}/stop`).then(res => res.data)
export const getAgentActivities = (id) => api.get(`/agents/${id}/activities`).then(res => res.data)
export const assignSitesToAgent = (agentId, siteIds) =>
  api.post(`/agents/${agentId}/assign-sites`, { site_ids: siteIds }).then(res => res.data)

// Escalations
export const getEscalations = () => api.get('/escalations/').then(res => res.data)
export const getOpenEscalations = () => api.get('/escalations/open').then(res => res.data)
export const resolveEscalation = (id, notes) =>
  api.patch(`/escalations/${id}`, { status: 'resolved', resolution_notes: notes }).then(res => res.data)

// Emails
export const getSentEmails = () => api.get('/emails/sent').then(res => res.data)

export default api
