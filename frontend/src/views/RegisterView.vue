<template>
  <div class="max-w-md mx-auto mt-16 px-4">
    <h1 class="text-2xl font-bold text-center mb-8">注册 UTOO</h1>
    <form @submit.prevent="submit" class="bg-white rounded-lg shadow p-6 space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">激活码 <span class="text-red-500">*</span></label>
        <input v-model="form.activation_code" required class="input" placeholder="8位激活码" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">专攻 / 研究科 <span class="text-red-500">*</span></label>
        <input v-model="form.department" required class="input" placeholder="例：情報理工学系研究科" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">密码 <span class="text-red-500">*</span></label>
        <input v-model="form.password" type="password" required class="input" placeholder="至少6位" minlength="6" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">昵称（可选）</label>
        <input v-model="form.username" class="input" placeholder="留空则全程匿名" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">邮箱（可选）</label>
        <input v-model="form.email" type="email" class="input" placeholder="可选" />
      </div>

      <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>

      <button type="submit" :disabled="loading" class="btn-primary w-full">
        {{ loading ? '注册中…' : '注册' }}
      </button>

      <p class="text-center text-sm text-gray-500">
        已有账号？<router-link to="/login" class="text-indigo-500 hover:underline">登录</router-link>
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

const form = ref({ activation_code: '', department: '', password: '', username: '', email: '' })
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const payload: Record<string, string> = {
      activation_code: form.value.activation_code,
      department: form.value.department,
      password: form.value.password,
    }
    if (form.value.username) payload.username = form.value.username
    if (form.value.email) payload.email = form.value.email

    const { data } = await api.post('/auth/register', payload)
    auth.setTokens(data.access_token, data.refresh_token)
    await auth.fetchMe()
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.detail || '注册失败，请检查激活码'
  } finally {
    loading.value = false
  }
}
</script>
