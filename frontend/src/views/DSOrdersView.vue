<template>
  <div class="orders-page">
    <div class="page-header">
      <h1>
        <el-icon><Document /></el-icon>
        {{ t('orders.productionPlanningOrders') }}
      </h1>
      <div class="header-actions">
        <DataExcelToolbar
          :entities="[{ id: 'production_orders', labelKey: 'dataManagement.productionOrders' }]"
          @imported="fetchData"
        />
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          {{ t('orders.addPlannedOrder') }}
        </el-button>
      </div>
    </div>
    
    <!-- Filter -->
    <el-card class="filter-card">
      <el-form :inline="true" class="filter-form">
        <el-form-item v-if="filterVisibility.orderNumber" :label="t('orders.orderNumber')">
          <el-input
            v-model="filterOrderNumber"
            :placeholder="t('orders.enterOrderNumber')"
            style="width: 180px"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item v-if="filterVisibility.location" :label="t('orders.location')">
          <el-select
            v-model="filterLocationCodes"
            multiple
            collapse-tags
            collapse-tags-tooltip
            :placeholder="t('orders.selectLocations')"
            clearable
            filterable
            style="width: 220px"
            @change="onFilterLocationChange"
          >
            <template #header>
              <div class="select-header-options">
                <el-checkbox
                  v-model="allOrderFilterLocationsSelected"
                  :indeterminate="orderFilterLocationsIndeterminate"
                  @change="handleSelectAllOrderFilterLocations"
                >
                  {{ t('orders.selectLocations') }}
                </el-checkbox>
              </div>
            </template>
            <el-option
              v-for="loc in locationOptions"
              :key="loc.code"
              :label="orderLocationOptionLabel(loc)"
              :value="loc.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="filterVisibility.orderType" :label="t('orders.orderType')">
          <el-select v-model="filterOrderType" :placeholder="t('orders.allTypes')" clearable style="width: 150px" @change="fetchData">
            <el-option :label="t('orders.plannedOrder')" value="planned" />
            <el-option :label="t('orders.productionOrder')" value="production" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="filterVisibility.status" :label="t('orders.statusFilter')">
          <el-select v-model="filterStatus" :placeholder="t('orders.allStatuses')" clearable style="width: 150px" @change="fetchData">
            <el-option :label="t('orders.pendingSchedule')" value="created" />
            <el-option :label="t('orders.scheduled')" value="scheduled" />
            <el-option :label="t('orders.inProgress')" value="in_progress" />
            <el-option :label="t('orders.completed')" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="filterVisibility.delayed" :label="t('orders.isDelayed')">
          <el-select v-model="filterDelayed" :placeholder="t('orders.all')" clearable style="width: 120px">
            <el-option :label="t('orders.yes')" :value="true" />
            <el-option :label="t('orders.no')" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="filterVisibility.dueDate" :label="t('orders.dueDate')">
          <el-date-picker
            v-model="filterDueDateRange"
            type="daterange"
            :format="datePickerDisplayFormat"
            :range-separator="t('orders.separator')"
            :start-placeholder="t('orders.startDate')"
            :end-placeholder="t('orders.endDate')"
            style="width: 260px"
            value-format="YYYY-MM-DD"
            :shortcuts="dueDateShortcuts"
            clearable
          />
        </el-form-item>
        <el-form-item v-if="filterVisibility.resource" :label="t('orders.resource')">
          <el-select
            v-model="filterResourceIds"
            multiple
            collapse-tags
            collapse-tags-tooltip
            :placeholder="orderResourceSelectPlaceholder"
            clearable
            filterable
            style="width: 240px"
          >
            <template #header>
              <div class="select-header-options">
                <el-checkbox
                  v-model="allOrderFilterResourcesSelected"
                  :indeterminate="orderFilterResourcesIndeterminate"
                  @change="handleSelectAllOrderFilterResources"
                >
                  {{ t('orders.selectResources') }}
                </el-checkbox>
              </div>
            </template>
            <el-option
              v-for="resource in resourcesForOrderFilter"
              :key="resource.id"
              :label="resource.name"
              :value="resource.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item class="filter-actions-item">
          <el-button :icon="Setting" @click="openAdjustFiltersDialog">
            {{ t('orders.adjustFilters') }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-dialog
      v-model="adjustFiltersDialogVisible"
      :title="t('orders.adjustFilters')"
      width="420px"
      destroy-on-close
    >
      <p class="adjust-filters-hint">{{ t('orders.adjustFiltersHint') }}</p>
      <div class="filter-visibility-checks">
        <el-checkbox v-model="filterVisibilityDraft.orderNumber">{{ t('orders.orderNumber') }}</el-checkbox>
        <el-checkbox v-model="filterVisibilityDraft.location">{{ t('orders.location') }}</el-checkbox>
        <el-checkbox v-model="filterVisibilityDraft.orderType">{{ t('orders.orderType') }}</el-checkbox>
        <el-checkbox v-model="filterVisibilityDraft.status">{{ t('orders.statusFilter') }}</el-checkbox>
        <el-checkbox v-model="filterVisibilityDraft.delayed">{{ t('orders.isDelayed') }}</el-checkbox>
        <el-checkbox v-model="filterVisibilityDraft.dueDate">{{ t('orders.dueDate') }}</el-checkbox>
        <el-checkbox v-model="filterVisibilityDraft.resource">{{ t('orders.resource') }}</el-checkbox>
      </div>
      <template #footer>
        <el-button @click="adjustFiltersDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="confirmAdjustFilters">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <!-- Orders Table -->
    <el-card>
      <el-table :data="filteredOrders" v-loading="loading" stripe table-layout="auto">
        <el-table-column :label="t('orders.type')" min-width="90">
          <template #default="{ row }">
            <el-tag :type="row.order_type === 'production' ? 'info' : 'primary'" effect="plain">
              {{ row.order_type === 'production' ? t('orders.productionOrder') : t('orders.plannedOrder') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="order_number" :label="t('orders.orderNumber')" min-width="130" />
        <el-table-column :label="t('orders.product')" min-width="120">
          <template #default="{ row }">
            {{ row.product?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column :label="t('orders.location')" min-width="90" align="center">
          <template #default="{ row }">
            {{ displayOrderLocation(row) }}
          </template>
        </el-table-column>
        <el-table-column prop="quantity" :label="t('orders.quantity')" min-width="70" align="right" />
        <el-table-column :label="t('orders.dueDate')" min-width="100">
          <template #default="{ row }">
            {{ formatDate(row.due_date) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('orders.estimatedFinishTime')" min-width="180">
          <template #default="{ row }">
            <span v-if="getEstimatedFinishTime(row)">
              {{ formatDateTime(getEstimatedFinishTime(row)) }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column :label="t('orders.isDelayed')" min-width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="isOrderDelayed(row) ? 'danger' : 'success'" size="small">
              {{ isOrderDelayed(row) ? t('orders.yes') : t('orders.no') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" :label="t('orders.priority')" min-width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">
              {{ row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('orders.status')" min-width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(getDisplayOrderStatus(row))" size="small">
              {{ getStatusLabel(getDisplayOrderStatus(row)) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('orders.operations')" min-width="60" align="center">
          <template #default="{ row }">
            {{ row.operations?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column :label="t('orders.actions')" width="280" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" size="small" @click="handleViewOperations(row)">{{ t('orders.viewOperations') }}</el-button>
              <el-button 
                v-if="row.order_type === 'planned'" 
                type="primary" 
                size="small"
                @click="handleEdit(row)"
              >{{ t('orders.edit') }}</el-button>
              <el-button 
                v-if="row.order_type === 'planned' && getDisplayOrderStatus(row) === 'scheduled'" 
                type="primary" 
                size="small"
                @click="handleConvertToProduction(row)"
              >{{ t('orders.convertToProduction') }}</el-button>
              <el-button type="primary" size="small" @click="handleDelete(row)">{{ t('orders.delete') }}</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- Order Edit Dialog -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? t('orders.editPlannedOrder') : t('orders.addPlannedOrder')"
      width="520px"
    >
      <el-form ref="formRef" :model="form" :rules="rulesRef" label-width="100px">
        <el-form-item :label="t('orders.orderNumber')" prop="order_number">
          <el-input
            v-model="form.order_number"
            :disabled="isEdit"
            :placeholder="isEdit ? '' : t('orders.orderNumberOptionalPlaceholder')"
          />
        </el-form-item>
        <el-form-item :label="t('orders.product')" prop="product_id">
          <el-select v-model="form.product_id" :disabled="isEdit" :placeholder="t('orders.selectProduct')" style="width: 100%">
            <el-option 
              v-for="p in products" 
              :key="p.id" 
              :label="`${p.code} - ${p.name}`" 
              :value="p.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.product_id" :label="t('orders.location')">
          <el-input :model-value="productLocationForForm" disabled />
          <div class="form-tip">{{ t('orders.locationFromProductHint') }}</div>
        </el-form-item>
        <el-form-item :label="t('orders.quantity')" prop="quantity">
          <el-input-number v-model="form.quantity" :min="1" :precision="0" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('orders.dueDate')" prop="due_date">
          <el-date-picker 
            v-model="form.due_date" 
            type="datetime"
            :format="dateTimePickerDisplayFormat"
            :placeholder="t('orders.dueDateRequired')"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('orders.earliestStart')">
          <el-date-picker 
            v-model="form.earliest_start" 
            type="datetime"
            :format="dateTimePickerDisplayFormat"
            :placeholder="t('orders.unlimited')"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('orders.priority')" prop="priority">
          <el-slider v-model="form.priority" :min="1" :max="10" :step="1" show-stops show-input />
        </el-form-item>
        <el-form-item :label="t('orders.description')">
          <el-input v-model="form.description" type="textarea" rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <!-- Convert to Production Dialog -->
    <el-dialog 
      v-model="convertDialogVisible" 
      :title="t('orders.convertToProductionTitle')"
      width="480px"
    >
      <el-alert 
        type="warning" 
        :closable="false"
        style="margin-bottom: 16px;"
      >
        {{ t('orders.convertWarning') }}
      </el-alert>
      
      <el-form :model="convertForm" label-width="100px">
        <el-form-item :label="t('orders.confirmedStart')">
          <el-date-picker 
            v-model="convertForm.confirmed_start" 
            type="datetime"
            :format="dateTimePickerDisplayFormat"
            :placeholder="t('orders.useScheduledTime')"
            style="width: 100%"
          />
          <div class="form-tip">{{ t('orders.startTip') }}</div>
        </el-form-item>
        <el-form-item :label="t('orders.confirmedEnd')">
          <el-date-picker 
            v-model="convertForm.confirmed_end" 
            type="datetime"
            :format="dateTimePickerDisplayFormat"
            :placeholder="t('orders.useScheduledTime')"
            style="width: 100%"
          />
          <div class="form-tip">{{ t('orders.endTip') }}</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="convertDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitConvert" :loading="converting">{{ t('orders.confirmConvert') }}</el-button>
      </template>
    </el-dialog>
    
    <!-- Operations Dialog -->
    <el-dialog 
      v-model="opsDialogVisible" 
      :title="`${t('orders.orderOperations')} - ${currentOrder?.order_number || ''}`"
      width="900px"
    >
      <el-descriptions :column="3" border style="margin-bottom: 16px;" v-if="currentOrder">
        <el-descriptions-item :label="t('orders.orderType')">
          <el-tag :type="currentOrder.order_type === 'production' ? 'success' : 'primary'" size="small">
            {{ currentOrder.order_type === 'production' ? t('orders.productionOrder') : t('orders.plannedOrder') }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="t('orders.orderStatus')">
          <el-tag :type="getStatusType(orderStatusInOpsDialog)" size="small">
            {{ getStatusLabel(orderStatusInOpsDialog) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="t('orders.dueDate')">{{ formatDate(currentOrder.due_date) }}</el-descriptions-item>
        <el-descriptions-item :label="t('orders.location')">
          {{ displayOrderLocation(currentOrder) }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('orders.confirmedStart')" v-if="currentOrder.order_type === 'production'">
          {{ formatDateTime(currentOrder.confirmed_start) || '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('orders.confirmedEnd')" v-if="currentOrder.order_type === 'production'">
          {{ formatDateTime(currentOrder.confirmed_end) || '-' }}
        </el-descriptions-item>
      </el-descriptions>
      
      <el-table :data="currentOrder?.operations || []" size="small" table-layout="auto">
        <el-table-column :label="t('masterData.operations')" min-width="140">
          <template #default="{ row }">
            {{ row.sequence }} {{ row.name }}
          </template>
        </el-table-column>
        <el-table-column :label="t('orders.resource')" min-width="100">
          <template #default="{ row }">
            {{ getResourceNameFromRouting(row, currentOrder?.product_id) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('gantt.startTime')" min-width="120">
          <template #default="{ row }">
            {{ row.scheduled_start ? formatDateTime(row.scheduled_start) : '-' }}
          </template>
        </el-table-column>
        <el-table-column :label="t('gantt.endTime')" min-width="120">
          <template #default="{ row }">
            {{ row.scheduled_end ? formatDateTime(row.scheduled_end) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="run_time" :label="t('orders.totalTimeH')" min-width="90" align="right">
          <template #default="{ row }">
            {{ row.run_time.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('orders.status')" min-width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="getOpStatusType(row.status)" size="small">
              {{ getOpStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useMasterDataStore } from '@/stores/masterData'
import { useDSFiltersStore } from '@/stores/dsFilters'
import { useI18nStore } from '@/stores/i18n'
import { ordersApi, masterDataApi } from '@/api'
import DataExcelToolbar from '@/components/DataExcelToolbar.vue'
import dayjs from 'dayjs'
import { Setting } from '@element-plus/icons-vue'
import {
  formatDisplayDate as formatDate,
  formatDisplayDateTime as formatDateTime,
  elementDatePickerDisplayFormat,
  elementDateTimePickerDisplayFormat
} from '@/utils/displayDateTime'

const ORDERS_FILTER_VISIBILITY_KEY = 'ds_orders_filter_visibility'

const defaultFilterVisibility = () => ({
  orderNumber: true,
  location: true,
  orderType: true,
  status: true,
  delayed: true,
  dueDate: true,
  resource: true
})

const loadFilterVisibility = () => {
  try {
    const raw = localStorage.getItem(ORDERS_FILTER_VISIBILITY_KEY)
    if (!raw) return defaultFilterVisibility()
    const parsed = JSON.parse(raw)
    return { ...defaultFilterVisibility(), ...parsed }
  } catch {
    return defaultFilterVisibility()
  }
}

const store = useMasterDataStore()
const dsFiltersStore = useDSFiltersStore()
const i18nStore = useI18nStore()
const t = (key) => i18nStore.t(key)

const datePickerDisplayFormat = computed(() => elementDatePickerDisplayFormat())
const dateTimePickerDisplayFormat = computed(() => elementDateTimePickerDisplayFormat())

const loading = computed(() => dsFiltersStore.ordersLoading)
const products = computed(() => store.products)
const routings = computed(() => store.routings)
const resources = computed(() => store.resources)

const displayOrderLocation = (order) => {
  if (!order) return '-'
  const loc = order.location || order.product?.location
  return loc && String(loc).trim() ? String(loc).trim() : '-'
}

// 根据产品ID获取对应的工艺路线
const getRoutingByProductId = (productId) => {
  return routings.value.find(r => r.product_id === productId && r.is_active)
}

// 获取工序的资源名称（优先使用工序自带的资源信息）
const getResourceNameFromRouting = (operation, productId) => {
  // 优先使用工序表中的资源（已根据工序名称正确匹配）
  if (operation.resource?.name) {
    return operation.resource.name
  }
  
  // 如果有 resource_id 但没有 resource 对象，从资源列表中查找
  if (operation.resource_id) {
    const resource = resources.value.find(r => r.id === operation.resource_id)
    if (resource) {
      return resource.name
    }
  }
  
  // 兜底逻辑：从工艺路线获取
  const routing = getRoutingByProductId(productId)
  if (routing && routing.operations) {
    const routingOp = routing.operations.find(op => op.sequence === operation.sequence)
    if (routingOp && routingOp.work_center_id) {
      const resource = resources.value.find(r => r.work_center_id === routingOp.work_center_id)
      if (resource) {
        return resource.name
      }
    }
  }
  
  return t('orders.unassigned')
}

const statusLabelKeys = {
  created: 'pendingSchedule',
  scheduled: 'scheduled',
  in_progress: 'inProgress',
  completed: 'completed',
  cancelled: 'cancelled'
}

const filterStatus = ref('')
const filterOrderType = ref('')
const filterDueDateRange = ref(null)
const filterOrderNumber = ref('')
const filterResourceIds = ref([])
const filterDelayed = ref(null)
const filterLocationCodes = ref([])
const locationOptions = ref([])

const normOrderLocationCode = (v) => (v != null && String(v).trim() ? String(v).trim() : '')

const filterOrderLocationCodesNorm = computed(() =>
  [...new Set(filterLocationCodes.value.map(normOrderLocationCode).filter(Boolean))]
)

/** 未选位置：全部资源；已选位置：仅 resource.location 与所选代码严格一致（未维护则不匹配） */
const resourcesForOrderFilter = computed(() => {
  const codes = filterOrderLocationCodesNorm.value
  const all = resources.value || []
  if (codes.length === 0) return all
  const set = new Set(codes)
  return all.filter((r) => set.has(normOrderLocationCode(r.location)))
})

const orderResourceSelectPlaceholder = computed(() => {
  if (filterOrderLocationCodesNorm.value.length > 0 && resourcesForOrderFilter.value.length === 0) {
    return t('orders.noResourcesAtLocation')
  }
  return t('orders.selectResources')
})

const allOrderFilterLocationsSelected = computed(() => {
  const options = locationOptions.value
  if (options.length === 0) return false
  const selected = new Set(filterLocationCodes.value)
  return selected.size === options.length && options.every((loc) => selected.has(loc.code))
})

const orderFilterLocationsIndeterminate = computed(() => {
  const options = locationOptions.value
  const selected = new Set(filterLocationCodes.value)
  const n = options.filter((loc) => selected.has(loc.code)).length
  return n > 0 && n < options.length
})

const handleSelectAllOrderFilterLocations = (val) => {
  if (val) {
    filterLocationCodes.value = locationOptions.value.map((loc) => loc.code)
  } else {
    filterLocationCodes.value = []
  }
  onFilterLocationChange()
}

const allOrderFilterResourcesSelected = computed(() => {
  const options = resourcesForOrderFilter.value
  return (
    options.length > 0 &&
    filterResourceIds.value.length === options.length &&
    options.every((r) => filterResourceIds.value.includes(r.id))
  )
})

const orderFilterResourcesIndeterminate = computed(() => {
  const options = resourcesForOrderFilter.value
  const selectedInOptions = options.filter((r) => filterResourceIds.value.includes(r.id)).length
  return selectedInOptions > 0 && selectedInOptions < options.length
})

const handleSelectAllOrderFilterResources = (val) => {
  if (val) {
    filterResourceIds.value = resourcesForOrderFilter.value.map((r) => r.id)
  } else {
    const filteredIds = new Set(resourcesForOrderFilter.value.map((r) => r.id))
    filterResourceIds.value = filterResourceIds.value.filter((id) => !filteredIds.has(id))
  }
}

async function onFilterLocationChange() {
  await nextTick()
  const allowed = new Set(resourcesForOrderFilter.value.map((r) => r.id))
  filterResourceIds.value = filterResourceIds.value.filter((id) => allowed.has(id))
  fetchData()
}

const filterVisibility = reactive(loadFilterVisibility())
const adjustFiltersDialogVisible = ref(false)
const filterVisibilityDraft = reactive(defaultFilterVisibility())

const persistFilterVisibility = () => {
  try {
    localStorage.setItem(
      ORDERS_FILTER_VISIBILITY_KEY,
      JSON.stringify({ ...filterVisibility })
    )
  } catch (e) {
    console.warn('Failed to persist filter visibility:', e)
  }
}

const openAdjustFiltersDialog = () => {
  Object.assign(filterVisibilityDraft, filterVisibility)
  adjustFiltersDialogVisible.value = true
}

const confirmAdjustFilters = () => {
  const d = filterVisibilityDraft
  if (!d.orderNumber) filterOrderNumber.value = ''
  if (!d.location) {
    filterLocationCodes.value = []
    fetchData()
  }
  if (!d.orderType) filterOrderType.value = ''
  if (!d.status) filterStatus.value = ''
  if (!d.delayed) filterDelayed.value = null
  if (!d.dueDate) filterDueDateRange.value = null
  if (!d.resource) filterResourceIds.value = []
  Object.assign(filterVisibility, d)
  persistFilterVisibility()
  adjustFiltersDialogVisible.value = false
}

const orderLocationOptionLabel = (loc) => {
  if (!loc) return ''
  const d = (loc.description || '').trim()
  return d ? `${loc.code} · ${d}` : loc.code
}

const loadOrderLocationOptions = async () => {
  try {
    locationOptions.value = (await masterDataApi.getLocations()) || []
  } catch (e) {
    console.error('Failed to load locations:', e)
    locationOptions.value = []
  }
}

// 判断订单是否延期
// 规则：预计完工时间晚于「交货期当天结束」才算延期；同一天内完工视为准时（交期按“天”理解）
const isOrderDelayed = (order) => {
  if (!order.due_date) return false
  
  // 获取预计完工时间（最后一道工序的结束时间）
  const finishTime = getEstimatedFinishTime(order)
  
  // 如果没有预计完工时间，判断交货期是否已过且订单未完成
  if (!finishTime) {
    const now = dayjs()
    const dueDate = dayjs(order.due_date)
    
    if (dueDate.isBefore(now, 'day')) {
      const displayStatus = getDisplayOrderStatus(order)
      return displayStatus !== 'completed'
    }
    return false
  }
  
  // 有预计完工时间：仅当完工时间晚于交货期当日结束时才算延期（同一天内完工不算延期）
  const dueEndOfDay = dayjs(order.due_date).endOf('day')
  return dayjs(finishTime).isAfter(dueEndOfDay)
}

// 订单列表（全部数据，DS订单数据是数据源，再经过筛选）
const filteredOrders = computed(() => {
  let orders = dsFiltersStore.dsOrders
  
  // 如果设置了订单号筛选
  if (filterOrderNumber.value && filterOrderNumber.value.trim()) {
    const searchTerm = filterOrderNumber.value.trim().toUpperCase()
    orders = orders.filter(order => 
      order.order_number && order.order_number.toUpperCase().includes(searchTerm)
    )
  }
  
  // 如果设置了订单类型筛选
  if (filterOrderType.value) {
    orders = orders.filter(order => order.order_type === filterOrderType.value)
  }
  
  // 如果设置了状态筛选（基于显示状态，而不是实际状态）
  if (filterStatus.value) {
    orders = orders.filter(order => {
      const displayStatus = getDisplayOrderStatus(order)
      return displayStatus === filterStatus.value
    })
  }
  
  // 如果设置了延期筛选
  if (filterDelayed.value !== null && filterDelayed.value !== undefined && filterDelayed.value !== '') {
    orders = orders.filter(order => isOrderDelayed(order) === filterDelayed.value)
  }
  
  // 如果设置了交货期筛选
  if (filterDueDateRange.value && filterDueDateRange.value.length === 2) {
    const [startDate, endDate] = filterDueDateRange.value
    const start = dayjs(startDate).startOf('day')
    const end = dayjs(endDate).endOf('day')
    
    orders = orders.filter(order => {
      if (!order.due_date) return false
      const dueDate = dayjs(order.due_date)
      return (dueDate.isAfter(start) || dueDate.isSame(start, 'day')) &&
             (dueDate.isBefore(end) || dueDate.isSame(end, 'day'))
    })
  }
  
  // 如果设置了资源筛选（多选：任一工序落在所选资源之一即保留）
  if (filterResourceIds.value?.length) {
    const idSet = new Set(filterResourceIds.value)
    orders = orders.filter((order) => {
      if (!order.operations || order.operations.length === 0) return false
      return order.operations.some((op) => op.resource_id != null && idSet.has(op.resource_id))
    })
  }
  
  return orders
})

// 搜索按钮点击（目前是实时搜索，此方法用于回车键搜索）
const handleSearch = () => {
  // 实时搜索已在 computed 中实现，这里可以用于额外逻辑
  if (filterOrderNumber.value && filteredOrders.value.length === 0) {
    ElMessage.warning(t('orders.noMatchingOrders'))
  }
}

// 交货期快捷选项
const dueDateShortcuts = computed(() => [
  {
    text: t('orders.today'),
    value: () => {
      const today = new Date()
      return [today, today]
    }
  },
  {
    text: t('orders.thisWeek'),
    value: () => {
      const today = new Date()
      const start = new Date(today)
      start.setDate(today.getDate() - today.getDay() + 1)
      const end = new Date(start)
      end.setDate(start.getDate() + 6)
      return [start, end]
    }
  },
  {
    text: t('orders.nextWeek'),
    value: () => {
      const today = new Date()
      const start = new Date(today)
      start.setDate(today.getDate() - today.getDay() + 8)
      const end = new Date(start)
      end.setDate(start.getDate() + 6)
      return [start, end]
    }
  },
  {
    text: t('orders.thisMonth'),
    value: () => {
      const today = new Date()
      const start = new Date(today.getFullYear(), today.getMonth(), 1)
      const end = new Date(today.getFullYear(), today.getMonth() + 1, 0)
      return [start, end]
    }
  },
  {
    text: t('orders.nextMonth'),
    value: () => {
      const today = new Date()
      const start = new Date(today.getFullYear(), today.getMonth() + 1, 1)
      const end = new Date(today.getFullYear(), today.getMonth() + 2, 0)
      return [start, end]
    }
  }
])

const fetchData = () => {
  // 使用共享的dsFiltersStore来获取订单数据
  // 注意：不再传递 filterStatus 和 filterOrderType 给后端，因为这些筛选在前端完成
  dsFiltersStore.fetchDSOrders(null, null, {
    filterLocationCodes: filterLocationCodes.value
  })
}

// Order form
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const form = ref({
  order_number: '',
  order_type: 'planned',
  product_id: null,
  quantity: 100,
  due_date: null,
  earliest_start: null,
  priority: 5,
  description: ''
})

const productLocationForForm = computed(() => {
  const pid = form.value.product_id
  if (!pid) return '-'
  const p = products.value.find((x) => x.id === pid)
  return p?.location && String(p.location).trim() ? String(p.location).trim() : '-'
})

const rulesRef = computed(() => ({
  product_id: [{ required: true, message: t('orders.productRequired'), trigger: 'change' }],
  quantity: [{ required: true, message: t('orders.quantityRequired'), trigger: 'blur' }],
  due_date: [{ required: true, message: t('orders.dueDateRequired'), trigger: 'change' }]
}))

// Convert to production dialog
const convertDialogVisible = ref(false)
const convertOrderId = ref(null)
const converting = ref(false)
const convertForm = ref({
  confirmed_start: null,
  confirmed_end: null
})

// Operations dialog
const opsDialogVisible = ref(false)
const currentOrder = ref(null)
// 订单工序弹窗中显示的订单状态：若有任一工序为待排程，则订单显示为待排程
const orderStatusInOpsDialog = computed(() => {
  const order = currentOrder.value
  if (!order) return 'created'
  const ops = order.operations || []
  if (ops.length === 0) return order.status
  const hasPending = ops.some(op => op.status === 'pending')
  return hasPending ? 'created' : order.status
})

// 获取订单的预计完工时间（最后一道工序的结束时间）
const getEstimatedFinishTime = (order) => {
  if (!order || !order.operations || order.operations.length === 0) {
    return null
  }
  
  // 找到序号最大的工序（最后一道工序）
  const lastOperation = order.operations.reduce((max, op) => {
    return op.sequence > max.sequence ? op : max
  }, order.operations[0])
  
  // 返回最后一道工序的结束时间
  // 优先使用 scheduled_end，如果没有则使用 confirmed_end（生产订单的确认结束时间）
  return lastOperation.scheduled_end || order.confirmed_end || null
}

const getPriorityType = (priority) => {
  if (priority <= 3) return 'danger'
  if (priority <= 5) return 'warning'
  return 'info'
}

const getStatusType = (status) => {
  const types = {
    created: 'info',
    scheduled: 'primary',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'danger'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status) => {
  const key = statusLabelKeys[status]
  return key ? t('orders.' + key) : status
}

// 根据工序状态推导订单显示状态：若有任一工序为待排程，则订单显示为待排程
const getDisplayOrderStatus = (order) => {
  if (!order) return 'created'
  const ops = order.operations || []
  if (ops.length === 0) return order.status
  const hasPending = ops.some(op => op.status === 'pending')
  return hasPending ? 'created' : order.status
}

const getOpStatusType = (status) => {
  const types = {
    pending: 'info',
    scheduled: 'primary',
    in_progress: 'warning',
    completed: 'success'
  }
  return types[status] || 'info'
}

const getOpStatusLabel = (status) => {
  const keyMap = { pending: 'pendingSchedule', scheduled: 'scheduled', in_progress: 'inProgress', completed: 'completed' }
  const key = keyMap[status]
  return key ? t('orders.' + key) : status
}

const handleAdd = () => {
  isEdit.value = false
  editId.value = null
  const defaultDueDate = dayjs().add(7, 'day').hour(17).minute(0).second(0).toDate()
  form.value = { 
    order_number: '',
    order_type: 'planned',
    product_id: null, 
    quantity: 100, 
    due_date: defaultDueDate,
    earliest_start: null,
    priority: 5, 
    description: '' 
  }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  if (row.order_type === 'production') {
    ElMessage.warning(t('orders.productionOrderCannotEdit'))
    return
  }
  isEdit.value = true
  editId.value = row.id
  form.value = {
    order_number: row.order_number,
    order_type: row.order_type,
    product_id: row.product_id,
    quantity: row.quantity,
    due_date: row.due_date ? new Date(row.due_date) : null,
    earliest_start: row.earliest_start ? new Date(row.earliest_start) : null,
    priority: row.priority,
    description: row.description || ''
  }
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  const typeLabel = row.order_type === 'production' ? t('orders.productionOrder') : t('orders.plannedOrder')
  try {
    await ElMessageBox.confirm(t('orders.confirmDelete').replace('{type}', typeLabel).replace('{number}', row.order_number), t('orders.confirmDeleteTitle'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    await store.deleteOrder(row.id)
    ElMessage.success(t('orders.deleteSuccess'))
    await fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('orders.deleteFailed'))
    }
  }
}

const handleConvertToProduction = (row) => {
  convertOrderId.value = row.id
  convertForm.value = {
    confirmed_start: null,
    confirmed_end: null
  }
  convertDialogVisible.value = true
}

const submitConvert = async () => {
  converting.value = true
  try {
    const data = {}
    if (convertForm.value.confirmed_start) {
      data.confirmed_start = convertForm.value.confirmed_start.toISOString()
    }
    if (convertForm.value.confirmed_end) {
      data.confirmed_end = convertForm.value.confirmed_end.toISOString()
    }
    
    await ordersApi.convertToProduction(convertOrderId.value, Object.keys(data).length > 0 ? data : null)
    ElMessage.success(t('orders.convertSuccess'))
    convertDialogVisible.value = false
    fetchData()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || t('orders.convertFailed'))
  } finally {
    converting.value = false
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    
    const data = {
      order_type: 'planned',
      product_id: form.value.product_id,
      quantity: form.value.quantity,
      due_date: form.value.due_date?.toISOString(),
      earliest_start: form.value.earliest_start?.toISOString() || null,
      priority: form.value.priority,
      description: form.value.description?.trim() ? form.value.description.trim() : null
    }
    if (!isEdit.value && form.value.order_number?.trim()) {
      data.order_number = form.value.order_number.trim()
    }
    if (isEdit.value) {
      await store.updateOrder(editId.value, data)
      ElMessage.success(t('orders.updateSuccess'))
    } else {
      await store.createOrder(data)
      ElMessage.success(t('orders.createSuccess'))
    }

    dialogVisible.value = false
    await fetchData()
  } catch (error) {
    if (error !== false) {
      ElMessage.error(isEdit.value ? t('orders.updateFailed') : t('orders.createFailed'))
    }
  } finally {
    submitting.value = false
  }
}

const handleViewOperations = (order) => {
  currentOrder.value = order
  opsDialogVisible.value = true
}

onMounted(async () => {
  await loadOrderLocationOptions()
  fetchData()
  store.fetchProducts()
  store.fetchRoutings()  // 加载工艺路线数据，用于获取工序的资源信息
  store.fetchResources() // 加载资源数据
})
</script>

<style lang="scss" scoped>
.orders-page {
  min-height: calc(100vh - 100px);

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 16px;

    .header-actions {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
  }
}

.filter-card {
  margin-bottom: 16px;
  
  :deep(.el-card__body) {
    padding: 12px 24px !important;
  }
  
  :deep(.el-form-item) {
    margin-bottom: 0;
  }

  .filter-actions-item {
    margin-right: 0;
  }
}

.adjust-filters-hint {
  margin: 0 0 16px;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.filter-visibility-checks {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.text-muted {
  color: #909399;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.action-buttons {
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  
  .el-button {
    margin: 0 !important;
  }
}

.select-header-options {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 4px 0;
}
</style>
