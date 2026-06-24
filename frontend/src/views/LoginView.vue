<template>
  <div class="mx-auto max-w-md px-4 py-16">
    <div class="mb-8 border-b border-slate-200 pb-5">
      <p class="meta mb-1">Account</p>
      <h1 class="text-2xl font-semibold text-slate-950">登录 UTOO</h1>
    </div>
    <form @submit.prevent="submit" class="panel bg-white p-5 space-y-4">
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">用户名或邮箱</label>
        <input v-model.trim="identifier" required class="input" placeholder="用户名 或 邮箱" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">密码</label>
        <input v-model="password" type="password" required class="input" />
      </div>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <button type="submit" :disabled="loading" class="btn-primary w-full">
        {{ loading ? '登录中...' : '登录' }}
      </button>

      <p class="text-center text-sm text-slate-500">
        没有账号？<router-link to="/register" class="link">注册</router-link>
      </p>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const identifier = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const isEmail = identifier.value.includes('@')
    const payload = isEmail
      ? { email: identifier.value, password: password.value }
      : { username: identifier.value, password: password.value }

    const { data } = await api.post('/auth/login', payload)
    auth.setTokens(data.access_token, data.refresh_token)
    await auth.fetchMe()
    router.push('/')
  } catch {
    error.value = '登录失败，请检查账号密码'
  } finally {
    loading.value = false
  }
}
</script>
