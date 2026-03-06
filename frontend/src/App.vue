<template>
  <el-config-provider :locale="elementLocale">
    <!-- 登录页面 -->
    <router-view v-if="isLoginPage" />
    
    <!-- 主应用布局 -->
    <div v-else class="app-container">
      <ChatBot />
      <el-container class="main-container">
        <el-aside width="280px" class="sidebar">
          <div class="logo">
            <div class="logo-icon we-logo">
              <span>We</span>
            </div>
            <span>{{ t('app.title') }}</span>
          </div>
          <el-menu
            :default-active="activeMenu"
            class="sidebar-menu"
            router
          >
            <el-menu-item index="/ds">
              <el-icon><Operation /></el-icon>
              <span>{{ t('menu.detailedSchedule') }}</span>
            </el-menu-item>
            <el-menu-item index="/dashboard">
              <el-icon><TrendCharts /></el-icon>
              <span>{{ t('menu.kpiDashboard') }}</span>
            </el-menu-item>
            <el-sub-menu index="master-data">
              <template #title>
                <el-icon><Setting /></el-icon>
                <span>{{ t('menu.masterDataManagement') }}</span>
              </template>
              <el-menu-item index="/ds-resource">{{ t('menu.resources') }}</el-menu-item>
              <el-menu-item index="/master-data/shifts">{{ t('menu.shifts') }}</el-menu-item>
              <el-menu-item index="/ds-product">{{ t('menu.products') }}</el-menu-item>
              <el-menu-item index="/ds-routing">{{ t('menu.routing') }}</el-menu-item>
              <el-menu-item index="/ds-setup-matrix">{{ t('menu.setupMatrix') }}</el-menu-item>
            </el-sub-menu>
            <el-sub-menu index="business-data">
              <template #title>
                <el-icon><Briefcase /></el-icon>
                <span>{{ t('menu.businessDataManagement') }}</span>
              </template>
              <el-menu-item index="/orders">{{ t('menu.productionOrders') }}</el-menu-item>
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
                    {{ t('user.profile') }}
                  </el-dropdown-item>
                  <el-dropdown-item command="password">
                    <el-icon><Lock /></el-icon>
                    {{ t('user.changePassword') }}
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon><SwitchButton /></el-icon>
                    {{ t('user.logout') }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-aside>
        <el-main class="main-content">
          <div class="main-content-top-bar">
            <span></span>
            <LanguageSwitcher />
          </div>
          <router-view />
        </el-main>
      </el-container>
    </div>
    
    <!-- 修改密码对话框 -->
    <el-dialog v-model="passwordDialogVisible" :title="t('password.title')" width="400px">
      <el-form :model="passwordForm" :rules="passwordRulesRef" ref="passwordFormRef" label-width="80px">
        <el-form-item :label="t('password.oldPassword')" prop="oldPassword">
          <el-input v-model="passwordForm.oldPassword" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('password.newPassword')" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('password.confirmPassword')" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleChangePassword" :loading="changingPassword">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </el-config-provider>
</template>

<script setup>
import { computed, ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown, User, Lock, SwitchButton, Briefcase } from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
import { authApi } from '@/api'
import { useI18nStore } from '@/stores/i18n'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import ChatBot from '@/components/ChatBot.vue'

const route = useRoute()
const router = useRouter()
const i18nStore = useI18nStore()
const t = (key) => i18nStore.t(key)

const activeMenu = computed(() => route.path)
const isLoginPage = computed(() => route.path === '/login')

const elementLocale = computed(() => i18nStore.currentLocale === 'zh-CN' ? zhCn : en)

// 用户信息
const currentUser = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}')
  } catch {
    return {}
  }
})

const userName = computed(() => currentUser.value.full_name || currentUser.value.username || (i18nStore.currentLocale === 'zh-CN' ? '用户' : 'User'))
const userInitial = computed(() => (userName.value || 'U')[0].toUpperCase())
const userRole = computed(() => currentUser.value.is_admin ? i18nStore.t('user.admin') : i18nStore.t('user.regularUser'))

// 修改密码
const passwordDialogVisible = ref(false)
const passwordFormRef = ref(null)
const changingPassword = ref(false)
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRulesRef = computed(() => ({
  oldPassword: [{ required: true, message: i18nStore.t('password.enterOldPassword'), trigger: 'blur' }],
  newPassword: [
    { required: true, message: i18nStore.t('password.enterNewPassword'), trigger: 'blur' },
    { min: 6, message: i18nStore.t('password.passwordTooShort'), trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: i18nStore.t('password.enterConfirmPassword'), trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error(i18nStore.t('password.passwordMismatch')))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}))

const handleUserCommand = (command) => {
  switch (command) {
    case 'profile':
      ElMessage.info(i18nStore.t('user.profileComingSoon'))
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
      ElMessage.success(i18nStore.t('password.changeSuccess'))
      passwordDialogVisible.value = false
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || i18nStore.t('password.changeFailed'))
    } finally {
      changingPassword.value = false
    }
  })
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(i18nStore.t('user.confirmLogout'), i18nStore.t('common.warning'), {
      type: 'warning'
    })
    
    try {
      await authApi.logout()
    } catch (e) {
      // 忽略登出API错误
    }
    
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    
    ElMessage.success(i18nStore.t('user.logoutSuccess'))
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

.main-content-top-bar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  margin: -24px -32px 0 0;
  padding: 8px 0 8px 16px;
  min-height: 40px;
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
