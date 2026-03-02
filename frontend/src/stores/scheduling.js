import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { schedulingApi } from '@/api'

export const useSchedulingStore = defineStore('scheduling', () => {
  // State
  const ganttData = ref({ data: [], links: [] })
  const productGanttData = ref({ data: [], links: [] })
  const utilizationData = ref([])
  const kpiData = ref(null)
  const loading = ref(false)
  const conflicts = ref([])
  const currentViewType = ref('order')
  const hasUnsavedChanges = ref(false)  // 是否有未保存的排程更改
  const planLog = ref(null)  // 最近一次自动计划/启发式的结果，用于「日志」展示（含错误详情）

  // Actions
  async function fetchGanttData(viewType = 'order', startDate = null, endDate = null) {
    loading.value = true
    try {
      currentViewType.value = viewType
      const data = await schedulingApi.getGanttData(viewType, startDate, endDate)
      ganttData.value = data
      // 更新未保存更改状态
      if (data.has_unsaved_changes !== undefined) {
        hasUnsavedChanges.value = data.has_unsaved_changes
      }
    } catch (error) {
      console.error('Failed to fetch gantt data:', error)
    } finally {
      loading.value = false
    }
  }

  // 获取产品视图甘特图数据
  async function fetchProductGanttData(startDate = null, endDate = null) {
    loading.value = true
    try {
      const data = await schedulingApi.getGanttData('product', startDate, endDate)
      productGanttData.value = data
    } catch (error) {
      console.error('Failed to fetch product gantt data:', error)
    } finally {
      loading.value = false
    }
  }

  // 获取资源利用率数据
  async function fetchUtilizationData(resourceIds = [], startDate = null, endDate = null, zoomLevel = 1) {
    loading.value = true
    try {
      const response = await schedulingApi.getUtilizationData(resourceIds, startDate, endDate, zoomLevel)
      // 后端返回 {"data": [...]} 格式，提取 data 数组
      utilizationData.value = response.data || []
    } catch (error) {
      console.error('Failed to fetch utilization data:', error)
      // 返回模拟数据用于开发
      utilizationData.value = generateMockUtilizationData(resourceIds, startDate, endDate)
    } finally {
      loading.value = false
    }
  }

  // 生成模拟利用率数据
  function generateMockUtilizationData(resourceIds, startDate, endDate) {
    return resourceIds.map(id => ({
      resource_id: id,
      resource_name: `资源 ${id}`,
      description: '',
      capacity: 24,
      time_slots: []
    }))
  }

  async function runScheduling(options = {}) {
    loading.value = true
    try {
      const result = await schedulingApi.runScheduling({
        order_ids: options.orderIds || null,
        direction: options.direction || 'forward',
        consider_capacity: options.considerCapacity !== false,
        priority_rule: options.priorityRule || 'EDD'
      })
      conflicts.value = result.conflicts || []
      await fetchGanttData(currentViewType.value)
      return result
    } catch (error) {
      console.error('Scheduling failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function clearScheduling(orderIds = null) {
    loading.value = true
    try {
      await schedulingApi.clearScheduling(orderIds)
      await fetchGanttData(currentViewType.value)
    } catch (error) {
      console.error('Clear scheduling failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function rescheduleOperation(operationId, newStart, newResourceId = null) {
    try {
      const result = await schedulingApi.rescheduleOperation({
        operation_id: operationId,
        new_start: newStart,
        new_resource_id: newResourceId
      })
      if (result.success) {
        await fetchGanttData(currentViewType.value)
      }
      return result
    } catch (error) {
      console.error('Reschedule failed:', error)
      throw error
    }
  }

  // 新增：支持策略的联动调整
  async function rescheduleOperationWithStrategy(operationId, newStart, newResourceId = null, strategy = 'EDD', moveLinkedOperations = true) {
    try {
      const result = await schedulingApi.rescheduleWithLinks({
        operation_id: operationId,
        new_start: newStart,
        new_resource_id: newResourceId,
        strategy: strategy,
        move_linked_operations: moveLinkedOperations
      })
      if (result.success) {
        await fetchGanttData(currentViewType.value)
      }
      return result
    } catch (error) {
      console.error('Reschedule with strategy failed:', error)
      // 降级到普通调整
      return rescheduleOperation(operationId, newStart, newResourceId)
    }
  }

  async function fetchKPIData() {
    try {
      kpiData.value = await schedulingApi.getKPI()
    } catch (error) {
      console.error('Failed to fetch KPI data:', error)
    }
  }

  async function validateScheduling(orderIds = null) {
    try {
      return await schedulingApi.validateScheduling(orderIds)
    } catch (error) {
      console.error('Validation failed:', error)
      throw error
    }
  }

  async function rescheduleResource(resourceIds, strategy) {
    loading.value = true
    try {
      const result = await schedulingApi.rescheduleResource({
        resource_ids: resourceIds,
        strategy: strategy
      })
      await fetchGanttData(currentViewType.value)
      return result
    } catch (error) {
      console.error('Reschedule resource failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function autoPlan(planType, heuristicId = null, optimizerConfig = null, resourceIds = null) {
    loading.value = true
    let planLogSetThisRun = false
    try {
      const result = await schedulingApi.autoPlan({
        plan_type: planType,
        heuristic_id: heuristicId,
        optimizer_config: optimizerConfig,
        resource_ids: resourceIds
      })
      // 更新缓存状态（立即终止且失败时后端返回 has_unsaved_changes: false）
      if (result.has_unsaved_changes !== undefined) {
        hasUnsavedChanges.value = result.has_unsaved_changes
      }
      // 记录本次结果供「日志」查看（含 success、message、details）；先写入再刷新甘特，避免后续 fetch 报错覆盖日志
      planLog.value = {
        success: result.success,
        message: result.message,
        details: result.details || [],
        scheduled_orders: result.scheduled_orders,
        scheduled_operations: result.scheduled_operations,
        timestamp: new Date().toLocaleString()
      }
      planLogSetThisRun = true
      await fetchGanttData(currentViewType.value)
      return result
    } catch (error) {
      console.error('Auto plan failed:', error)
      // 仅当本次未拿到启发式结果时才写入错误日志，避免 fetchGanttData 失败覆盖掉已有的排程错误详情
      if (!planLogSetThisRun) {
        planLog.value = {
          success: false,
          message: error?.response?.data?.message || error?.message || '请求失败',
          details: [],
          timestamp: new Date().toLocaleString()
        }
      }
      throw error
    } finally {
      loading.value = false
    }
  }

  async function cancelPlan(resourceIds = null, productIds = null) {
    loading.value = true
    try {
      const result = await schedulingApi.cancelPlan(resourceIds, productIds)
      await fetchGanttData(currentViewType.value)
      return result
    } catch (error) {
      console.error('Cancel plan failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function savePlan(resourceIds = null, productIds = null) {
    loading.value = true
    try {
      const result = await schedulingApi.savePlan(resourceIds, productIds)
      hasUnsavedChanges.value = false
      await fetchGanttData(currentViewType.value)
      return result
    } catch (error) {
      console.error('Save plan failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 丢弃计划 - 清除缓存的预览排程数据
  async function discardPlan() {
    loading.value = true
    try {
      const result = await schedulingApi.discardPlan()
      hasUnsavedChanges.value = false
      await fetchGanttData(currentViewType.value)
      return result
    } catch (error) {
      console.error('Discard plan failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // 获取缓存状态
  async function getCacheStatus() {
    try {
      const result = await schedulingApi.getCacheStatus()
      hasUnsavedChanges.value = result.has_unsaved_changes
      return result
    } catch (error) {
      console.error('Get cache status failed:', error)
      return { has_unsaved_changes: false }
    }
  }

  return {
    // State
    ganttData,
    productGanttData,
    utilizationData,
    kpiData,
    loading,
    conflicts,
    currentViewType,
    hasUnsavedChanges,
    planLog,
    // Actions
    fetchGanttData,
    fetchProductGanttData,
    fetchUtilizationData,
    runScheduling,
    clearScheduling,
    rescheduleOperation,
    rescheduleOperationWithStrategy,
    fetchKPIData,
    validateScheduling,
    rescheduleResource,
    autoPlan,
    cancelPlan,
    savePlan,
    discardPlan,
    getCacheStatus
  }
})
