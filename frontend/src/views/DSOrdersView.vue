<template>
  <div class="orders-page">
    <div class="page-header">
      <h1>
        <el-icon><Document /></el-icon>
        DS订单数据
      </h1>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增计划订单
      </el-button>
    </div>
    
    <!-- Filter -->
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="订单号">
          <el-input
            v-model="filterOrderNumber"
            placeholder="输入订单号查询"
            style="width: 180px"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="订单类型">
          <el-select v-model="filterOrderType" placeholder="全部类型" clearable style="width: 150px" @change="fetchData">
            <el-option label="计划订单" value="planned" />
            <el-option label="生产订单" value="production" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态筛选">
          <el-select v-model="filterStatus" placeholder="全部状态" clearable style="width: 150px" @change="fetchData">
            <el-option label="待排程" value="created" />
            <el-option label="已排程" value="scheduled" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        <el-form-item label="交货期">
          <el-date-picker
            v-model="filterDueDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 260px"
            value-format="YYYY-MM-DD"
            :shortcuts="dueDateShortcuts"
            clearable
          />
        </el-form-item>
        <el-form-item label="资源">
          <el-select
            v-model="filterResourceId"
            placeholder="选择资源"
            clearable
            filterable
            style="width: 180px"
          >
            <el-option
              v-for="resource in resources"
              :key="resource.id"
              :label="resource.name"
              :value="resource.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- Orders Table -->
    <el-card>
      <el-table :data="filteredOrders" v-loading="loading" stripe table-layout="auto">
        <el-table-column label="类型" min-width="90">
          <template #default="{ row }">
            <el-tag :type="row.order_type === 'production' ? 'info' : 'primary'" effect="plain">
              {{ row.order_type === 'production' ? '生产订单' : '计划订单' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="order_number" label="订单号" min-width="130" />
        <el-table-column label="产品" min-width="120">
          <template #default="{ row }">
            {{ row.product?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" min-width="70" align="right" />
        <el-table-column label="交货期" min-width="100">
          <template #default="{ row }">
            {{ formatDate(row.due_date) }}
          </template>
        </el-table-column>
        <el-table-column label="确认时间" min-width="180" v-if="showConfirmedTime">
          <template #default="{ row }">
            <span v-if="row.order_type === 'production' && row.confirmed_start">
              {{ formatDateTime(row.confirmed_start) }} - {{ formatDateTime(row.confirmed_end) }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" min-width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">
              {{ row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(getDisplayOrderStatus(row))" size="small">
              {{ getStatusLabel(getDisplayOrderStatus(row)) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="工序" min-width="60" align="center">
          <template #default="{ row }">
            {{ row.operations?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" size="small" @click="handleViewOperations(row)">工序</el-button>
              <el-button 
                v-if="row.order_type === 'planned'" 
                type="primary" 
                size="small"
                @click="handleEdit(row)"
              >编辑</el-button>
              <el-button 
                v-if="row.order_type === 'planned' && getDisplayOrderStatus(row) === 'scheduled'" 
                type="primary" 
                size="small"
                @click="handleConvertToProduction(row)"
              >转生产</el-button>
              <el-button type="primary" size="small" @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- Order Edit Dialog -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑计划订单' : '新增计划订单'"
      width="520px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="订单号" prop="order_number">
          <el-input v-model="form.order_number" :disabled="isEdit" placeholder="请输入订单号" />
        </el-form-item>
        <el-form-item label="产品" prop="product_id">
          <el-select v-model="form.product_id" :disabled="isEdit" placeholder="请选择产品" style="width: 100%">
            <el-option 
              v-for="p in products" 
              :key="p.id" 
              :label="`${p.code} - ${p.name}`" 
              :value="p.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="form.quantity" :min="1" :precision="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="交货期" prop="due_date">
          <el-date-picker 
            v-model="form.due_date" 
            type="datetime"
            placeholder="请选择交货期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="最早开始">
          <el-date-picker 
            v-model="form.earliest_start" 
            type="datetime"
            placeholder="不限"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-slider v-model="form.priority" :min="1" :max="10" :step="1" show-stops show-input />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- Convert to Production Dialog -->
    <el-dialog 
      v-model="convertDialogVisible" 
      title="转换为生产订单"
      width="480px"
    >
      <el-alert 
        type="warning" 
        :closable="false"
        style="margin-bottom: 16px;"
      >
        转换后订单将变为生产订单，时间将被锁定，不再参与排程计算。
      </el-alert>
      
      <el-form :model="convertForm" label-width="100px">
        <el-form-item label="确认开始">
          <el-date-picker 
            v-model="convertForm.confirmed_start" 
            type="datetime"
            placeholder="使用排程时间"
            style="width: 100%"
          />
          <div class="form-tip">留空则使用排程计算的开始时间</div>
        </el-form-item>
        <el-form-item label="确认结束">
          <el-date-picker 
            v-model="convertForm.confirmed_end" 
            type="datetime"
            placeholder="使用排程时间"
            style="width: 100%"
          />
          <div class="form-tip">留空则使用排程计算的结束时间</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="convertDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitConvert" :loading="converting">确认转换</el-button>
      </template>
    </el-dialog>
    
    <!-- Operations Dialog -->
    <el-dialog 
      v-model="opsDialogVisible" 
      :title="`订单工序 - ${currentOrder?.order_number || ''}`"
      width="900px"
    >
      <el-descriptions :column="3" border style="margin-bottom: 16px;" v-if="currentOrder">
        <el-descriptions-item label="订单类型">
          <el-tag :type="currentOrder.order_type === 'production' ? 'success' : 'primary'" size="small">
            {{ currentOrder.order_type === 'production' ? '生产订单' : '计划订单' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(orderStatusInOpsDialog)" size="small">
            {{ getStatusLabel(orderStatusInOpsDialog) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="交货期">{{ formatDate(currentOrder.due_date) }}</el-descriptions-item>
        <el-descriptions-item label="确认开始" v-if="currentOrder.order_type === 'production'">
          {{ formatDateTime(currentOrder.confirmed_start) || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="确认结束" v-if="currentOrder.order_type === 'production'">
          {{ formatDateTime(currentOrder.confirmed_end) || '-' }}
        </el-descriptions-item>
      </el-descriptions>
      
      <el-table :data="currentOrder?.operations || []" size="small" table-layout="auto">
        <el-table-column label="工序" min-width="140">
          <template #default="{ row }">
            {{ row.sequence }} {{ row.name }}
          </template>
        </el-table-column>
        <el-table-column label="资源" min-width="100">
          <template #default="{ row }">
            {{ getResourceNameFromRouting(row, currentOrder?.product_id) }}
          </template>
        </el-table-column>
        <el-table-column label="计划开始" min-width="120">
          <template #default="{ row }">
            {{ row.scheduled_start ? formatDateTime(row.scheduled_start) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="计划结束" min-width="120">
          <template #default="{ row }">
            {{ row.scheduled_end ? formatDateTime(row.scheduled_end) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="run_time" label="总时间(h)" min-width="90" align="right">
          <template #default="{ row }">
            {{ row.run_time.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" min-width="90" align="center">
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useMasterDataStore } from '@/stores/masterData'
import { useDSFiltersStore } from '@/stores/dsFilters'
import { ordersApi } from '@/api'
import dayjs from 'dayjs'

const store = useMasterDataStore()
const dsFiltersStore = useDSFiltersStore()

const loading = computed(() => dsFiltersStore.ordersLoading)
const products = computed(() => store.products)
const routings = computed(() => store.routings)
const resources = computed(() => store.resources)

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
  
  return '未分配'
}

const filterStatus = ref('')
const filterOrderType = ref('')
const filterDueDateRange = ref(null)
const filterOrderNumber = ref('')
const filterResourceId = ref(null)  // 资源筛选

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
  
  // 如果设置了资源筛选
  if (filterResourceId.value) {
    orders = orders.filter(order => {
      // 检查订单的工序中是否有分配到该资源的
      if (!order.operations || order.operations.length === 0) return false
      return order.operations.some(op => op.resource_id === filterResourceId.value)
    })
  }
  
  return orders
})

// 搜索按钮点击（目前是实时搜索，此方法用于回车键搜索）
const handleSearch = () => {
  // 实时搜索已在 computed 中实现，这里可以用于额外逻辑
  if (filterOrderNumber.value && filteredOrders.value.length === 0) {
    ElMessage.warning('未找到匹配的订单')
  }
}

// 交货期快捷选项
const dueDateShortcuts = [
  {
    text: '今天',
    value: () => {
      const today = new Date()
      return [today, today]
    }
  },
  {
    text: '本周',
    value: () => {
      const today = new Date()
      const start = new Date(today)
      start.setDate(today.getDate() - today.getDay() + 1) // 周一
      const end = new Date(start)
      end.setDate(start.getDate() + 6) // 周日
      return [start, end]
    }
  },
  {
    text: '下周',
    value: () => {
      const today = new Date()
      const start = new Date(today)
      start.setDate(today.getDate() - today.getDay() + 8) // 下周一
      const end = new Date(start)
      end.setDate(start.getDate() + 6) // 下周日
      return [start, end]
    }
  },
  {
    text: '本月',
    value: () => {
      const today = new Date()
      const start = new Date(today.getFullYear(), today.getMonth(), 1)
      const end = new Date(today.getFullYear(), today.getMonth() + 1, 0)
      return [start, end]
    }
  },
  {
    text: '下月',
    value: () => {
      const today = new Date()
      const start = new Date(today.getFullYear(), today.getMonth() + 1, 1)
      const end = new Date(today.getFullYear(), today.getMonth() + 2, 0)
      return [start, end]
    }
  }
]

// Show confirmed time column when filtering production orders or showing all
const showConfirmedTime = computed(() => {
  return !filterOrderType.value || filterOrderType.value === 'production'
})

const fetchData = () => {
  // 使用共享的dsFiltersStore来获取订单数据
  dsFiltersStore.fetchDSOrders(filterStatus.value || null, filterOrderType.value || null)
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

const rules = {
  order_number: [{ required: true, message: '请输入订单号', trigger: 'blur' }],
  product_id: [{ required: true, message: '请选择产品', trigger: 'change' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  due_date: [{ required: true, message: '请选择交货期', trigger: 'change' }]
}

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

const formatDate = (date) => {
  return date ? dayjs(date).format('YYYY-MM-DD') : ''
}

const formatDateTime = (date) => {
  return date ? dayjs(date).format('MM-DD HH:mm') : ''
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
  const labels = {
    created: '待排程',
    scheduled: '已排程',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return labels[status] || status
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
  const labels = {
    pending: '待排程',
    scheduled: '已排程',
    in_progress: '进行中',
    completed: '已完成'
  }
  return labels[status] || status
}

const handleAdd = () => {
  isEdit.value = false
  editId.value = null
  const defaultDueDate = dayjs().add(7, 'day').hour(17).minute(0).second(0).toDate()
  form.value = { 
    order_number: `PLN${Date.now().toString().slice(-8)}`,
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
    ElMessage.warning('生产订单不可编辑')
    return
  }
  isEdit.value = true
  editId.value = row.id
  form.value = { 
    ...row,
    due_date: row.due_date ? new Date(row.due_date) : null,
    earliest_start: row.earliest_start ? new Date(row.earliest_start) : null
  }
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  const typeLabel = row.order_type === 'production' ? '生产订单' : '计划订单'
  try {
    await ElMessageBox.confirm(`确定要删除${typeLabel} "${row.order_number}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await store.deleteOrder(row.id)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
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
    ElMessage.success('已转换为生产订单')
    convertDialogVisible.value = false
    fetchData()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '转换失败')
  } finally {
    converting.value = false
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    
    const data = {
      ...form.value,
      order_type: 'planned', // Always create as planned order
      due_date: form.value.due_date?.toISOString(),
      earliest_start: form.value.earliest_start?.toISOString() || null
    }
    
    if (isEdit.value) {
      await store.updateOrder(editId.value, data)
      ElMessage.success('更新成功')
    } else {
      await store.createOrder(data)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
  } catch (error) {
    if (error !== false) {
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    }
  } finally {
    submitting.value = false
  }
}

const handleViewOperations = (order) => {
  currentOrder.value = order
  opsDialogVisible.value = true
}

onMounted(() => {
  fetchData()
  store.fetchProducts()
  store.fetchRoutings()  // 加载工艺路线数据，用于获取工序的资源信息
  store.fetchResources() // 加载资源数据
})
</script>

<style lang="scss" scoped>
.orders-page {
  min-height: calc(100vh - 100px);
}

.filter-card {
  margin-bottom: 16px;
  
  :deep(.el-card__body) {
    padding: 12px 24px !important;
  }
  
  :deep(.el-form-item) {
    margin-bottom: 0;
  }
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
</style>
