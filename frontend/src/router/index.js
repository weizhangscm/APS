import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { messages, defaultLocale } from '@/i18n'

function t(key) {
  const loc = localStorage.getItem('locale') || defaultLocale
  const pack = messages[loc] || messages[defaultLocale]
  const keys = key.split('.')
  let v = pack
  for (const k of keys) {
    v = v?.[k]
  }
  return v || key
}

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/gantt',
    name: 'Gantt',
    component: () => import('@/views/GanttView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/resource-view',
    name: 'ResourceView',
    component: () => import('@/views/ResourceView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/orders',
    name: 'Orders',
    component: () => import('@/views/DSOrdersView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/master-data/work-centers',
    name: 'WorkCenters',
    component: () => import('@/views/MasterData/WorkCenters.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/master-data/locations',
    name: 'Locations',
    component: () => import('@/views/MasterData/Locations.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/master-data/shifts',
    name: 'Shifts',
    component: () => import('@/views/ShiftsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/master-data/resources',
    name: 'Resources',
    component: () => import('@/views/MasterData/Resources.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/master-data/products',
    name: 'Products',
    component: () => import('@/views/MasterData/Products.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/master-data/routings',
    name: 'Routings',
    component: () => import('@/views/MasterData/Routings.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/master-data/setup-matrix',
    name: 'SetupMatrix',
    component: () => import('@/views/MasterData/SetupMatrix.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ds',
    name: 'DS',
    component: () => import('@/views/DSView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ds-scheduling',
    name: 'DSScheduling',
    component: () => import('@/views/DSSchedulingView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ds-resource',
    name: 'DSResource',
    component: () => import('@/views/DSResourceView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ds-product',
    name: 'DSProduct',
    component: () => import('@/views/DSProductView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ds-routing',
    name: 'DSRouting',
    component: () => import('@/views/DSRoutingView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ds-setup-matrix',
    name: 'DSSetupMatrix',
    component: () => import('@/views/DSSetupMatrixView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ds-orders',
    name: 'DSOrders',
    component: () => import('@/views/DSOrdersView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/data-management',
    name: 'DataManagement',
    component: () => import('@/views/DataManagement.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 检查登录状态
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const requiresAuth = to.meta.requiresAuth !== false
  
  if (requiresAuth && !token) {
    // 需要登录但未登录，跳转到登录页
    next('/login')
  } else if (to.meta.requiresAdmin && token) {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      if (!user.is_admin) {
        ElMessage.warning(t('user.clearDataAdminOnly'))
        next('/dashboard')
        return
      }
    } catch {
      next('/dashboard')
      return
    }
    next()
  } else if (to.path === '/login' && token) {
    // 已登录但访问登录页，跳转到首页
    next('/dashboard')
  } else {
    next()
  }
})

export default router
