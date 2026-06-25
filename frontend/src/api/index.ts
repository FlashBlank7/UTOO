import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const api = axios.create({ baseURL: '/api/v1' })

api.interceptors.request.use(async (config) => {
  const auth = useAuthStore()
  await auth.ensureFreshAccess()
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        const auth = useAuthStore()
        const refreshed = await auth.ensureFreshAccess(true)
        if (refreshed) {
          const token = localStorage.getItem('access_token')
          original.headers.Authorization = `Bearer ${token}`
          return api(original)
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api
