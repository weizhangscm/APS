<template>
  <div class="master-data-page">
    <div v-if="dsFiltersStore.selectedProductIds.length > 0" class="filter-hint">
      <el-icon><Filter /></el-icon>
      <span>{{ t('dsRouting.filterHint') }} {{ routings.length }} {{ t('dsRouting.routings') }}</span>
      <el-tag v-for="name in dsFiltersStore.selectedProductNames.slice(0, 3)" :key="name" size="small" type="info" class="filter-tag">
        {{ name }}
      </el-tag>
      <span v-if="dsFiltersStore.selectedProductNames.length > 3" class="more-hint">
        {{ t('dsRouting.andMoreProducts') }} {{ dsFiltersStore.selectedProductNames.length }} {{ t('dsRouting.products') }}
      </span>
      <el-button type="primary" link size="small" @click="goToDetailedPlan">{{ t('dsRouting.modifyFilter') }}</el-button>
    </div>
    
    <div class="page-header">
      <h1>
        <el-icon><Share /></el-icon>
        {{ t('dsRouting.title') }}
      </h1>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        {{ t('dsRouting.addRouting') }}
      </el-button>
    </div>
    
    <el-card>
      <el-table :data="routings" v-loading="loading" stripe row-key="id" table-layout="auto">
        <el-table-column prop="code" :label="t('masterData.code')" min-width="100" />
        <el-table-column prop="name" :label="t('masterData.name')" min-width="120" />
        <el-table-column :label="t('dsRouting.productCode')" min-width="120">
          <template #default="{ row }">
            {{ row.product?.code || '-' }}
          </template>
        </el-table-column>
        <el-table-column :label="t('dsRouting.productName')" min-width="120">
          <template #default="{ row }">
            {{ row.product?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="version" :label="t('masterData.version')" min-width="70" align="center" />
        <el-table-column :label="t('masterData.status')" min-width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? t('masterData.active') : t('masterData.inactive') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('dsRouting.operationCount')" min-width="80" align="center">
          <template #default="{ row }">
            {{ row.operations?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column :label="t('masterData.actions')" width="180" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link @click="handleViewOperations(row)">{{ t('masterData.operations') }}</el-button>
              <el-button type="primary" link @click="handleEdit(row)">{{ t('masterData.edit') }}</el-button>
              <el-button type="primary" link @click="handleDelete(row)">{{ t('masterData.delete') }}</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? t('dsRouting.editRouting') : t('dsRouting.addRouting')"
      width="480px"
    >
      <el-form ref="formRef" :model="form" :rules="rulesRef" label-width="80px">
        <el-form-item :label="t('masterData.code')" prop="code">
          <el-input v-model="form.code" :disabled="isEdit" :placeholder="t('masterData.enterCode')" />
        </el-form-item>
        <el-form-item :label="t('masterData.name')" prop="name">
          <el-input v-model="form.name" :placeholder="t('masterData.enterName')" />
        </el-form-item>
        <el-form-item :label="t('masterData.product')" prop="product_id">
          <el-select v-model="form.product_id" :placeholder="t('masterData.selectProduct')" style="width: 100%">
            <el-option 
              v-for="p in products" 
              :key="p.id" 
              :label="`${p.code} - ${p.name}`" 
              :value="p.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('masterData.version')" prop="version">
          <el-input v-model="form.version" :placeholder="t('masterData.enterVersion')" />
        </el-form-item>
        <el-form-item :label="t('masterData.status')">
          <el-switch v-model="form.is_active" :active-value="1" :inactive-value="0" />
        </el-form-item>
        <el-form-item :label="t('masterData.description')">
          <el-input v-model="form.description" type="textarea" rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <!-- Operations Dialog -->
    <el-dialog 
      v-model="opsDialogVisible" 
      :title="`${t('dsRouting.routingOperations')} - ${currentRouting?.name || ''}`"
      width="800px"
    >
      <div class="ops-toolbar">
        <el-button type="primary" size="small" @click="handleAddOperation">
          <el-icon><Plus /></el-icon>
          {{ t('dsRouting.addOperation') }}
        </el-button>
      </div>
      <el-table :data="currentRouting?.operations || []" size="small" table-layout="auto">
        <el-table-column prop="sequence" :label="t('dsRouting.sequence')" min-width="70" align="center" />
        <el-table-column prop="name" :label="t('dsRouting.operationName')" min-width="120" />
        <el-table-column :label="t('dsRouting.resource')" min-width="120">
          <template #default="{ row }">
            {{ getResourceDisplayName(row) }}
          </template>
        </el-table-column>
        <el-table-column prop="setup_time" :label="t('dsRouting.setupTime')" min-width="100" align="right">
          <template #default="{ row }">
            {{ row.setup_time.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="run_time_per_unit" :label="t('dsRouting.runTimePerUnit')" min-width="100" align="right">
          <template #default="{ row }">
            {{ row.run_time_per_unit.toFixed(4) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('masterData.actions')" width="140" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link size="small" @click="handleEditOperation(row)">{{ t('dsRouting.editOperation') }}</el-button>
              <el-button type="primary" link size="small" @click="handleDeleteOperation(row)">{{ t('dsRouting.deleteOperation') }}</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
    
    <el-dialog 
      v-model="opDialogVisible" 
      :title="isEditOp ? t('dsRouting.editOperation') : t('dsRouting.addOperation')"
      width="480px"
    >
      <el-form ref="opFormRef" :model="opForm" :rules="opRulesRef" label-width="100px">
        <el-form-item :label="t('dsRouting.sequence')" prop="sequence">
          <el-input-number v-model="opForm.sequence" :min="1" />
        </el-form-item>
        <el-form-item :label="t('dsRouting.operationName')" prop="name">
          <el-input v-model="opForm.name" :placeholder="t('dsRouting.enterOperationName')" />
        </el-form-item>
        <el-form-item :label="t('dsRouting.resource')" prop="resource_id">
          <el-select v-model="opForm.resource_id" :placeholder="t('dsRouting.selectResource')" style="width: 100%">
            <el-option 
              v-for="r in resources" 
              :key="r.id" 
              :label="`${r.code || ''} - ${r.name}`" 
              :value="r.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('dsRouting.setupTime')" prop="setup_time">
          <el-input-number v-model="opForm.setup_time" :min="0" :precision="2" :step="0.1" />
        </el-form-item>
        <el-form-item :label="t('dsRouting.runTimePerUnit')" prop="run_time_per_unit">
          <el-input-number v-model="opForm.run_time_per_unit" :min="0.0001" :precision="4" :step="0.01" />
        </el-form-item>
        <el-form-item :label="t('masterData.description')">
          <el-input v-model="opForm.description" type="textarea" rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="opDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmitOperation" :loading="submittingOp">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Filter } from '@element-plus/icons-vue'
import { useMasterDataStore } from '@/stores/masterData'
import { useDSFiltersStore } from '@/stores/dsFilters'
import { useI18nStore } from '@/stores/i18n'

const router = useRouter()
const store = useMasterDataStore()
const dsFiltersStore = useDSFiltersStore()
const i18nStore = useI18nStore()
const t = (key) => i18nStore.t(key)

const loading = computed(() => store.loading)

// 根据详细计划表筛选条件过滤后的工艺路线列表
const routings = computed(() => {
  const allRoutings = store.routings || []
  const selectedProductIds = dsFiltersStore.selectedProductIds
  
  // 如果详细计划表没有选择产品，显示所有工艺路线
  if (!selectedProductIds || selectedProductIds.length === 0) {
    return allRoutings
  }
  // 否则只显示选中产品的工艺路线
  return allRoutings.filter(r => selectedProductIds.includes(r.product_id))
})
const products = computed(() => store.products)
const resources = computed(() => store.resources)

// 工序表中显示资源名称：优先 resource / resource_id（与 DS资源 一致），否则按 work_center_id 取第一个
const getResourceDisplayName = (row) => {
  if (row.resource?.name) return row.resource.name
  if (row.resource_id) {
    const r = resources.value.find(x => x.id === row.resource_id)
    return r ? `${r.code || ''} - ${r.name}` : '-'
  }
  if (row.work_center_id) {
    const r = resources.value.find(x => x.work_center_id === row.work_center_id)
    return r?.name || '-'
  }
  return '-'
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

const rulesRef = computed(() => ({
  code: [{ required: true, message: t('masterData.enterCode'), trigger: 'blur' }],
  name: [{ required: true, message: t('masterData.enterName'), trigger: 'blur' }],
  product_id: [{ required: true, message: t('masterData.selectProduct'), trigger: 'change' }]
}))

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
  resource_id: null,
  setup_time: 0,
  run_time_per_unit: 0.1,
  description: ''
})

const opRulesRef = computed(() => ({
  sequence: [{ required: true, message: t('dsRouting.enterSequence'), trigger: 'blur' }],
  name: [{ required: true, message: t('dsRouting.enterOperationName'), trigger: 'blur' }],
  resource_id: [{ required: true, message: t('dsRouting.selectResource'), trigger: 'change' }],
  run_time_per_unit: [{ required: true, message: t('dsRouting.enterRunTime'), trigger: 'blur' }]
}))

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
    await ElMessageBox.confirm(t('dsRouting.confirmDeleteRouting').replace('{name}', row.name), t('orders.confirmDeleteTitle'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    await store.deleteRouting(row.id)
    ElMessage.success(t('messages.deleteSuccess'))
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('messages.deleteFailed'))
    }
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (isEdit.value) {
      await store.updateRouting(editId.value, form.value)
      ElMessage.success(t('messages.updateSuccess'))
    } else {
      await store.createRouting(form.value)
      ElMessage.success(t('messages.createSuccess'))
    }
    
    dialogVisible.value = false
  } catch (error) {
    if (error !== false) {
      ElMessage.error(isEdit.value ? t('messages.updateFailed') : t('messages.createFailed'))
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
    resource_id: null, 
    setup_time: 0, 
    run_time_per_unit: 0.1, 
    description: '' 
  }
  opDialogVisible.value = true
}

const handleEditOperation = (op) => {
  isEditOp.value = true
  editOpId.value = op.id
  const resourceId = op.resource_id ?? (op.work_center_id && resources.value.length
    ? resources.value.find(r => r.work_center_id === op.work_center_id)?.id
    : null)
  opForm.value = { ...op, resource_id: resourceId }
  opDialogVisible.value = true
}

const handleDeleteOperation = async (op) => {
  try {
    await ElMessageBox.confirm(t('dsRouting.confirmDeleteOperation') + ` "${op.name}"?`, t('orders.confirmDeleteTitle'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    await store.deleteRoutingOperation(op.id)
    // Refresh routing
    const updatedRouting = routings.value.find(r => r.id === currentRouting.value.id)
    currentRouting.value = updatedRouting
    ElMessage.success(t('messages.deleteSuccess'))
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('messages.deleteFailed'))
    }
  }
}

const handleSubmitOperation = async () => {
  try {
    await opFormRef.value.validate()
    submittingOp.value = true
    
    if (isEditOp.value) {
      await store.updateRoutingOperation(editOpId.value, opForm.value)
      ElMessage.success(t('messages.updateSuccess'))
    } else {
      await store.createRoutingOperation(currentRouting.value.id, opForm.value)
      ElMessage.success(t('messages.createSuccess'))
    }
    
    const updatedRouting = routings.value.find(r => r.id === currentRouting.value.id)
    currentRouting.value = updatedRouting
    
    opDialogVisible.value = false
  } catch (error) {
    if (error !== false) {
      ElMessage.error(isEditOp.value ? t('messages.updateFailed') : t('messages.createFailed'))
    }
  } finally {
    submittingOp.value = false
  }
}

// 跳转到详细计划表
const goToDetailedPlan = () => {
  router.push('/ds')
}

onMounted(() => {
  store.fetchRoutings()
  store.fetchProducts()
  store.fetchWorkCenters()
  store.fetchResources()
})
</script>

<style lang="scss" scoped>
.master-data-page {
  min-height: calc(100vh - 100px);
}

// 筛选状态提示
.filter-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  margin-bottom: 16px;
  background: #ecf5ff;
  border-radius: 8px;
  font-size: 13px;
  color: #409eff;
  
  .el-icon {
    font-size: 16px;
  }
  
  .filter-tag {
    margin: 0 2px;
  }
  
  .more-hint {
    color: #909399;
  }
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
