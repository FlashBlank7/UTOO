<template>
  <div class="max-w-md mx-auto mt-16 px-4">
    <h1 class="text-2xl font-bold text-center mb-8">登录 UTOO</h1>
    <form @submit.prevent="submit" class="bg-white rounded-lg shadow p-6 space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">用户名或邮箱</label>
        <input v-model.trim="identifier" required class="input" placeholder="用户名 或 邮箱" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
        <input v-model="password" type="password" required class="input" />
      </div>

      <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>

      <button type="submit" :disabled="loading" class="btn-primary w-full">
        {{ loading ? '登录中…' : '登录' }}
      </button>

      <p class="text-center text-sm text-gray-500">
        没有账号？<router-link to="/register" class="text-indigo-500 hover:underline">注册</router-link>
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
