<template>
  <div class="mx-auto max-w-md px-4 py-16">
    <div class="mb-8 border-b border-slate-200 pb-5">
      <p class="meta mb-1">{{ t('account') }}</p>
      <h1 class="text-2xl font-semibold text-slate-950">{{ t('registerTitle') }}</h1>
    </div>
    <form @submit.prevent="submit" class="panel bg-white p-5 space-y-4">
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">{{ t('activationCode') }} <span class="text-red-600">*</span></label>
        <input v-model.trim="form.activation_code" required class="input" :placeholder="t('activationPlaceholder')" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">{{ t('username') }} <span class="text-red-600">*</span></label>
        <input v-model.trim="form.username" required class="input" :placeholder="t('usernamePlaceholder')" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">{{ t('department') }} <span class="text-red-600">*</span></label>
        <input v-model.trim="form.department" required class="input" :placeholder="t('departmentPlaceholder')" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">{{ t('password') }} <span class="text-red-600">*</span></label>
        <input v-model="form.password" type="password" required class="input" :placeholder="t('passwordPlaceholder')" minlength="6" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">{{ t('displayNameOptional') }}</label>
        <input v-model.trim="form.display_name" class="input" :placeholder="t('displayNamePlaceholder')" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">{{ t('emailOptional') }}</label>
        <input v-model="form.email" type="email" class="input" :placeholder="t('optional')" />
      </div>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <button type="submit" :disabled="loading" class="btn-primary w-full">
        {{ loading ? t('registering') : t('register') }}
      </button>

      <p class="text-center text-sm text-slate-500">
        {{ t('hasAccount') }} <router-link :to="{ path: '/login', query: nextQuery }" class="link">{{ t('login') }}</router-link>
      </p>
    </form>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from '@/i18n'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const { t } = useI18n()

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
  if (detail === 'Invalid or inactive activation code') return t('invalidActivation')
  if (detail === 'Activation code has reached its usage limit') return t('activationLimit')
  if (detail === 'Username already taken') return t('usernameTaken')
  if (detail === 'Email already registered') return t('emailTaken')
  if (detail === 'Username is required') return t('usernameRequired')
  if (detail === 'Department is required') return t('departmentRequired')
  if (typeof detail === 'string') return detail
  if (e.request && !e.response) return t('networkError')
  return t('registerFailed')
}
</script>
