<template>
  <div class="login-container">
    <div class="login-background">
      <div class="bg-shape shape-1"></div>
      <div class="bg-shape shape-2"></div>
      <div class="bg-shape shape-3"></div>
    </div>
    
    <div class="login-card">
      <div class="login-header">
        <div class="logo">
          <div class="logo-icon we-logo">
            <span class="we-text">We</span>
          </div>
          <h1>{{ t('login.title') }}</h1>
        </div>
        <p class="subtitle">{{ t('login.subtitle') }}</p>
      </div>
      
      <el-form 
        ref="loginFormRef" 
        :model="loginForm" 
        :rules="loginRulesRef" 
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            :placeholder="t('login.username')"
            size="large"
            :prefix-icon="User"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            :placeholder="t('login.password')"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="rememberMe">{{ t('login.rememberMe') }}</el-checkbox>
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            size="large" 
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            {{ loading ? t('login.loggingIn') : t('login.login') }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>{{ t('login.defaultAccount') }}</p>
      </div>
    </div>
    
    <div class="copyright">
      © 2026 AI Native APS - {{ t('login.advancedPlanningSystem') }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { authApi } from '@/api'
import { useI18nStore } from '@/stores/i18n'

const router = useRouter()
const i18nStore = useI18nStore()
const t = (key) => i18nStore.t(key)
const loginFormRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRulesRef = computed(() => ({
  username: [
    { required: true, message: i18nStore.t('login.enterUsername'), trigger: 'blur' }
  ],
  password: [
    { required: true, message: i18nStore.t('login.enterPassword'), trigger: 'blur' }
  ]
}))

onMounted(() => {
  // 检查是否有记住的用户名
  const savedUsername = localStorage.getItem('rememberedUsername')
  if (savedUsername) {
    loginForm.username = savedUsername
    rememberMe.value = true
  }
  
  // 如果已登录，跳转到首页
  const token = localStorage.getItem('token')
  if (token) {
    router.push('/dashboard')
  }
})

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      const response = await authApi.login(loginForm.username, loginForm.password)
      
      // 保存 token 和用户信息
      localStorage.setItem('token', response.access_token)
      localStorage.setItem('user', JSON.stringify(response.user))
      
      // 记住用户名
      if (rememberMe.value) {
        localStorage.setItem('rememberedUsername', loginForm.username)
      } else {
        localStorage.removeItem('rememberedUsername')
      }
      
      const name = response.user.full_name || response.user.username
      ElMessage.success(i18nStore.t('login.welcomeBackMessage').replace('{name}', name))
      
      // 跳转到首页
      router.push('/dashboard')
    } catch (error) {
      const message = error.response?.data?.detail || i18nStore.t('login.loginFailed')
      ElMessage.error(message)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped lang="scss">
.login-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow: hidden;
}

.login-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  
  .bg-shape {
    position: absolute;
    border-radius: 50%;
    opacity: 0.1;
    background: #fff;
  }
  
  .shape-1 {
    width: 600px;
    height: 600px;
    top: -200px;
    left: -100px;
    animation: float 20s ease-in-out infinite;
  }
  
  .shape-2 {
    width: 400px;
    height: 400px;
    bottom: -100px;
    right: -50px;
    animation: float 15s ease-in-out infinite reverse;
  }
  
  .shape-3 {
    width: 200px;
    height: 200px;
    top: 50%;
    right: 20%;
    animation: float 10s ease-in-out infinite;
  }
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-30px) rotate(5deg);
  }
}

.login-card {
  background: #fff;
  border-radius: 24px;
  padding: 48px;
  width: 420px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
  
  .logo {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    margin-bottom: 12px;
    
    .logo-icon {
      width: 56px;
      height: 56px;
      background: #0099cc;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      &.we-logo {
        .we-text {
          font-family: 'Arial', sans-serif;
          font-size: 26px;
          font-weight: 700;
          color: #fff;
          letter-spacing: -1px;
        }
      }
    }
    
    h1 {
      font-size: 28px;
      font-weight: 700;
      background: linear-gradient(135deg, #0099cc 0%, #667eea 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      margin: 0;
    }
  }
  
  .subtitle {
    color: #6b7280;
    font-size: 16px;
    margin: 0;
  }
}

.login-form {
  :deep(.el-input__wrapper) {
    border-radius: 12px;
    padding: 4px 16px;
    box-shadow: 0 0 0 1px #e5e7eb;
    
    &:hover {
      box-shadow: 0 0 0 1px #667eea;
    }
    
    &.is-focus {
      box-shadow: 0 0 0 2px #667eea;
    }
  }
  
  :deep(.el-input__inner) {
    height: 44px;
  }
  
  :deep(.el-form-item) {
    margin-bottom: 24px;
  }
  
  :deep(.el-checkbox__label) {
    color: #6b7280;
  }
}

.login-button {
  width: 100%;
  height: 52px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px -10px rgba(102, 126, 234, 0.5);
  }
  
  &:active {
    transform: translateY(0);
  }
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #f3f4f6;
  
  p {
    color: #9ca3af;
    font-size: 13px;
    margin: 0;
  }
}

.copyright {
  position: absolute;
  bottom: 24px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
}
</style>
