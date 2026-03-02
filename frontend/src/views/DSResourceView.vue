<template>
  <div class="master-data-page">
    <div class="page-header">
      <h1>
        <el-icon><Grid /></el-icon>
        资源
      </h1>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增资源
      </el-button>
    </div>
    
    <el-card>
      <el-table :data="allResourceList" v-loading="loading" stripe table-layout="auto">
        <el-table-column prop="code" label="资源" min-width="120" />
        <el-table-column prop="name" label="资源名称" min-width="120" />
        <el-table-column prop="location" label="位置" min-width="80" align="center" />
        <el-table-column label="工作中心" min-width="100">
          <template #default="{ row }">
            {{ getWorkCenterName(row.work_center_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="production_hours" label="生产时间/小时" min-width="110" align="right">
          <template #default="{ row }">
            {{ row.production_hours.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="finite_planning" label="有限计划" min-width="80" align="center">
          <template #default="{ row }">
            <el-checkbox v-model="row.finite_planning" disabled />
          </template>
        </el-table-column>
        <el-table-column prop="is_bottleneck" label="瓶颈资源" min-width="80" align="center">
          <template #default="{ row }">
            <el-checkbox v-model="row.is_bottleneck" disabled />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link @click="handleView(row)">详情</el-button>
              <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
              <el-button type="primary" link @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 显示所有字段对话框 -->
    <el-dialog 
      v-model="viewDialogVisible" 
      :title="`资源详情 - ${currentResource?.name || ''}`"
      width="800px"
    >
      <el-descriptions :column="2" border v-if="currentResource">
        <el-descriptions-item label="资源">{{ currentResource.code }}</el-descriptions-item>
        <el-descriptions-item label="资源名称">{{ currentResource.name }}</el-descriptions-item>
        <el-descriptions-item label="位置">{{ currentResource.location }}</el-descriptions-item>
        <el-descriptions-item label="工作中心">{{ getWorkCenterName(currentResource.work_center_id) }}</el-descriptions-item>
        <el-descriptions-item label="工作中心描述">{{ getWorkCenterDescription(currentResource.work_center_id) }}</el-descriptions-item>
        <el-descriptions-item label="开始">{{ currentResource.start_time }}</el-descriptions-item>
        <el-descriptions-item label="结束">{{ currentResource.end_time }}</el-descriptions-item>
        <el-descriptions-item label="休息期间">{{ currentResource.break_time }}</el-descriptions-item>
        <el-descriptions-item label="利用率百分比">{{ currentResource.utilization_percent.toFixed(3) }}</el-descriptions-item>
        <el-descriptions-item label="生产时间/小时">{{ currentResource.production_hours.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="容量">
          {{ currentResource.capacity !== null && currentResource.capacity !== undefined && currentResource.capacity !== '' ? currentResource.capacity.toFixed(3) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="有限计划">
          <el-tag :type="currentResource.finite_planning ? 'success' : 'info'" size="small">
            {{ currentResource.finite_planning ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="瓶颈资源">
          <el-tag :type="currentResource.is_bottleneck ? 'warning' : 'info'" size="small">
            {{ currentResource.is_bottleneck ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="资源模式">{{ getResourceMode(currentResource.capacity) }}</el-descriptions-item>
        <el-descriptions-item label="时区">{{ currentResource.timezone }}</el-descriptions-item>
        <el-descriptions-item label="工厂日历">{{ currentResource.factory_calendar }}</el-descriptions-item>
        <el-descriptions-item label="计划人员组">{{ currentResource.planning_group }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    
    <!-- 编辑/新增资源对话框 -->
    <el-dialog 
      v-model="editDialogVisible" 
      :title="isEdit ? '编辑资源' : '新增资源'"
      width="600px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="资源代码" prop="code">
          <el-input v-model="form.code" :disabled="isEdit" placeholder="请输入资源代码" />
        </el-form-item>
        <el-form-item label="资源名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入资源名称" />
        </el-form-item>
        <el-form-item label="工作中心" prop="work_center_id">
          <el-select v-model="form.work_center_id" placeholder="请选择工作中心" style="width: 100%">
            <el-option 
              v-for="wc in workCenters" 
              :key="wc.id" 
              :label="`${wc.code} - ${wc.name}`" 
              :value="wc.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="效率">
          <el-input-number v-model="form.efficiency" :min="0" :max="2" :step="0.1" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="每日可用产能">
          <el-input-number v-model="form.capacity_per_day" :min="0" :step="1" :precision="1" style="width: 100%" />
          <div class="form-tip">单位：小时/天</div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Grid, Plus } from '@element-plus/icons-vue'
import { masterDataApi } from '@/api'

// 加载状态
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

// 表单验证规则
const rules = {
  code: [{ required: true, message: '请输入资源代码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入资源名称', trigger: 'blur' }],
  work_center_id: [{ required: true, message: '请选择工作中心', trigger: 'change' }]
}

// 资源模式计算逻辑
const getResourceMode = (capacity) => {
  return (capacity === null || capacity === undefined || capacity === '') 
    ? '单一' 
    : '多重'
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
    ElMessage.error('加载工作中心数据失败')
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
    ElMessage.error('加载资源数据失败')
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
    await ElMessageBox.confirm(`确定要删除资源"${row.name}"吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    // TODO: 调用删除API
    // await masterDataApi.deleteResource(row.id)
    
    ElMessage.success('删除成功')
    loadResources()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (isEdit.value) {
      // TODO: 调用更新API
      // await masterDataApi.updateResource(form.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      // TODO: 调用创建API
      // await masterDataApi.createResource(form.value)
      ElMessage.success('创建成功')
    }
    
    editDialogVisible.value = false
    loadResources()
  } catch (error) {
    if (error !== false) {
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
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
