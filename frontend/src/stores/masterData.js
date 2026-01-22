import { defineStore } from 'pinia'
import { ref } from 'vue'
import { masterDataApi, ordersApi } from '@/api'

export const useMasterDataStore = defineStore('masterData', () => {
  // State
  const workCenters = ref([])
  const resources = ref([])
  const products = ref([])
  const routings = ref([])
  const orders = ref([])
  const loading = ref(false)

  // Work Centers
  async function fetchWorkCenters() {
    loading.value = true
    try {
      workCenters.value = await masterDataApi.getWorkCenters()
    } finally {
      loading.value = false
    }
  }

  async function createWorkCenter(data) {
    const result = await masterDataApi.createWorkCenter(data)
    await fetchWorkCenters()
    return result
  }

  async function updateWorkCenter(id, data) {
    const result = await masterDataApi.updateWorkCenter(id, data)
    await fetchWorkCenters()
    return result
  }

  async function deleteWorkCenter(id) {
    await masterDataApi.deleteWorkCenter(id)
    await fetchWorkCenters()
  }

  // Resources
  async function fetchResources(workCenterId = null) {
    loading.value = true
    try {
      resources.value = await masterDataApi.getResources(workCenterId)
    } finally {
      loading.value = false
    }
  }

  async function createResource(data) {
    const result = await masterDataApi.createResource(data)
    await fetchResources()
    return result
  }

  async function updateResource(id, data) {
    const result = await masterDataApi.updateResource(id, data)
    await fetchResources()
    return result
  }

  async function deleteResource(id) {
    await masterDataApi.deleteResource(id)
    await fetchResources()
  }

  // Products
  async function fetchProducts() {
    loading.value = true
    try {
      products.value = await masterDataApi.getProducts()
    } finally {
      loading.value = false
    }
  }

  async function createProduct(data) {
    const result = await masterDataApi.createProduct(data)
    await fetchProducts()
    return result
  }

  async function updateProduct(id, data) {
    const result = await masterDataApi.updateProduct(id, data)
    await fetchProducts()
    return result
  }

  async function deleteProduct(id) {
    await masterDataApi.deleteProduct(id)
    await fetchProducts()
  }

  // Routings
  async function fetchRoutings(productId = null) {
    loading.value = true
    try {
      routings.value = await masterDataApi.getRoutings(productId)
    } finally {
      loading.value = false
    }
  }

  async function createRouting(data) {
    const result = await masterDataApi.createRouting(data)
    await fetchRoutings()
    return result
  }

  async function updateRouting(id, data) {
    const result = await masterDataApi.updateRouting(id, data)
    await fetchRoutings()
    return result
  }

  async function deleteRouting(id) {
    await masterDataApi.deleteRouting(id)
    await fetchRoutings()
  }

  // Routing Operations
  async function createRoutingOperation(routingId, data) {
    const result = await masterDataApi.createRoutingOperation(routingId, data)
    await fetchRoutings()
    return result
  }

  async function updateRoutingOperation(id, data) {
    const result = await masterDataApi.updateRoutingOperation(id, data)
    await fetchRoutings()
    return result
  }

  async function deleteRoutingOperation(id) {
    await masterDataApi.deleteRoutingOperation(id)
    await fetchRoutings()
  }

  // Orders
  async function fetchOrders(status = null, orderType = null) {
    loading.value = true
    try {
      orders.value = await ordersApi.getOrders(status, orderType)
    } finally {
      loading.value = false
    }
  }

  async function createOrder(data) {
    const result = await ordersApi.createOrder(data)
    await fetchOrders()
    return result
  }

  async function updateOrder(id, data) {
    const result = await ordersApi.updateOrder(id, data)
    await fetchOrders()
    return result
  }

  async function deleteOrder(id) {
    await ordersApi.deleteOrder(id)
    await fetchOrders()
  }

  return {
    // State
    workCenters,
    resources,
    products,
    routings,
    orders,
    loading,
    // Work Center actions
    fetchWorkCenters,
    createWorkCenter,
    updateWorkCenter,
    deleteWorkCenter,
    // Resource actions
    fetchResources,
    createResource,
    updateResource,
    deleteResource,
    // Product actions
    fetchProducts,
    createProduct,
    updateProduct,
    deleteProduct,
    // Routing actions
    fetchRoutings,
    createRouting,
    updateRouting,
    deleteRouting,
    // Routing Operation actions
    createRoutingOperation,
    updateRoutingOperation,
    deleteRoutingOperation,
    // Order actions
    fetchOrders,
    createOrder,
    updateOrder,
    deleteOrder
  }
})
