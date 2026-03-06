<template>
  <div class="master-data-page">
    <div class="page-header">
      <h1>
        <el-icon><Grid /></el-icon>
        {{ t('dsResource.title') }}
      </h1>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        {{ t('dsResource.addResource') }}
      </el-button>
    </div>
    
    <el-card>
      <el-table :data="allResourceList" v-loading="loading" stripe table-layout="auto">
        <el-table-column prop="code" :label="t('dsResource.resourceCode')" min-width="120" />
        <el-table-column prop="name" :label="t('dsResource.resourceName')" min-width="120" />
        <el-table-column prop="location" :label="t('dsResource.location')" min-width="80" align="center" />
        <el-table-column :label="t('dsResource.workCenter')" min-width="100">
          <template #default="{ row }">
            {{ getWorkCenterName(row.work_center_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="production_hours" :label="t('dsResource.productionHours')" min-width="110" align="right">
          <template #default="{ row }">
            {{ row.production_hours.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="finite_planning" :label="t('dsResource.finitePlanning')" min-width="80" align="center">
          <template #default="{ row }">
            <el-checkbox v-model="row.finite_planning" disabled />
          </template>
        </el-table-column>
        <el-table-column prop="is_bottleneck" :label="t('dsResource.bottleneckResource')" min-width="80" align="center">
          <template #default="{ row }">
            <el-checkbox v-model="row.is_bottleneck" disabled />
          </template>
        </el-table-column>
        <el-table-column :label="t('masterData.actions')" width="220" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link @click="handleView(row)">{{ t('dsProduct.viewDetails') }}</el-button>
              <el-button type="primary" link @click="handleEdit(row)">{{ t('masterData.edit') }}</el-button>
              <el-button type="primary" link @click="handleDelete(row)">{{ t('masterData.delete') }}</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog 
      v-model="viewDialogVisible" 
      :title="`${t('dsResource.resourceDetails')} - ${currentResource?.name || ''}`"
      width="800px"
    >
      <el-descriptions :column="2" border v-if="currentResource">
        <el-descriptions-item :label="t('dsResource.resourceCode')">{{ currentResource.code }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.resourceName')">{{ currentResource.name }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.location')">{{ currentResource.location }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.workCenter')">{{ getWorkCenterName(currentResource.work_center_id) }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.workCenterDesc')">{{ getWorkCenterDescription(currentResource.work_center_id) }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.start')">{{ currentResource.start_time }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.end')">{{ currentResource.end_time }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.breakPeriod')">{{ currentResource.break_time }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.utilizationPercent')">{{ currentResource.utilization_percent.toFixed(3) }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.productionHours')">{{ currentResource.production_hours.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.capacity')">
          {{ currentResource.capacity !== null && currentResource.capacity !== undefined && currentResource.capacity !== '' ? currentResource.capacity.toFixed(3) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.finitePlanning')">
          <el-tag :type="currentResource.finite_planning ? 'success' : 'info'" size="small">
            {{ currentResource.finite_planning ? t('common.yes') : t('common.no') }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.bottleneckResource')">
          <el-tag :type="currentResource.is_bottleneck ? 'warning' : 'info'" size="small">
            {{ currentResource.is_bottleneck ? t('common.yes') : t('common.no') }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.resourceMode')">{{ getResourceMode(currentResource.capacity) }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.timezone')">{{ currentResource.timezone }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.factoryCalendar')">{{ currentResource.factory_calendar }}</el-descriptions-item>
        <el-descriptions-item :label="t('dsResource.planningGroup')">{{ currentResource.planning_group }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="viewDialogVisible = false">{{ t('dsResource.close') }}</el-button>
      </template>
    </el-dialog>
    
    <el-dialog 
      v-model="editDialogVisible" 
      :title="isEdit ? t('dsResource.editResource') : t('dsResource.addResource')"
      width="600px"
    >
      <el-form ref="formRef" :model="form" :rules="rulesRef" label-width="120px">
        <el-form-item :label="t('dsResource.resourceCode')" prop="code">
          <el-input v-model="form.code" :disabled="isEdit" :placeholder="t('dsResource.enterResourceCode')" />
        </el-form-item>
        <el-form-item :label="t('dsResource.resourceName')" prop="name">
          <el-input v-model="form.name" :placeholder="t('dsResource.enterResourceName')" />
        </el-form-item>
        <el-form-item :label="t('dsResource.workCenter')" prop="work_center_id">
          <el-select v-model="form.work_center_id" :placeholder="t('dsResource.selectWorkCenter')" style="width: 100%">
            <el-option 
              v-for="wc in workCenters" 
              :key="wc.id" 
              :label="`${wc.code} - ${wc.name}`" 
              :value="wc.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('dsResource.efficiency')">
          <el-input-number v-model="form.efficiency" :min="0" :max="2" :step="0.1" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item :label="t('dsResource.dailyCapacity')">
          <el-input-number v-model="form.capacity_per_day" :min="0" :step="1" :precision="1" style="width: 100%" />
          <div class="form-tip">{{ t('dsResource.capacityUnitTip') }}</div>
        </el-form-item>
        <el-form-item :label="t('dsResource.description')">
          <el-input v-model="form.description" type="textarea" rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Grid, Plus } from '@element-plus/icons-vue'
import { masterDataApi } from '@/api'
import { useI18nStore } from '@/stores/i18n'

const i18nStore = useI18nStore()
const t = (key) => i18nStore.t(key)

const loading = ref(false)

// 资源列表数据（所有资源，不再过滤）
const allResourceList = ref([])

// 工作中心列表
const workCenters = ref([])

// 对话框状态
const viewDialogVisible = ref(false)
const editDialogVisible = ref(false)
const isEdit = ref(false)
const currentResource = ref(null)
const submitting = ref(false)
const formRef = ref(null)

// 表单数据
const form = ref({
  code: '',
  name: '',
  work_center_id: null,
  efficiency: 1.0,
  capacity_per_day: 8.0,
  description: ''
})

const rulesRef = computed(() => ({
  code: [{ required: true, message: t('dsResource.enterResourceCode'), trigger: 'blur' }],
  name: [{ required: true, message: t('dsResource.enterResourceName'), trigger: 'blur' }],
  work_center_id: [{ required: true, message: t('dsResource.selectWorkCenter'), trigger: 'change' }]
}))

const getResourceMode = (capacity) => {
  return (capacity === null || capacity === undefined || capacity === '') 
    ? t('dsResource.singleMode') 
    : t('dsResource.multiMode')
}

// 获取工作中心名称
const getWorkCenterName = (workCenterId) => {
  const wc = workCenters.value.find(w => w.id === workCenterId)
  return wc ? wc.name : '-'
}

// 获取工作中心描述
const getWorkCenterDescription = (workCenterId) => {
  const wc = workCenters.value.find(w => w.id === workCenterId)
  return wc ? wc.description || '-' : '-'
}

// 将 "HH:mm:ss" 或 "HH:mm" 转为从 0 点起的分钟数
const timeToMinutes = (timeStr) => {
  if (!timeStr) return 0
  const s = String(timeStr).trim()
  const parts = s.split(':').map(Number)
  const h = parts[0] || 0
  const m = parts[1] || 0
  const sec = parts[2] || 0
  return h * 60 + m + sec / 60
}

// 生产时间/小时 = 结束 - 开始 - 休息时间
const calcProductionHours = (startTime, endTime, breakTime) => {
  const startMin = timeToMinutes(startTime)
  const endMin = timeToMinutes(endTime)
  const breakMin = timeToMinutes(breakTime)
  const minutes = Math.max(0, endMin - startMin - breakMin)
  return Math.round(minutes / 60 * 100) / 100
}

// 根据资源获取容量值（模拟逻辑：部分资源有容量，部分没有）
const getCapacityValue = (resource) => {
  // 模拟：如果 capacity_per_day > 10，则认为有容量值
  if (resource.capacity_per_day && resource.capacity_per_day > 10) {
    return resource.capacity_per_day
  }
  // 模拟：如果名称包含特定关键字，设置容量
  if (resource.name?.includes('多') || resource.name?.includes('并行')) {
    return 10.0
  }
  return null
}

// 加载工作中心数据
const loadWorkCenters = async () => {
  try {
    workCenters.value = await masterDataApi.getWorkCenters()
  } catch (error) {
    console.error('Failed to load work centers:', error)
    ElMessage.error(t('dsResource.loadWorkCentersFailed'))
  }
}

// 加载资源数据
const loadResources = async () => {
  loading.value = true
  try {
    const data = await masterDataApi.getResources()
    const defaultStart = '09:00:00'
    const defaultEnd = '18:00:00'
    const defaultBreak = '00:00:00'
    allResourceList.value = data.map(resource => {
      const start_time = defaultStart
      const end_time = defaultEnd
      const break_time = defaultBreak
      const production_hours = calcProductionHours(start_time, end_time, break_time)
      return {
        id: resource.id,
        code: resource.code,
        name: resource.name,
        work_center_id: resource.work_center_id,
        location: resource.work_center?.code || resource.work_center_id || '1020',
        start_time,
        end_time,
        break_time,
        utilization_percent: (resource.efficiency || 1) * 100,
        production_hours,
        capacity: getCapacityValue(resource),
        finite_planning: true,
        is_bottleneck: resource.name?.includes('CNC') || resource.name?.includes('加工') || resource.name?.includes('瓶颈') || false,
        timezone: 'CET',
        factory_calendar: resource.work_center?.code === 'CN' ? 'CN' : '01',
        planning_group: 'A',
        efficiency: resource.efficiency,
        capacity_per_day: resource.capacity_per_day,
        description: resource.description
      }
    })
  } catch (error) {
    console.error('Failed to load resources:', error)
    ElMessage.error(t('dsResource.loadResourcesFailed'))
  } finally {
    loading.value = false
  }
}

// 显示资源详情
const handleView = (row) => {
  currentResource.value = row
  viewDialogVisible.value = true
}

// 新增资源
const handleAdd = () => {
  isEdit.value = false
  form.value = {
    code: '',
    name: '',
    work_center_id: null,
    efficiency: 1.0,
    capacity_per_day: 8.0,
    description: ''
  }
  editDialogVisible.value = true
}

// 编辑资源
const handleEdit = (row) => {
  isEdit.value = true
  form.value = {
    id: row.id,
    code: row.code,
    name: row.name,
    work_center_id: row.work_center_id,
    efficiency: row.efficiency || 1.0,
    capacity_per_day: row.capacity_per_day || 8.0,
    description: row.description || ''
  }
  editDialogVisible.value = true
}

// 删除资源
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      t('dsResource.confirmDeleteResource').replace('{name}', row.name),
      t('orders.confirmDeleteTitle'),
      { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' }
    )
    ElMessage.success(t('messages.deleteSuccess'))
    loadResources()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('messages.deleteFailed'))
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (isEdit.value) {
      ElMessage.success(t('messages.updateSuccess'))
    } else {
      ElMessage.success(t('messages.createSuccess'))
    }
    
    editDialogVisible.value = false
    loadResources()
  } catch (error) {
    if (error !== false) {
      ElMessage.error(isEdit.value ? t('messages.updateFailed') : t('messages.createFailed'))
    }
  } finally {
    submitting.value = false
  }
}

// 初始化
onMounted(() => {
  loadWorkCenters()
  loadResources()
})
</script>

<style lang="scss" scoped>
.master-data-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  
  h1 {
    margin: 0;
    font-size: 24px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
