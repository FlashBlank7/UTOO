import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { useI18n } from '@/i18n'

interface User {
  id: number
  username: string | null
  display_name: string | null
  department: string | null
  school: {
    id: number
    slug: string
    name_zh: string
    name_en: string
    name_ja: string
    kind: string
    theme: string
  } | null
  school_name_custom: string | null
  email: string | null
  is_admin: boolean
}

let refreshPromise: Promise<boolean> | null = null

function parseJwtExp(token: string | null) {
  if (!token) return 0
  try {
    const payload = token.split('.')[1]
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(normalized.length + ((4 - normalized.length % 4) % 4), '=')
    const decoded = JSON.parse(window.atob(padded)) as { exp?: number }
    return typeof decoded.exp === 'number' ? decoded.exp * 1000 : 0
  } catch {
    return 0
  }
}

function tokenExpiresSoon(token: string | null, skewMs = 5 * 60 * 1000) {
  const exp = parseJwtExp(token)
  return !exp || exp - Date.now() <= skewMs
}

export const useAuthStore = defineStore('auth', () => {
  const { t } = useI18n()
  const user = ref<User | null>(null)
  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)
  const displayName = computed(() => user.value?.display_name || (user.value ? t('navAccountFallback', { id: user.value.id }) : ''))

  async function ensureFreshAccess(force = false) {
    const access = localStorage.getItem('access_token')
    const refresh = localStorage.getItem('refresh_token')
    if (!refresh) return Boolean(access && !tokenExpiresSoon(access, 0))
    if (!force && access && !tokenExpiresSoon(access)) return true

    if (!refreshPromise) {
      refreshPromise = axios.post('/api/v1/auth/refresh', { refresh_token: refresh })
        .then(({ data }) => {
          setTokens(data.access_token, data.refresh_token)
          return true
        })
        .catch(() => {
          logout()
          return false
        })
        .finally(() => {
          refreshPromise = null
        })
    }
    return refreshPromise
  }

  async function fetchMe() {
    const hasSession = await ensureFreshAccess()
    if (!hasSession) return false
    const token = localStorage.getItem('access_token')
    if (!token) return false
    try {
      const { data } = await axios.get('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
      user.value = data
      return true
    } catch {
      const refreshed = await ensureFreshAccess(true)
      if (!refreshed) return false
      const freshToken = localStorage.getItem('access_token')
      if (!freshToken) return false
      try {
        const { data } = await axios.get('/api/v1/auth/me', {
          headers: { Authorization: `Bearer ${freshToken}` }
        })
        user.value = data
        return true
      } catch {
        logout()
        return false
      }
    }
  }

  function setTokens(access: string, refresh: string) {
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    user.value = null
  }

  return { user, isLoggedIn, isAdmin, displayName, ensureFreshAccess, fetchMe, setTokens, logout }
})
