import { createRouter, createWebHistory } from 'vue-router'
import store from '@/store'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard'
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '数据概览' }
      },
      {
        path: 'sales',
        name: 'Sales',
        component: () => import('@/views/Sales/SalesManagement.vue'),
        meta: { title: '销售数据管理' }
      },
      {
        path: 'visualization',
        name: 'Visualization',
        component: () => import('@/views/Visualization/DataVisualization.vue'),
        meta: { title: '数据可视化' }
      },
      {
        path: 'prediction',
        name: 'Prediction',
        component: () => import('@/views/Prediction/SalesPrediction.vue'),
        meta: { title: '销量预测' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users/UserManagement.vue'),
        meta: { title: '用户管理', requiresAdmin: true }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const isAuthenticated = store.getters.isAuthenticated
  const userRole = store.getters.userRole

  if (to.meta.requiresAuth === false) {
    if (isAuthenticated && to.name === 'Login') {
      return next('/dashboard')
    }
    return next()
  }

  if (!isAuthenticated) {
    return next('/login')
  }

  if (to.meta.requiresAdmin && userRole !== 'admin') {
    return next('/dashboard')
  }

  next()
})

export default router
