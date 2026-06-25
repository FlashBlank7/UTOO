<template>
  <div class="mx-auto max-w-md px-4 py-16">
    <div class="mb-8 border-b border-slate-200 pb-5">
      <p class="meta mb-1">Account</p>
      <h1 class="text-2xl font-semibold text-slate-950">注册 UTOO</h1>
    </div>
    <form @submit.prevent="submit" class="panel bg-white p-5 space-y-4">
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">激活码 <span class="text-red-600">*</span></label>
        <input v-model.trim="form.activation_code" required class="input" placeholder="8位激活码" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">用户名 <span class="text-red-600">*</span></label>
        <input v-model.trim="form.username" required class="input" placeholder="用于登录，不会公开显示" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">专攻 / 研究科 <span class="text-red-600">*</span></label>
        <input v-model.trim="form.department" required class="input" placeholder="例：情報理工学系研究科" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">密码 <span class="text-red-600">*</span></label>
        <input v-model="form.password" type="password" required class="input" placeholder="至少6位" minlength="6" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">昵称（可选）</label>
        <input v-model.trim="form.display_name" class="input" placeholder="公开展示名，留空则显示用户编号" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">邮箱（可选）</label>
        <input v-model="form.email" type="email" class="input" placeholder="可选" />
      </div>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <button type="submit" :disabled="loading" class="btn-primary w-full">
        {{ loading ? '注册中...' : '注册' }}
      </button>

      <p class="text-center text-sm text-slate-500">
        已有账号？<router-link :to="{ path: '/login', query: nextQuery }" class="link">登录</router-link>
      </p>
    </form>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = ref({ activation_code: '', department: '', password: '', username: '', display_name: '', email: '' })
const error = ref('')
const loading = ref(false)
const nextQuery = computed(() => {
  const next = typeof route.query.next === 'string' ? route.query.next : ''
  return next ? { next } : {}
})

function nextPath() {
  const next = typeof route.query.next === 'string' ? route.query.next : ''
  return next.startsWith('/') && !next.startsWith('//') ? next : '/'
}

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const payload: Record<string, string> = {
      activation_code: form.value.activation_code,
      department: form.value.department,
      password: form.value.password,
      username: form.value.username,
    }
    if (form.value.display_name) payload.display_name = form.value.display_name
    if (form.value.email) payload.email = form.value.email

    const { data } = await api.post('/auth/register', payload)
    auth.setTokens(data.access_token, data.refresh_token)
    await auth.fetchMe()
    router.replace(nextPath())
  } catch (e: any) {
    error.value = registerErrorMessage(e)
  } finally {
    loading.value = false
  }
}

function registerErrorMessage(e: any) {
  const detail = e.response?.data?.detail
  if (detail === 'Invalid or inactive activation code') return '激活码无效或已停用'
  if (detail === 'Activation code has reached its usage limit') return '激活码使用次数已满'
  if (detail === 'Username already taken') return '用户名已被占用'
  if (detail === 'Email already registered') return '邮箱已注册'
  if (detail === 'Username is required') return '请填写用户名'
  if (detail === 'Department is required') return '请填写专攻 / 研究科'
  if (typeof detail === 'string') return detail
  if (e.request && !e.response) return '网络连接失败，请稍后再试'
  return '注册失败，请检查信息后重试'
}
</script>
