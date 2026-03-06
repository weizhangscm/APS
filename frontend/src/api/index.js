import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor - add auth token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    // 401 错误时清除 token 并跳转登录页
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Auth APIs
export const authApi = {
  login: (username, password) => {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    return api.post('/auth/login', null, { params })
  },
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/auth/me'),
  changePassword: (oldPassword, newPassword) => {
    const params = new URLSearchParams()
    params.append('old_password', oldPassword)
    params.append('new_password', newPassword)
    return api.post('/auth/change-password', null, { params })
  }
}

// Master Data APIs
export const masterDataApi = {
  // Work Centers
  getWorkCenters: () => api.get('/master-data/work-centers'),
  getWorkCenter: (id) => api.get(`/master-data/work-centers/${id}`),
  createWorkCenter: (data) => api.post('/master-data/work-centers', data),
  updateWorkCenter: (id, data) => api.put(`/master-data/work-centers/${id}`, data),
  deleteWorkCenter: (id) => api.delete(`/master-data/work-centers/${id}`),
  
  // Resources
  getResources: (workCenterId = null) => {
    const params = workCenterId ? { work_center_id: workCenterId } : {}
    return api.get('/master-data/resources', { params })
  },
  getResource: (id) => api.get(`/master-data/resources/${id}`),
  createResource: (data) => api.post('/master-data/resources', data),
  updateResource: (id, data) => api.put(`/master-data/resources/${id}`, data),
  deleteResource: (id) => api.delete(`/master-data/resources/${id}`),

  // Shifts 班次
  getShifts: (resourceId = null) => {
    const params = resourceId ? { resource_id: resourceId } : {}
    return api.get('/master-data/shifts', { params })
  },
  createShift: (data) => api.post('/master-data/shifts', data),
  updateShift: (id, data) => api.put(`/master-data/shifts/${id}`, data),
  deleteShift: (id) => api.delete(`/master-data/shifts/${id}`),
  
  // Products
  getProducts: () => api.get('/master-data/products'),
  getProduct: (id) => api.get(`/master-data/products/${id}`),
  createProduct: (data) => api.post('/master-data/products', data),
  updateProduct: (id, data) => api.put(`/master-data/products/${id}`, data),
  deleteProduct: (id) => api.delete(`/master-data/products/${id}`),
  
  // Routings
  getRoutings: (productId = null) => {
    const params = productId ? { product_id: productId } : {}
    return api.get('/master-data/routings', { params })
  },
  getRouting: (id) => api.get(`/master-data/routings/${id}`),
  createRouting: (data) => api.post('/master-data/routings', data),
  updateRouting: (id, data) => api.put(`/master-data/routings/${id}`, data),
  deleteRouting: (id) => api.delete(`/master-data/routings/${id}`),
  
  // Routing Operations
  createRoutingOperation: (routingId, data) => api.post(`/master-data/routings/${routingId}/operations`, data),
  updateRoutingOperation: (id, data) => api.put(`/master-data/routing-operations/${id}`, data),
  deleteRoutingOperation: (id) => api.delete(`/master-data/routing-operations/${id}`)
}

// Orders APIs
export const ordersApi = {
  getOrders: (status = null, orderType = null) => {
    const params = {}
    if (status) params.status = status
    if (orderType) params.order_type = orderType
    return api.get('/orders/', { params })
  },
  getOrder: (id) => api.get(`/orders/${id}`),
  createOrder: (data) => api.post('/orders/', data),
  updateOrder: (id, data) => api.put(`/orders/${id}`, data),
  deleteOrder: (id) => api.delete(`/orders/${id}`),
  getOrderOperations: (orderId) => api.get(`/orders/${orderId}/operations`),
  updateOperation: (id, data) => api.put(`/orders/operations/${id}`, data),
  convertToProduction: (id, data = null) => api.post(`/orders/${id}/convert-to-production`, data)
}

// Scheduling APIs
export const schedulingApi = {
  runScheduling: (data) => api.post('/scheduling/run', data),
  clearScheduling: (orderIds = null) => api.post('/scheduling/clear', orderIds ? { order_ids: orderIds } : null),
  rescheduleOperation: (data) => api.post('/scheduling/reschedule-operation', data),
  getGanttData: (viewType = 'order', startDate = null, endDate = null) => {
    const params = { view_type: viewType }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    return api.get('/scheduling/gantt-data', { params })
  },
  validateScheduling: (orderIds = null) => {
    const params = orderIds ? { order_ids: orderIds.join(',') } : {}
    return api.get('/scheduling/validate', { params })
  },
  getKPI: (params = {}) => api.get('/scheduling/kpi', { params }),
  rescheduleResource: (data) => api.post('/scheduling/reschedule-resource', data),
  autoPlan: (data) => api.post('/scheduling/auto-plan', data),
  // 取消计划 - 根据资源和/或产品清除排程
  cancelPlan: (resourceIds = null, productIds = null) => api.post('/scheduling/cancel-plan', {
    resource_ids: resourceIds,
    product_ids: productIds
  }),
  // 保存计划 - 将缓存的排程数据写入数据库
  savePlan: (resourceIds = null, productIds = null) => api.post('/scheduling/save-plan', {
    resource_ids: resourceIds,
    product_ids: productIds
  }),
  // 丢弃计划 - 清除缓存的预览排程数据
  discardPlan: () => api.post('/scheduling/discard-plan'),
  // 获取缓存状态 - 检查是否有未保存的排程
  getCacheStatus: () => api.get('/scheduling/cache-status'),
  // 新增：获取资源利用率数据
  getUtilizationData: (resourceIds = [], startDate = null, endDate = null, zoomLevel = 1) => {
    const params = {}
    if (resourceIds && resourceIds.length > 0) params.resource_ids = resourceIds.join(',')
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    params.zoom_level = zoomLevel  // 0=小时, 1=4小时, 2=天, 3=周, 4=月
    return api.get('/scheduling/utilization', { params })
  },
  // 新增：联动调整工序（支持策略）
  rescheduleWithLinks: (data) => api.post('/scheduling/reschedule-with-links', data)
}

// Chatbot APIs
export const chatbotApi = {
  sendMessage: (message, context = {}) => api.post('/chatbot/chat', { message, context }),
  getHistory: () => api.get('/chatbot/history')
}

// Setup Matrix APIs (切换矩阵)
export const setupMatrixApi = {
  // Setup Groups
  getSetupGroups: () => api.get('/setup-matrix/groups'),
  getSetupGroup: (id) => api.get(`/setup-matrix/groups/${id}`),
  createSetupGroup: (data) => api.post('/setup-matrix/groups', data),
  updateSetupGroup: (id, data) => api.put(`/setup-matrix/groups/${id}`, data),
  deleteSetupGroup: (id) => api.delete(`/setup-matrix/groups/${id}`),
  
  // Product Setup Group Assignments
  getProductAssignments: (params = {}) => api.get('/setup-matrix/product-assignments', { params }),
  assignProductToGroup: (data) => api.post('/setup-matrix/product-assignments', data),
  removeProductAssignment: (id) => api.delete(`/setup-matrix/product-assignments/${id}`),
  
  // Setup Matrix Entries
  getMatrixEntries: (params = {}) => api.get('/setup-matrix/matrix', { params }),
  getMatrixGrid: (resourceId = null, workCenterId = null) => {
    const params = {}
    if (resourceId !== null) params.resource_id = resourceId
    if (workCenterId !== null) params.work_center_id = workCenterId
    return api.get('/setup-matrix/matrix/grid', { params })
  },
  createMatrixEntry: (data) => api.post('/setup-matrix/matrix', data),
  batchUpdateMatrix: (entries) => api.post('/setup-matrix/matrix/batch', entries),
  deleteMatrixEntry: (id) => api.delete(`/setup-matrix/matrix/${id}`),
  
  // Query changeover time
  getChangeoverTime: (fromProductId, toProductId, resourceId = null, workCenterId = null) => {
    const params = { from_product_id: fromProductId, to_product_id: toProductId }
    if (resourceId) params.resource_id = resourceId
    if (workCenterId) params.work_center_id = workCenterId
    return api.get('/setup-matrix/changeover-time', { params })
  }
}

export default api
