<template>
  <div class="shifts-view">
    <div class="page-header">
      <h1>
        <el-icon><Clock /></el-icon>
        {{ t('shifts.title') }}
      </h1>
      <div class="header-buttons">
        <el-button @click="handleDefineShiftOrder">{{ t('shifts.defineShiftOrder') }}</el-button>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          {{ t('shifts.addShift') }}
        </el-button>
      </div>
    </div>
    
    <el-card>
      <el-table :data="shifts" v-loading="loading" stripe table-layout="auto">
        <el-table-column :label="t('shifts.resource')" min-width="150">
          <template #default="{ row }">
            {{ getResourceName(row.resource_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="shift_code" :label="t('shifts.shiftCode')" min-width="100" />
        <el-table-column prop="shift_name" :label="t('shifts.shiftName')" min-width="120" />
        <el-table-column prop="start_time" :label="t('shifts.startTime')" min-width="100" align="center" />
        <el-table-column prop="end_time" :label="t('shifts.endTime')" min-width="100" align="center" />
        <el-table-column prop="break_time" :label="t('shifts.breakTime')" min-width="120" align="center" />
        <el-table-column :label="t('shifts.actions')" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link @click="handleEdit(row)">{{ t('shifts.edit') }}</el-button>
              <el-button type="primary" link @click="handleDelete(row)">{{ t('shifts.delete') }}</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 新增/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? t('shifts.editShift') : t('shifts.addShift')"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="rulesRef" label-width="120px">
        <el-form-item :label="t('shifts.resource')" prop="resource_id">
          <el-select v-model="form.resource_id" :placeholder="t('shifts.selectResource')" style="width: 100%">
            <el-option 
              v-for="resource in resources" 
              :key="resource.id" 
              :label="`${resource.code} - ${resource.name}`" 
              :value="resource.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('shifts.shiftCode')" prop="shift_code">
          <el-input v-model="form.shift_code" :placeholder="t('shifts.exampleShiftCode')" />
        </el-form-item>
        <el-form-item :label="t('shifts.shiftName')" prop="shift_name">
          <el-input v-model="form.shift_name" :placeholder="t('shifts.exampleMorningShift')" />
        </el-form-item>
        <el-form-item :label="t('shifts.startTime')" prop="start_time">
          <el-time-picker 
            v-model="form.start_time" 
            format="HH:mm"
            value-format="HH:mm"
            :placeholder="t('shifts.selectStartTime')"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('shifts.endTime')" prop="end_time">
          <el-time-picker 
            v-model="form.end_time" 
            format="HH:mm"
            value-format="HH:mm"
            :placeholder="t('shifts.selectEndTime')"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item :label="t('shifts.breakTime')" prop="break_time">
          <el-input-number 
            v-model="form.break_time" 
            :min="0" 
            :max="480"
            :step="15"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <!-- 定义班次顺序对话框 -->
    <el-dialog 
      v-model="shiftOrderDialogVisible" 
      :title="t('shifts.defineShiftOrder')"
      width="500px"
    >
      <el-form label-width="100px">
        <el-form-item :label="t('shifts.shiftOrder')">
          <el-select v-model="shiftOrder" :placeholder="t('shifts.selectShiftOrder')" style="width: 100%">
            <el-option :label="t('shifts.pleaseSelect')" value="" disabled />
            <el-option :label="t('shifts.morningAfternoonNight')" value="morning-afternoon-night" />
            <el-option :label="t('shifts.dayNight')" value="day-night" />
            <el-option :label="t('shifts.custom')" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('shifts.cycleMode')">
          <el-radio-group v-model="cycleMode">
            <el-radio value="daily">{{ t('shifts.daily') }}</el-radio>
            <el-radio value="weekly">{{ t('shifts.weekly') }}</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shiftOrderDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSaveShiftOrder">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Clock, Plus } from '@element-plus/icons-vue'
import { masterDataApi } from '@/api'
import { useI18nStore } from '@/stores/i18n'

const i18nStore = useI18nStore()
const t = (key) => i18nStore.t(key)

const shifts = ref([])
const resources = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const shiftOrderDialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const submitting = ref(false)
const formRef = ref(null)
const shiftOrder = ref('')
const cycleMode = ref('daily')

const form = ref({
  resource_id: null,
  shift_code: '',
  shift_name: '',
  start_time: '',
  end_time: '',
  break_time: 0
})

const rulesRef = computed(() => ({
  resource_id: [{ required: true, message: t('shifts.selectResource'), trigger: 'change' }],
  shift_code: [{ required: true, message: t('shifts.enterShiftCode'), trigger: 'blur' }],
  shift_name: [{ required: true, message: t('shifts.enterShiftName'), trigger: 'blur' }],
  start_time: [{ required: true, message: t('shifts.selectStartTime'), trigger: 'change' }],
  end_time: [{ required: true, message: t('shifts.selectEndTime'), trigger: 'change' }]
}))

const getResourceName = (resourceId) => {
  const resource = resources.value.find(r => r.id === resourceId)
  return resource ? `${resource.code} - ${resource.name}` : '-'
}

const fetchData = async () => {
  loading.value = true
  try {
    const data = await masterDataApi.getShifts()
    shifts.value = data || []
  } catch (error) {
    ElMessage.error(t('shifts.loadDataFailed'))
  } finally {
    loading.value = false
  }
}

const fetchResources = async () => {
  try {
    const data = await masterDataApi.getResources()
    resources.value = data || []
  } catch (error) {
    ElMessage.error(t('shifts.loadResourcesFailed'))
  }
}

const handleAdd = () => {
  isEdit.value = false
  editId.value = null
  form.value = {
    resource_id: null,
    shift_code: '',
    shift_name: '',
    start_time: '08:00',
    end_time: '17:00',
    break_time: 60
  }
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
    await ElMessageBox.confirm(
      t('shifts.confirmDeleteShift').replace('{name}', row.shift_name),
      t('orders.confirmDeleteTitle'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )
    await masterDataApi.deleteShift(row.id)
    ElMessage.success(t('orders.deleteSuccess'))
    await fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('orders.deleteFailed'))
    }
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    if (isEdit.value) {
      await masterDataApi.updateShift(editId.value, form.value)
      ElMessage.success(t('orders.updateSuccess'))
    } else {
      await masterDataApi.createShift(form.value)
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

const handleDefineShiftOrder = () => {
  shiftOrderDialogVisible.value = true
}

const handleSaveShiftOrder = () => {
  ElMessage.success(t('shifts.shiftOrderSaved'))
  shiftOrderDialogVisible.value = false
}

onMounted(() => {
  fetchData()
  fetchResources()
})
</script>

<style lang="scss" scoped>
.shifts-view {
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
  
  .header-buttons {
    display: flex;
    gap: 12px;
  }
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 8px;
}
</style>
