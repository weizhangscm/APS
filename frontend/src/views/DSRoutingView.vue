<template>
  <div class="master-data-page">
    <div class="page-header">
      <h1>
        <el-icon><Share /></el-icon>
        DS工艺路线
      </h1>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增工艺路线
      </el-button>
    </div>
    
    <el-card>
      <el-table :data="routings" v-loading="loading" stripe row-key="id" table-layout="auto">
        <el-table-column prop="code" label="编码" min-width="100" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column label="产品标识" min-width="120">
          <template #default="{ row }">
            {{ row.product?.code || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="产品名称" min-width="120">
          <template #default="{ row }">
            {{ row.product?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" min-width="70" align="center" />
        <el-table-column label="状态" min-width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="工序数" min-width="80" align="center">
          <template #default="{ row }">
            {{ row.operations?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link @click="handleViewOperations(row)">工序</el-button>
              <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
              <el-button type="primary" link @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- Routing Edit Dialog -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑工艺路线' : '新增工艺路线'"
      width="480px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="编码" prop="code">
          <el-input v-model="form.code" :disabled="isEdit" placeholder="请输入编码" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item label="产品" prop="product_id">
          <el-select v-model="form.product_id" placeholder="请选择产品" style="width: 100%">
            <el-option 
              v-for="p in products" 
              :key="p.id" 
              :label="`${p.code} - ${p.name}`" 
              :value="p.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="版本" prop="version">
          <el-input v-model="form.version" placeholder="如: 1.0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" :active-value="1" :inactive-value="0" />
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
    
    <!-- Operations Dialog -->
    <el-dialog 
      v-model="opsDialogVisible" 
      :title="`工艺路线工序 - ${currentRouting?.name || ''}`"
      width="800px"
    >
      <div class="ops-toolbar">
        <el-button type="primary" size="small" @click="handleAddOperation">
          <el-icon><Plus /></el-icon>
          新增工序
        </el-button>
      </div>
      <el-table :data="currentRouting?.operations || []" size="small" table-layout="auto">
        <el-table-column prop="sequence" label="顺序" min-width="70" align="center" />
        <el-table-column prop="name" label="工序名称" min-width="120" />
        <el-table-column label="工作中心" min-width="100">
          <template #default="{ row }">
            {{ getResourceName(row.work_center_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="setup_time" label="准备时间(h)" min-width="100" align="right">
          <template #default="{ row }">
            {{ row.setup_time.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="run_time_per_unit" label="单件时间(h)" min-width="100" align="right">
          <template #default="{ row }">
            {{ row.run_time_per_unit.toFixed(4) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link size="small" @click="handleEditOperation(row)">编辑</el-button>
              <el-button type="primary" link size="small" @click="handleDeleteOperation(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
    
    <!-- Operation Edit Dialog -->
    <el-dialog 
      v-model="opDialogVisible" 
      :title="isEditOp ? '编辑工序' : '新增工序'"
      width="480px"
    >
      <el-form ref="opFormRef" :model="opForm" :rules="opRules" label-width="100px">
        <el-form-item label="顺序" prop="sequence">
          <el-input-number v-model="opForm.sequence" :min="1" />
        </el-form-item>
        <el-form-item label="工序名称" prop="name">
          <el-input v-model="opForm.name" placeholder="请输入工序名称" />
        </el-form-item>
        <el-form-item label="工作中心" prop="work_center_id">
          <el-select v-model="opForm.work_center_id" placeholder="请选择工作中心" style="width: 100%">
            <el-option 
              v-for="wc in workCenters" 
              :key="wc.id" 
              :label="wc.name" 
              :value="wc.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="准备时间(h)" prop="setup_time">
          <el-input-number v-model="opForm.setup_time" :min="0" :precision="2" :step="0.1" />
        </el-form-item>
        <el-form-item label="单件时间(h)" prop="run_time_per_unit">
          <el-input-number v-model="opForm.run_time_per_unit" :min="0.0001" :precision="4" :step="0.01" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="opForm.description" type="textarea" rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="opDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitOperation" :loading="submittingOp">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useMasterDataStore } from '@/stores/masterData'
import { useDSFiltersStore } from '@/stores/dsFilters'

const store = useMasterDataStore()
const dsFiltersStore = useDSFiltersStore()

const loading = computed(() => store.loading)

// 工艺路线列表（全部数据，DS工艺路线是数据源）
const routings = computed(() => store.routings || [])
const products = computed(() => store.products)
const workCenters = computed(() => store.workCenters)
const resources = computed(() => store.resources)

// 根据工作中心ID获取对应的资源名称
const getResourceName = (workCenterId) => {
  if (!workCenterId) return '-'
  const res = resources.value.find(r => r.work_center_id === workCenterId)
  return res?.name || '-'
}

// Routing form
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const form = ref({
  code: '',
  name: '',
  product_id: null,
  version: '1.0',
  is_active: 1,
  description: ''
})

const rules = {
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  product_id: [{ required: true, message: '请选择产品', trigger: 'change' }]
}

// Operations
const opsDialogVisible = ref(false)
const currentRouting = ref(null)

const opDialogVisible = ref(false)
const isEditOp = ref(false)
const editOpId = ref(null)
const submittingOp = ref(false)
const opFormRef = ref(null)

const opForm = ref({
  sequence: 10,
  name: '',
  work_center_id: null,
  setup_time: 0,
  run_time_per_unit: 0.1,
  description: ''
})

const opRules = {
  sequence: [{ required: true, message: '请输入顺序', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  work_center_id: [{ required: true, message: '请选择工作中心', trigger: 'change' }],
  run_time_per_unit: [{ required: true, message: '请输入单件时间', trigger: 'blur' }]
}

// Routing handlers
const handleAdd = () => {
  isEdit.value = false
  editId.value = null
  form.value = { code: '', name: '', product_id: null, version: '1.0', is_active: 1, description: '' }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除工艺路线 "${row.name}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await store.deleteRouting(row.id)
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (isEdit.value) {
      await store.updateRouting(editId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await store.createRouting(form.value)
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

// Operation handlers
const handleViewOperations = (routing) => {
  currentRouting.value = routing
  opsDialogVisible.value = true
}

const handleAddOperation = () => {
  isEditOp.value = false
  editOpId.value = null
  const maxSeq = currentRouting.value?.operations?.reduce((max, op) => Math.max(max, op.sequence), 0) || 0
  opForm.value = { 
    sequence: maxSeq + 10, 
    name: '', 
    work_center_id: null, 
    setup_time: 0, 
    run_time_per_unit: 0.1, 
    description: '' 
  }
  opDialogVisible.value = true
}

const handleEditOperation = (op) => {
  isEditOp.value = true
  editOpId.value = op.id
  opForm.value = { ...op }
  opDialogVisible.value = true
}

const handleDeleteOperation = async (op) => {
  try {
    await ElMessageBox.confirm(`确定要删除工序 "${op.name}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await store.deleteRoutingOperation(op.id)
    // Refresh routing
    const updatedRouting = routings.value.find(r => r.id === currentRouting.value.id)
    currentRouting.value = updatedRouting
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleSubmitOperation = async () => {
  try {
    await opFormRef.value.validate()
    submittingOp.value = true
    
    if (isEditOp.value) {
      await store.updateRoutingOperation(editOpId.value, opForm.value)
      ElMessage.success('更新成功')
    } else {
      await store.createRoutingOperation(currentRouting.value.id, opForm.value)
      ElMessage.success('创建成功')
    }
    
    // Refresh routing
    const updatedRouting = routings.value.find(r => r.id === currentRouting.value.id)
    currentRouting.value = updatedRouting
    
    opDialogVisible.value = false
  } catch (error) {
    if (error !== false) {
      ElMessage.error(isEditOp.value ? '更新失败' : '创建失败')
    }
  } finally {
    submittingOp.value = false
  }
}

onMounted(async () => {
  await store.fetchRoutings()
  store.fetchProducts()
  store.fetchWorkCenters()
  store.fetchResources()
  
  // 同步到共享store，供详细计划表使用
  dsFiltersStore.setDSRoutings(store.routings)
})
</script>

<style lang="scss" scoped>
.master-data-page {
  min-height: calc(100vh - 100px);
}

.ops-toolbar {
  margin-bottom: 16px;
}

.action-buttons {
  display: flex;
  flex-wrap: nowrap;
  gap: 4px;
}
</style>
