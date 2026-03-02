<template>
  <div class="shifts-view">
    <div class="page-header">
      <h1>
        <el-icon><Clock /></el-icon>
        班次
      </h1>
      <div class="header-buttons">
        <el-button @click="handleDefineShiftOrder">定义班次顺序</el-button>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新增班次
        </el-button>
      </div>
    </div>
    
    <el-card>
      <el-table :data="shifts" v-loading="loading" stripe table-layout="auto">
        <el-table-column label="资源" min-width="150">
          <template #default="{ row }">
            {{ getResourceName(row.resource_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="shift_code" label="班次" min-width="100" />
        <el-table-column prop="shift_name" label="班次名称" min-width="120" />
        <el-table-column prop="start_time" label="开始时间" min-width="100" align="center" />
        <el-table-column prop="end_time" label="结束时间" min-width="100" align="center" />
        <el-table-column prop="break_time" label="休息时间(分钟)" min-width="120" align="center" />
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
              <el-button type="primary" link @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 新增/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑班次' : '新增班次'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="资源" prop="resource_id">
          <el-select v-model="form.resource_id" placeholder="请选择资源" style="width: 100%">
            <el-option 
              v-for="resource in resources" 
              :key="resource.id" 
              :label="`${resource.code} - ${resource.name}`" 
              :value="resource.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="班次" prop="shift_code">
          <el-input v-model="form.shift_code" placeholder="例如：SHIFT1" />
        </el-form-item>
        <el-form-item label="班次名称" prop="shift_name">
          <el-input v-model="form.shift_name" placeholder="例如：早班" />
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-time-picker 
            v-model="form.start_time" 
            format="HH:mm"
            value-format="HH:mm"
            placeholder="选择开始时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_time">
          <el-time-picker 
            v-model="form.end_time" 
            format="HH:mm"
            value-format="HH:mm"
            placeholder="选择结束时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="休息时间(分钟)" prop="break_time">
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
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 定义班次顺序对话框 -->
    <el-dialog 
      v-model="shiftOrderDialogVisible" 
      title="定义班次顺序"
      width="500px"
    >
      <el-form label-width="100px">
        <el-form-item label="班次顺序">
          <el-select v-model="shiftOrder" placeholder="选择班次顺序" style="width: 100%">
            <el-option label="请选择" value="" disabled />
            <el-option label="早班 → 中班 → 晚班" value="morning-afternoon-night" />
            <el-option label="白班 → 夜班" value="day-night" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="循环模式">
          <el-radio-group v-model="cycleMode">
            <el-radio value="daily">每日</el-radio>
            <el-radio value="weekly">每周</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shiftOrderDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveShiftOrder">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Clock, Plus } from '@element-plus/icons-vue'

// Mock data - 在实际项目中应该从API获取
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

const rules = {
  resource_id: [{ required: true, message: '请选择资源', trigger: 'change' }],
  shift_code: [{ required: true, message: '请输入班次代码', trigger: 'blur' }],
  shift_name: [{ required: true, message: '请输入班次名称', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }]
}

// 获取资源名称
const getResourceName = (resourceId) => {
  const resource = resources.value.find(r => r.id === resourceId)
  return resource ? `${resource.code} - ${resource.name}` : '-'
}

// 加载数据
const fetchData = async () => {
  loading.value = true
  try {
    // TODO: 从API加载班次数据
    // const response = await shiftsApi.getShifts()
    // shifts.value = response.data
    
    // Mock数据
    shifts.value = [
      {
        id: 1,
        resource_id: 1,
        shift_code: 'SHIFT1',
        shift_name: '早班',
        start_time: '08:00',
        end_time: '16:00',
        break_time: 60
      },
      {
        id: 2,
        resource_id: 1,
        shift_code: 'SHIFT2',
        shift_name: '晚班',
        start_time: '16:00',
        end_time: '00:00',
        break_time: 60
      }
    ]
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 加载资源列表
const fetchResources = async () => {
  try {
    // TODO: 从API加载资源数据
    // const response = await resourcesApi.getResources()
    // resources.value = response.data
    
    // Mock数据
    resources.value = [
      { id: 1, code: 'CNC-1', name: 'CNC机床-1' },
      { id: 2, code: 'CNC-2', name: 'CNC机床-2' },
      { id: 3, code: 'CNC-3', name: 'CNC机床-3' }
    ]
  } catch (error) {
    ElMessage.error('加载资源列表失败')
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
    await ElMessageBox.confirm(`确定要删除班次"${row.shift_name}"吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    // TODO: 调用删除API
    // await shiftsApi.deleteShift(row.id)
    
    // Mock删除
    const index = shifts.value.findIndex(s => s.id === row.id)
    if (index !== -1) {
      shifts.value.splice(index, 1)
    }
    
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
    
    // TODO: 调用API保存
    if (isEdit.value) {
      // await shiftsApi.updateShift(editId.value, form.value)
      
      // Mock更新
      const index = shifts.value.findIndex(s => s.id === editId.value)
      if (index !== -1) {
        shifts.value[index] = { ...form.value, id: editId.value }
      }
      
      ElMessage.success('更新成功')
    } else {
      // await shiftsApi.createShift(form.value)
      
      // Mock新增
      const newShift = {
        ...form.value,
        id: shifts.value.length + 1
      }
      shifts.value.push(newShift)
      
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    fetchData()
  } catch (error) {
    if (error !== false) {
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    }
  } finally {
    submitting.value = false
  }
}

const handleDefineShiftOrder = () => {
  shiftOrderDialogVisible.value = true
}

const handleSaveShiftOrder = () => {
  ElMessage.success('班次顺序已保存')
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
