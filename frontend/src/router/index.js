import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    redirect: '/gantt'
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
    component: () => import('@/views/Orders.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/master-data/work-centers',
    name: 'WorkCenters',
    component: () => import('@/views/MasterData/WorkCenters.vue'),
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
  } else if (to.path === '/login' && token) {
    // 已登录但访问登录页，跳转到首页
    next('/gantt')
  } else {
    next()
  }
})

export default router
