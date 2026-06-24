import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

interface User {
  id: number
  username: string | null
  display_name: string | null
  department: string
  email: string | null
  is_admin: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.is_admin ?? false)
  const displayName = computed(() => user.value?.display_name || (user.value ? `用户${user.value.id}` : ''))

  async function fetchMe() {
    const token = localStorage.getItem('access_token')
    if (!token) return
    try {
      const { data } = await axios.get('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
      user.value = data
    } catch {
      logout()
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

  return { user, isLoggedIn, isAdmin, displayName, fetchMe, setTokens, logout }
})
