import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('@/views/HomeView.vue') },
    { path: '/schools/:schoolSlug', component: () => import('@/views/HomeView.vue'), meta: { requiresAuth: true } },
    { path: '/schools/:schoolSlug/boards/:boardSlug', component: () => import('@/views/HomeView.vue'), meta: { requiresAuth: true } },
    { path: '/post/:id', component: () => import('@/views/PostView.vue'), meta: { requiresAuth: true } },
    { path: '/login', component: () => import('@/views/LoginView.vue') },
    { path: '/register', component: () => import('@/views/RegisterView.vue') },
    {
      path: '/account',
      component: () => import('@/views/AccountView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/admin',
      component: () => import('@/views/admin/AdminView.vue'),
      meta: { requiresAdmin: true }
    }
  ]
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.user) await auth.fetchMe()

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { path: '/login', query: { next: to.fullPath } }
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    if (!auth.isLoggedIn) return { path: '/login', query: { next: to.fullPath } }
    return { path: '/' }
  }
})

export default router
