<template>
  <div class="master-data-page">
    <div class="page-header">
      <h1>
        <el-icon><Monitor /></el-icon>
        资源管理
      </h1>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增资源
      </el-button>
    </div>
    
    <el-card>
      <el-table :data="resources" v-loading="loading" stripe table-layout="auto">
        <el-table-column prop="code" label="编码" min-width="100" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column label="工作中心" min-width="120">
          <template #default="{ row }">
            {{ row.work_center?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="capacity_per_day" label="日产能(小时)" min-width="110" align="right">
          <template #default="{ row }">
            {{ row.capacity_per_day.toFixed(1) }}
          </template>
        </el-table-column>
        <el-table-column prop="efficiency" label="效率" min-width="80" align="right">
          <template #default="{ row }">
            {{ (row.efficiency * 100).toFixed(0) }}%
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
              <el-button type="primary" link @click="handleDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- Edit Dialog -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑资源' : '新增资源'"
      width="480px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="编码" prop="code">
          <el-input v-model="form.code" :disabled="isEdit" placeholder="请输入编码" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item label="工作中心" prop="work_center_id">
          <el-select v-model="form.work_center_id" placeholder="请选择工作中心" style="width: 100%">
            <el-option 
              v-for="wc in workCenters" 
              :key="wc.id" 
              :label="wc.name" 
              :value="wc.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="日产能(小时)" prop="capacity_per_day">
          <el-input-number v-model="form.capacity_per_day" :min="0" :max="24" :precision="1" />
        </el-form-item>
        <el-form-item label="效率" prop="efficiency">
          <el-slider v-model="form.efficiency" :min="0" :max="2" :step="0.1" show-input />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" rows="3" placeholder="请输入描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useMasterDataStore } from '@/stores/masterData'

const store = useMasterDataStore()

const loading = computed(() => store.loading)
const resources = computed(() => store.resources)
const workCenters = computed(() => store.workCenters)

const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const form = ref({
  code: '',
  name: '',
  work_center_id: null,
  capacity_per_day: 8.0,
  efficiency: 1.0,
  description: ''
})

const rules = {
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  work_center_id: [{ required: true, message: '请选择工作中心', trigger: 'change' }]
}

const handleAdd = () => {
  isEdit.value = false
  editId.value = null
  form.value = { code: '', name: '', work_center_id: null, capacity_per_day: 8.0, efficiency: 1.0, description: '' }
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
    await ElMessageBox.confirm(`确定要删除资源 "${row.name}" 吗？`, '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await store.deleteResource(row.id)
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
      await store.updateResource(editId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await store.createResource(form.value)
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

onMounted(() => {
  store.fetchResources()
  store.fetchWorkCenters()
})
</script>

<style lang="scss" scoped>
.master-data-page {
  min-height: calc(100vh - 100px);
}

.action-buttons {
  display: flex;
  flex-wrap: nowrap;
  gap: 4px;
}
</style>
