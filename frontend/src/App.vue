<template>
  <el-config-provider :locale="zhCn">
    <!-- 登录页面 -->
    <router-view v-if="isLoginPage" />
    
    <!-- 主应用布局 -->
    <div v-else class="app-container">
      <el-container class="main-container">
        <el-aside width="280px" class="sidebar">
          <div class="logo">
            <div class="logo-icon we-logo">
              <span>We</span>
            </div>
            <span>AI Native APS</span>
          </div>
          <el-menu
            :default-active="activeMenu"
            class="sidebar-menu"
            router
          >
            <el-menu-item index="/gantt">
              <el-icon><DataLine /></el-icon>
              <span>甘特图排程</span>
            </el-menu-item>
            <el-menu-item index="/resource-view">
              <el-icon><Grid /></el-icon>
              <span>资源视图</span>
            </el-menu-item>
            <el-menu-item index="/dashboard">
              <el-icon><TrendCharts /></el-icon>
              <span>KPI仪表板</span>
            </el-menu-item>
            <el-sub-menu index="master-data">
              <template #title>
                <el-icon><Setting /></el-icon>
                <span>主数据管理</span>
              </template>
              <el-menu-item index="/master-data/work-centers">工作中心</el-menu-item>
              <el-menu-item index="/master-data/resources">资源</el-menu-item>
              <el-menu-item index="/master-data/products">产品</el-menu-item>
              <el-menu-item index="/master-data/routings">工艺路线</el-menu-item>
              <el-menu-item index="/master-data/setup-matrix">切换矩阵</el-menu-item>
            </el-sub-menu>
            <el-menu-item index="/orders">
              <el-icon><Document /></el-icon>
              <span>订单数据</span>
            </el-menu-item>
            <el-sub-menu index="detailed-scheduling">
              <template #title>
                <el-icon><Operation /></el-icon>
                <span>详细排程</span>
              </template>
              <el-menu-item index="/ds">详细计划表</el-menu-item>
              <el-menu-item index="/ds-resource">DS资源</el-menu-item>
              <el-menu-item index="/ds-product">DS产品</el-menu-item>
              <el-menu-item index="/ds-routing">DS工艺路线</el-menu-item>
              <el-menu-item index="/ds-setup-matrix">DS切换矩阵</el-menu-item>
              <el-menu-item index="/ds-orders">DS订单数据</el-menu-item>
            </el-sub-menu>
          </el-menu>
          
          <!-- 用户信息区域 -->
          <div class="user-section">
            <el-dropdown trigger="click" @command="handleUserCommand">
              <div class="user-info">
                <el-avatar :size="36" class="user-avatar">
                  {{ userInitial }}
                </el-avatar>
                <div class="user-details">
                  <span class="user-name">{{ userName }}</span>
                  <span class="user-role">{{ userRole }}</span>
                </div>
                <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon>
                    个人信息
                  </el-dropdown-item>
                  <el-dropdown-item command="password">
                    <el-icon><Lock /></el-icon>
                    修改密码
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-aside>
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </div>
    
    <!-- 修改密码对话框 -->
    <el-dialog v-model="passwordDialogVisible" title="修改密码" width="400px">
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="80px">
        <el-form-item label="原密码" prop="oldPassword">
          <el-input v-model="passwordForm.oldPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleChangePassword" :loading="changingPassword">确定</el-button>
      </template>
    </el-dialog>
  </el-config-provider>
</template>

<script setup>
import { computed, ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, User, Lock, SwitchButton } from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { authApi } from '@/api'

const route = useRoute()
const router = useRouter()

const activeMenu = computed(() => route.path)
const isLoginPage = computed(() => route.path === '/login')

// 用户信息
const currentUser = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}')
  } catch {
    return {}
  }
})

const userName = computed(() => currentUser.value.full_name || currentUser.value.username || '用户')
const userInitial = computed(() => (userName.value || 'U')[0].toUpperCase())
const userRole = computed(() => currentUser.value.is_admin ? '管理员' : '普通用户')

// 修改密码
const passwordDialogVisible = ref(false)
const passwordFormRef = ref(null)
const changingPassword = ref(false)
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const handleUserCommand = (command) => {
  switch (command) {
    case 'profile':
      ElMessage.info('个人信息功能开发中')
      break
    case 'password':
      passwordForm.oldPassword = ''
      passwordForm.newPassword = ''
      passwordForm.confirmPassword = ''
      passwordDialogVisible.value = true
      break
    case 'logout':
      handleLogout()
      break
  }
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    changingPassword.value = true
    try {
      await authApi.changePassword(passwordForm.oldPassword, passwordForm.newPassword)
      ElMessage.success('密码修改成功')
      passwordDialogVisible.value = false
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '密码修改失败')
    } finally {
      changingPassword.value = false
    }
  })
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      type: 'warning'
    })
    
    try {
      await authApi.logout()
    } catch (e) {
      // 忽略登出API错误
    }
    
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    
    ElMessage.success('已退出登录')
    router.push('/login')
  } catch {
    // 用户取消
  }
}
</script>

<style lang="scss">
// Material 3 Design Tokens
$m3-primary: #1a73e8;
$m3-primary-container: #d3e3fd;
$m3-on-primary-container: #041e49;
$m3-surface: #ffffff;
$m3-surface-dim: #f8fafd;
$m3-surface-container: #eceef1;
$m3-surface-container-low: #f1f3f4;
$m3-surface-container-high: #e3e5e8;
$m3-on-surface: #1f1f1f;
$m3-on-surface-variant: #444746;
$m3-outline-variant: #c4c7c5;

$m3-shape-lg: 16px;
$m3-shape-xl: 28px;
$m3-shape-full: 9999px;

.app-container {
  min-height: 100vh;
  background: $m3-surface-dim;
}

.main-container {
  min-height: 100vh;
}

.sidebar {
  background: $m3-surface;
  border-right: none;
  box-shadow: none;
  
  .logo {
    height: 72px;
    display: flex;
    align-items: center;
    padding: 0 24px;
    gap: 12px;
    font-size: 18px;
    font-weight: 500;
    color: $m3-on-surface;
    letter-spacing: 0;
    
    .logo-icon {
      width: 40px;
      height: 40px;
      background: $m3-primary-container;
      border-radius: $m3-shape-lg;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .el-icon {
        color: $m3-on-primary-container;
      }
      
      &.we-logo {
        background: #0099cc;
        border-radius: 10px;
        
        span {
          font-family: 'Arial', sans-serif;
          font-size: 20px;
          font-weight: 700;
          color: #fff;
          letter-spacing: -1px;
        }
      }
    }
  }
  
  .sidebar-menu {
    border-right: none;
    padding: 8px 12px;
    background: transparent;
    
    .el-menu-item {
      height: 56px;
      line-height: 56px;
      margin: 2px 0;
      border-radius: $m3-shape-full;
      padding: 0 24px !important;
      color: $m3-on-surface-variant;
      font-weight: 500;
      font-size: 14px;
      transition: all 0.2s ease;
      
      .el-icon {
        margin-right: 12px;
        font-size: 24px;
      }
      
      &:hover {
        background: $m3-surface-container-low !important;
        color: $m3-on-surface;
      }
      
      &.is-active {
        background: $m3-primary-container !important;
        color: $m3-on-primary-container;
        
        .el-icon {
          color: $m3-on-primary-container;
        }
      }
    }
    
    .el-sub-menu {
      .el-sub-menu__title {
        height: 56px;
        line-height: 56px;
        margin: 2px 0;
        border-radius: $m3-shape-full;
        padding: 0 24px !important;
        color: $m3-on-surface-variant;
        font-weight: 500;
        font-size: 14px;
        
        .el-icon {
          margin-right: 12px;
          font-size: 24px;
        }
        
        &:hover {
          background: $m3-surface-container-low !important;
        }
        
        .el-sub-menu__icon-arrow {
          right: 20px;
        }
      }
      
      .el-menu-item {
        padding-left: 72px !important;
        height: 48px;
        line-height: 48px;
        font-size: 14px;
        margin: 0;
        border-radius: 0 $m3-shape-full $m3-shape-full 0;
        margin-left: 12px;
        
        &.is-active {
          background: $m3-primary-container !important;
          color: $m3-on-primary-container;
        }
      }
    }
  }
}

.main-content {
  background: $m3-surface-dim;
  padding: 24px 32px;
  overflow-y: auto;
}

.sidebar {
  display: flex;
  flex-direction: column;
  
  .sidebar-menu {
    flex: 1;
    overflow-y: auto;
  }
}

.user-section {
  padding: 16px;
  border-top: 1px solid $m3-outline-variant;
  
  .user-info {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    border-radius: 12px;
    cursor: pointer;
    transition: background 0.2s;
    
    &:hover {
      background: $m3-surface-container-low;
    }
  }
  
  .user-avatar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    font-weight: 600;
  }
  
  .user-details {
    flex: 1;
    min-width: 0;
    
    .user-name {
      display: block;
      font-weight: 500;
      font-size: 14px;
      color: $m3-on-surface;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    
    .user-role {
      display: block;
      font-size: 12px;
      color: $m3-on-surface-variant;
    }
  }
  
  .dropdown-icon {
    color: $m3-on-surface-variant;
  }
}
</style>
