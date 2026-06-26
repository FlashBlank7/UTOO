<template>
  <div class="mx-auto max-w-md px-4 py-16">
    <div class="mb-8 border-b border-slate-200 pb-5">
      <p class="meta mb-1">{{ t('account') }}</p>
      <h1 class="text-2xl font-semibold text-slate-950">{{ t('loginTitle') }}</h1>
    </div>
    <form @submit.prevent="submit" class="panel bg-white p-5 space-y-4">
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">{{ t('usernameOrEmail') }}</label>
        <input v-model.trim="identifier" required class="input" :placeholder="t('loginIdentifierPlaceholder')" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">{{ t('password') }}</label>
        <input v-model="password" type="password" required class="input" />
      </div>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <button type="submit" :disabled="loading" class="btn-primary w-full">
        {{ loading ? t('loggingIn') : t('login') }}
      </button>

      <p class="text-center text-sm text-slate-500">
        {{ t('noAccount') }} <router-link :to="{ path: '/register', query: nextQuery }" class="link">{{ t('register') }}</router-link>
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
const identifier = ref('')
const password = ref('')
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
    const isEmail = identifier.value.includes('@')
    const payload = isEmail
      ? { email: identifier.value, password: password.value }
      : { username: identifier.value, password: password.value }

    const { data } = await api.post('/auth/login', payload)
    auth.setTokens(data.access_token, data.refresh_token)
    await auth.fetchMe()
    router.replace(nextPath())
  } catch {
    error.value = t('loginFailed')
  } finally {
    loading.value = false
  }
}
</script>
