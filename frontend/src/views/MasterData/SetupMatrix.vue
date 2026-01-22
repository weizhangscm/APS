<template>
  <div class="setup-matrix-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>切换矩阵配置</h2>
      <p class="subtitle">配置产品切换时间，参考 SAP PPDS Setup Matrix</p>
    </div>

    <!-- 标签页切换 -->
    <el-tabs v-model="activeTab" type="card" class="m3-tabs">
      <!-- 切换组管理 -->
      <el-tab-pane label="切换组" name="groups">
        <div class="tab-toolbar">
          <el-button type="primary" @click="handleAddGroup">
            <el-icon><Plus /></el-icon>
            新建切换组
          </el-button>
        </div>

        <el-table :data="setupGroups" v-loading="loading" class="m3-table" table-layout="auto">
          <el-table-column prop="code" label="代码" min-width="100" />
          <el-table-column prop="name" label="名称" min-width="150" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
          <el-table-column label="包含产品" min-width="100" align="center">
            <template #default="{ row }">
              <span>{{ getProductCountForGroup(row.id) }} 个产品</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="140" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button type="primary" link @click="handleEditGroup(row)">编辑</el-button>
                <el-button type="primary" link @click="handleDeleteGroup(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 产品分配 -->
      <el-tab-pane label="产品分配" name="assignments">
        <div class="tab-toolbar">
          <el-button type="primary" @click="handleAddAssignment">
            <el-icon><Plus /></el-icon>
            分配产品
          </el-button>
          <el-select v-model="filterWorkCenterId" placeholder="筛选工作中心" clearable style="width: 200px; margin-left: 16px;">
            <el-option label="全局" :value="null" />
            <el-option v-for="wc in workCenters" :key="wc.id" :label="wc.name" :value="wc.id" />
          </el-select>
        </div>

        <el-table :data="filteredAssignments" v-loading="loading" class="m3-table" table-layout="auto">
          <el-table-column label="产品" min-width="200">
            <template #default="{ row }">
              {{ row.product?.code }} - {{ row.product?.name }}
            </template>
          </el-table-column>
          <el-table-column label="切换组" min-width="150">
            <template #default="{ row }">
              <el-tag>{{ row.setup_group?.name || '-' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="适用工作中心" min-width="150">
            <template #default="{ row }">
              {{ row.work_center?.name || '全局' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-button type="primary" link @click="handleDeleteAssignment(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 切换矩阵 -->
      <el-tab-pane label="切换矩阵" name="matrix">
        <div class="tab-toolbar">
          <el-select v-model="matrixScope" placeholder="选择范围" style="width: 150px;">
            <el-option label="全局" value="global" />
            <el-option label="工作中心" value="work_center" />
            <el-option label="资源" value="resource" />
          </el-select>
          
          <el-select 
            v-if="matrixScope === 'work_center'" 
            v-model="selectedWorkCenterId" 
            placeholder="选择工作中心" 
            style="width: 200px; margin-left: 12px;"
            @change="loadMatrixGrid"
          >
            <el-option v-for="wc in workCenters" :key="wc.id" :label="wc.name" :value="wc.id" />
          </el-select>
          
          <el-select 
            v-if="matrixScope === 'resource'" 
            v-model="selectedResourceId" 
            placeholder="选择资源" 
            style="width: 200px; margin-left: 12px;"
            @change="loadMatrixGrid"
          >
            <el-option v-for="r in resources" :key="r.id" :label="`${r.code} - ${r.name}`" :value="r.id" />
          </el-select>

          <el-button type="primary" style="margin-left: 16px;" @click="saveMatrix" :loading="saving">
            <el-icon><Check /></el-icon>
            保存矩阵
          </el-button>
        </div>

        <div class="matrix-grid-container" v-loading="loading">
          <div class="matrix-description">
            <p><strong>说明：</strong>行表示"从"切换组，列表示"到"切换组。单元格值为切换时间（小时）。</p>
            <p>相同切换组之间切换时间为0（对角线）。空单元格表示使用上级默认值或无需切换时间。</p>
          </div>

          <div class="matrix-table-wrapper" v-if="matrixGrid.setup_groups?.length > 0">
            <table class="matrix-table">
              <thead>
                <tr>
                  <th class="corner-cell">从 \ 到</th>
                  <th v-for="group in matrixGrid.setup_groups" :key="group.id" class="header-cell">
                    {{ group.name }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="fromGroup in matrixGrid.setup_groups" :key="fromGroup.id">
                  <td class="row-header">{{ fromGroup.name }}</td>
                  <td v-for="toGroup in matrixGrid.setup_groups" :key="toGroup.id" class="matrix-cell">
                    <el-input-number 
                      v-if="fromGroup.id !== toGroup.id"
                      v-model="matrixValues[fromGroup.id][toGroup.id]"
                      :min="0"
                      :step="0.5"
                      :precision="1"
                      size="small"
                      controls-position="right"
                      placeholder="-"
                    />
                    <span v-else class="diagonal-cell">-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <el-empty v-else description="暂无切换组，请先创建切换组" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 切换组对话框 -->
    <el-dialog 
      v-model="groupDialogVisible" 
      :title="editingGroup ? '编辑切换组' : '新建切换组'"
      width="500px"
    >
      <el-form :model="groupForm" label-width="80px">
        <el-form-item label="代码" required>
          <el-input v-model="groupForm.code" placeholder="例如: GRP-A" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="groupForm.name" placeholder="例如: 金属件组" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="groupForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="groupDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveGroup" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 产品分配对话框 -->
    <el-dialog v-model="assignmentDialogVisible" title="分配产品到切换组" width="500px">
      <el-form :model="assignmentForm" label-width="100px">
        <el-form-item label="产品" required>
          <el-select v-model="assignmentForm.product_id" filterable placeholder="选择产品" style="width: 100%;">
            <el-option v-for="p in products" :key="p.id" :label="`${p.code} - ${p.name}`" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="切换组" required>
          <el-select v-model="assignmentForm.setup_group_id" placeholder="选择切换组" style="width: 100%;">
            <el-option v-for="g in setupGroups" :key="g.id" :label="g.name" :value="g.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="适用工作中心">
          <el-select v-model="assignmentForm.work_center_id" clearable placeholder="全局（不限）" style="width: 100%;">
            <el-option v-for="wc in workCenters" :key="wc.id" :label="wc.name" :value="wc.id" />
          </el-select>
          <div class="form-tip">留空表示全局适用</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignmentDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAssignment" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Check } from '@element-plus/icons-vue'
import { setupMatrixApi, masterDataApi } from '@/api'

// 状态
const loading = ref(false)
const saving = ref(false)
const activeTab = ref('groups')

// 数据
const setupGroups = ref([])
const productAssignments = ref([])
const products = ref([])
const workCenters = ref([])
const resources = ref([])
const matrixGrid = ref({ setup_groups: [], matrix: {} })
const matrixValues = reactive({})

// 筛选
const filterWorkCenterId = ref(null)

// 矩阵范围
const matrixScope = ref('global')
const selectedWorkCenterId = ref(null)
const selectedResourceId = ref(null)

// 对话框
const groupDialogVisible = ref(false)
const assignmentDialogVisible = ref(false)
const editingGroup = ref(null)

const groupForm = reactive({
  code: '',
  name: '',
  description: ''
})

const assignmentForm = reactive({
  product_id: null,
  setup_group_id: null,
  work_center_id: null
})

// 计算属性
const filteredAssignments = computed(() => {
  if (filterWorkCenterId.value === null) {
    return productAssignments.value
  }
  return productAssignments.value.filter(a => 
    a.work_center_id === filterWorkCenterId.value || a.work_center_id === null
  )
})

// 方法
function getProductCountForGroup(groupId) {
  return productAssignments.value.filter(a => a.setup_group_id === groupId).length
}

async function loadData() {
  loading.value = true
  try {
    const [groupsRes, assignmentsRes, productsRes, wcRes, resRes] = await Promise.all([
      setupMatrixApi.getSetupGroups(),
      setupMatrixApi.getProductAssignments(),
      masterDataApi.getProducts(),
      masterDataApi.getWorkCenters(),
      masterDataApi.getResources()
    ])
    setupGroups.value = groupsRes
    productAssignments.value = assignmentsRes
    products.value = productsRes
    workCenters.value = wcRes
    resources.value = resRes
    
    // 加载矩阵
    await loadMatrixGrid()
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

async function loadMatrixGrid() {
  loading.value = true
  try {
    let resourceId = null
    let workCenterId = null
    
    if (matrixScope.value === 'resource' && selectedResourceId.value) {
      resourceId = selectedResourceId.value
    } else if (matrixScope.value === 'work_center' && selectedWorkCenterId.value) {
      workCenterId = selectedWorkCenterId.value
    }
    
    const grid = await setupMatrixApi.getMatrixGrid(resourceId, workCenterId)
    matrixGrid.value = grid
    
    // 初始化矩阵值
    for (const fromGroup of grid.setup_groups) {
      if (!matrixValues[fromGroup.id]) {
        matrixValues[fromGroup.id] = {}
      }
      for (const toGroup of grid.setup_groups) {
        if (fromGroup.id !== toGroup.id) {
          matrixValues[fromGroup.id][toGroup.id] = grid.matrix?.[fromGroup.id]?.[toGroup.id] || null
        }
      }
    }
  } catch (error) {
    console.error('加载矩阵失败', error)
  } finally {
    loading.value = false
  }
}

// 切换组操作
function handleAddGroup() {
  editingGroup.value = null
  groupForm.code = ''
  groupForm.name = ''
  groupForm.description = ''
  groupDialogVisible.value = true
}

function handleEditGroup(group) {
  editingGroup.value = group
  groupForm.code = group.code
  groupForm.name = group.name
  groupForm.description = group.description || ''
  groupDialogVisible.value = true
}

async function saveGroup() {
  if (!groupForm.code || !groupForm.name) {
    ElMessage.warning('请填写代码和名称')
    return
  }
  
  saving.value = true
  try {
    if (editingGroup.value) {
      await setupMatrixApi.updateSetupGroup(editingGroup.value.id, groupForm)
      ElMessage.success('更新成功')
    } else {
      await setupMatrixApi.createSetupGroup(groupForm)
      ElMessage.success('创建成功')
    }
    groupDialogVisible.value = false
    await loadData()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDeleteGroup(group) {
  try {
    await ElMessageBox.confirm(`确定删除切换组 "${group.name}"？`, '确认删除')
    await setupMatrixApi.deleteSetupGroup(group.id)
    ElMessage.success('删除成功')
    await loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 产品分配操作
function handleAddAssignment() {
  assignmentForm.product_id = null
  assignmentForm.setup_group_id = null
  assignmentForm.work_center_id = null
  assignmentDialogVisible.value = true
}

async function saveAssignment() {
  if (!assignmentForm.product_id || !assignmentForm.setup_group_id) {
    ElMessage.warning('请选择产品和切换组')
    return
  }
  
  saving.value = true
  try {
    await setupMatrixApi.assignProductToGroup(assignmentForm)
    ElMessage.success('分配成功')
    assignmentDialogVisible.value = false
    await loadData()
  } catch (error) {
    ElMessage.error('分配失败')
  } finally {
    saving.value = false
  }
}

async function handleDeleteAssignment(assignment) {
  try {
    await ElMessageBox.confirm('确定删除此分配？', '确认删除')
    await setupMatrixApi.removeProductAssignment(assignment.id)
    ElMessage.success('删除成功')
    await loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 保存矩阵
async function saveMatrix() {
  saving.value = true
  try {
    const entries = []
    
    let resourceId = null
    let workCenterId = null
    
    if (matrixScope.value === 'resource' && selectedResourceId.value) {
      resourceId = selectedResourceId.value
    } else if (matrixScope.value === 'work_center' && selectedWorkCenterId.value) {
      workCenterId = selectedWorkCenterId.value
    }
    
    for (const fromGroupId in matrixValues) {
      for (const toGroupId in matrixValues[fromGroupId]) {
        const value = matrixValues[fromGroupId][toGroupId]
        if (value !== null && value !== undefined && value > 0) {
          entries.push({
            from_setup_group_id: parseInt(fromGroupId),
            to_setup_group_id: parseInt(toGroupId),
            resource_id: resourceId,
            work_center_id: workCenterId,
            changeover_time: value
          })
        }
      }
    }
    
    await setupMatrixApi.batchUpdateMatrix(entries)
    ElMessage.success('矩阵保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 监听范围变化
watch(matrixScope, () => {
  selectedWorkCenterId.value = null
  selectedResourceId.value = null
  if (matrixScope.value === 'global') {
    loadMatrixGrid()
  }
})

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.setup-matrix-view {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
  
  h2 {
    margin: 0 0 8px 0;
    font-size: 24px;
    font-weight: 500;
    color: var(--m3-on-surface);
  }
  
  .subtitle {
    margin: 0;
    color: var(--m3-on-surface-variant);
    font-size: 14px;
  }
}

.m3-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 24px;
  }
}

.tab-toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding: 16px;
  background: var(--m3-surface-container-low);
  border-radius: 12px;
}

.m3-table {
  border-radius: 12px;
  overflow: hidden;
}

.matrix-grid-container {
  padding: 16px;
  background: var(--m3-surface-container-low);
  border-radius: 12px;
}

.matrix-description {
  margin-bottom: 20px;
  padding: 12px 16px;
  background: var(--m3-surface-container);
  border-radius: 8px;
  font-size: 13px;
  color: var(--m3-on-surface-variant);
  
  p {
    margin: 0;
    &:first-child {
      margin-bottom: 4px;
    }
  }
}

.matrix-table-wrapper {
  overflow-x: auto;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--m3-surface);
  border-radius: 8px;
  overflow: hidden;
  
  th, td {
    padding: 12px;
    text-align: center;
    border: 1px solid var(--m3-outline-variant);
  }
  
  .corner-cell {
    background: var(--m3-surface-container-highest);
    font-weight: 600;
    min-width: 120px;
  }
  
  .header-cell {
    background: var(--m3-primary-container);
    color: var(--m3-on-primary-container);
    font-weight: 500;
    min-width: 100px;
  }
  
  .row-header {
    background: var(--m3-secondary-container);
    color: var(--m3-on-secondary-container);
    font-weight: 500;
    text-align: left;
  }
  
  .matrix-cell {
    min-width: 100px;
    
    .el-input-number {
      width: 80px;
    }
  }
  
  .diagonal-cell {
    color: var(--m3-outline);
    font-style: italic;
  }
}

.form-tip {
  font-size: 12px;
  color: var(--m3-on-surface-variant);
  margin-top: 4px;
}

.action-buttons {
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
}
</style>
