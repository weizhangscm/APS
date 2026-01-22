import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { schedulingApi } from '@/api'

export const useSchedulingStore = defineStore('scheduling', () => {
  // State
  const ganttData = ref({ data: [], links: [] })
  const kpiData = ref(null)
  const loading = ref(false)
  const conflicts = ref([])
  const currentViewType = ref('order')

  // Actions
  async function fetchGanttData(viewType = 'order') {
    loading.value = true
    try {
      currentViewType.value = viewType
      const data = await schedulingApi.getGanttData(viewType)
      ganttData.value = data
    } catch (error) {
      console.error('Failed to fetch gantt data:', error)
    } finally {
      loading.value = false
    }
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

  return {
    // State
    ganttData,
    kpiData,
    loading,
    conflicts,
    currentViewType,
    // Actions
    fetchGanttData,
    runScheduling,
    clearScheduling,
    rescheduleOperation,
    fetchKPIData,
    validateScheduling
  }
})
