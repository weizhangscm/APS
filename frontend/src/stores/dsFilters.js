import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ordersApi } from '@/api'
import dayjs from 'dayjs'

/**
 * DS数据共享Store
 * DS资源、DS产品、DS工艺路线、DS切换矩阵、DS订单数据 是数据源
 * 详细计划表 从这些DS数据中获取数据并进行筛选显示
 */
export const useDSFiltersStore = defineStore('dsFilters', () => {
  // ===== DS数据源（全部数据）=====
  // DS资源数据
  const dsResources = ref([])
  
  // DS产品数据
  const dsProducts = ref([])
  
  // DS工艺路线数据（从masterData store获取，这里存储引用）
  const dsRoutings = ref([])
  
  // DS切换组数据
  const dsSetupGroups = ref([])
  
  // DS产品分配数据
  const dsProductAssignments = ref([])
  
  // DS订单数据
  const dsOrders = ref([])
  
  // 订单加载状态
  const ordersLoading = ref(false)
  
  // ===== 详细计划表筛选条件 =====
  // 选中的资源ID列表
  const selectedResourceIds = ref([])
  
  // 选中的产品ID列表
  const selectedProductIds = ref([])
  
  // 日期范围
  const dateRange = ref([])
  
  // 是否只显示瓶颈资源
  const bottleneckOnly = ref(true)

  // ===== 计算属性 =====
  // 是否有筛选条件
  const hasFilters = computed(() => {
    return selectedResourceIds.value.length > 0 || selectedProductIds.value.length > 0
  })

  // 详细计划表的资源选项（来自DS资源）
  const resourceOptions = computed(() => {
    return dsResources.value.map(r => ({
      id: r.id,
      name: r.name,
      is_bottleneck: r.is_bottleneck || false
    }))
  })

  // 详细计划表的产品选项（来自DS产品）
  const productOptions = computed(() => {
    return dsProducts.value.map(p => ({
      id: p.id,
      name: p.product_description || p.product_code
    }))
  })

  // 选中的资源名称列表
  const selectedResourceNames = computed(() => {
    return selectedResourceIds.value.map(id => {
      const resource = dsResources.value.find(r => r.id === id)
      return resource ? resource.name : `资源 ${id}`
    })
  })

  // 选中的产品名称列表
  const selectedProductNames = computed(() => {
    return selectedProductIds.value.map(id => {
      const product = dsProducts.value.find(p => p.id === id)
      return product ? (product.product_description || product.product_code) : `产品 ${id}`
    })
  })

  // 根据筛选条件过滤后的订单（供详细计划表使用）
  const filteredDSOrders = computed(() => {
    // 如果没有选择产品，返回所有DS订单
    if (!selectedProductIds.value || selectedProductIds.value.length === 0) {
      return dsOrders.value
    }
    // 否则只返回选中产品的订单
    return dsOrders.value.filter(o => selectedProductIds.value.includes(o.product_id))
  })

  // 根据筛选条件过滤后的资源（供详细计划表使用）
  const filteredDSResources = computed(() => {
    // 如果没有选择资源，返回所有DS资源
    if (!selectedResourceIds.value || selectedResourceIds.value.length === 0) {
      return dsResources.value
    }
    // 否则只返回选中的资源
    return dsResources.value.filter(r => selectedResourceIds.value.includes(r.id))
  })

  // 根据筛选条件过滤后的产品（供详细计划表使用）
  const filteredDSProducts = computed(() => {
    // 如果没有选择产品，返回所有DS产品
    if (!selectedProductIds.value || selectedProductIds.value.length === 0) {
      return dsProducts.value
    }
    // 否则只返回选中的产品
    return dsProducts.value.filter(p => selectedProductIds.value.includes(p.id))
  })

  // ===== DS数据设置方法（各DS页面调用）=====
  // 设置DS资源数据
  function setDSResources(data) {
    dsResources.value = data || []
  }

  // 设置DS产品数据
  function setDSProducts(data) {
    dsProducts.value = data || []
  }

  // 设置DS工艺路线数据
  function setDSRoutings(data) {
    dsRoutings.value = data || []
  }

  // 设置DS切换组数据
  function setDSSetupGroups(data) {
    dsSetupGroups.value = data || []
  }

  // 设置DS产品分配数据
  function setDSProductAssignments(data) {
    dsProductAssignments.value = data || []
  }

  // 加载DS订单数据
  async function fetchDSOrders(status = null, orderType = null) {
    ordersLoading.value = true
    try {
      const orders = await ordersApi.getOrders(status, orderType)
      // 处理订单数据：当工序的计划开始/计划结束为空时，使用交货日期填充
      dsOrders.value = orders.map(order => {
        if (order.operations && order.operations.length > 0 && order.due_date) {
          const dueDate = dayjs(order.due_date)
          order.operations = order.operations.map(op => {
            // 如果计划开始为空，使用交货日期的08:00
            if (!op.scheduled_start) {
              op.scheduled_start = dueDate.format('YYYY-MM-DD') + 'T08:00:00'
            }
            // 如果计划结束为空，使用交货日期的18:00
            if (!op.scheduled_end) {
              op.scheduled_end = dueDate.format('YYYY-MM-DD') + 'T18:00:00'
            }
            return op
          })
        }
        return order
      })
    } catch (error) {
      console.error('Failed to fetch DS orders:', error)
    } finally {
      ordersLoading.value = false
    }
  }

  // ===== 详细计划表筛选条件设置方法 =====
  // 设置资源筛选
  function setSelectedResources(ids) {
    selectedResourceIds.value = ids || []
  }

  // 设置产品筛选
  function setSelectedProducts(ids) {
    selectedProductIds.value = ids || []
  }

  // 设置日期范围
  function setDateRange(range) {
    dateRange.value = range || []
  }

  // 设置瓶颈资源筛选
  function setBottleneckOnly(value) {
    bottleneckOnly.value = value
  }

  // 清除所有筛选条件
  function clearFilters() {
    selectedResourceIds.value = []
    selectedProductIds.value = []
  }

  // 从 localStorage 恢复筛选条件
  function restoreFromStorage() {
    try {
      const stored = localStorage.getItem('ds_view_filters')
      if (stored) {
        const filters = JSON.parse(stored)
        const now = Date.now()
        // 检查是否过期（10分钟）
        if (now - filters.timestamp <= 10 * 60 * 1000) {
          selectedResourceIds.value = filters.selectedResources || []
          selectedProductIds.value = filters.selectedProducts || []
          dateRange.value = filters.dateRange || []
          bottleneckOnly.value = filters.bottleneckOnly ?? true
        }
      }
    } catch (e) {
      console.warn('Failed to restore filters from localStorage:', e)
    }
  }

  return {
    // DS数据源（全部数据）
    dsResources,
    dsProducts,
    dsRoutings,
    dsSetupGroups,
    dsProductAssignments,
    dsOrders,
    ordersLoading,
    // 详细计划表筛选条件
    selectedResourceIds,
    selectedProductIds,
    dateRange,
    bottleneckOnly,
    // 计算属性
    hasFilters,
    resourceOptions,
    productOptions,
    selectedResourceNames,
    selectedProductNames,
    filteredDSOrders,
    filteredDSResources,
    filteredDSProducts,
    // DS数据设置方法
    setDSResources,
    setDSProducts,
    setDSRoutings,
    setDSSetupGroups,
    setDSProductAssignments,
    fetchDSOrders,
    // 详细计划表筛选方法
    setSelectedResources,
    setSelectedProducts,
    setDateRange,
    setBottleneckOnly,
    clearFilters,
    restoreFromStorage
  }
})
