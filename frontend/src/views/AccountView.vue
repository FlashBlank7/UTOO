<template>
  <div class="max-w-xl mx-auto px-4 py-8">
    <h1 class="text-xl font-bold text-gray-800 mb-6">我的信息</h1>

    <form @submit.prevent="saveProfile" class="bg-white rounded-lg border border-gray-100 p-6 space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
        <input :value="auth.user?.username || ''" disabled class="input bg-gray-50 text-gray-400" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">昵称</label>
        <input v-model.trim="profile.display_name" class="input" placeholder="公开展示名，可留空" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">专攻 / 研究科</label>
        <input v-model.trim="profile.department" required class="input" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
        <input v-model.trim="profile.email" type="email" class="input" placeholder="可选" />
      </div>

      <p v-if="profileMessage" class="text-green-600 text-sm">{{ profileMessage }}</p>
      <p v-if="profileError" class="text-red-500 text-sm">{{ profileError }}</p>

      <button type="submit" :disabled="savingProfile" class="btn-primary">
        {{ savingProfile ? '保存中…' : '保存资料' }}
      </button>
    </form>

    <form @submit.prevent="changePassword" class="bg-white rounded-lg border border-gray-100 p-6 space-y-4 mt-6">
      <h2 class="font-semibold text-gray-800">修改密码</h2>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">当前密码</label>
        <input v-model="password.current_password" type="password" required class="input" />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">新密码</label>
        <input v-model="password.new_password" type="password" required minlength="6" class="input" />
      </div>

      <p v-if="passwordMessage" class="text-green-600 text-sm">{{ passwordMessage }}</p>
      <p v-if="passwordError" class="text-red-500 text-sm">{{ passwordError }}</p>

      <button type="submit" :disabled="savingPassword" class="btn-primary">
        {{ savingPassword ? '更新中…' : '更新密码' }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const profile = ref({ display_name: '', department: '', email: '' })
const password = ref({ current_password: '', new_password: '' })
const savingProfile = ref(false)
const savingPassword = ref(false)
const profileMessage = ref('')
const profileError = ref('')
const passwordMessage = ref('')
const passwordError = ref('')

function hydrateProfile() {
  profile.value = {
    display_name: auth.user?.display_name || '',
    department: auth.user?.department || '',
    email: auth.user?.email || ''
  }
}

async function saveProfile() {
  profileMessage.value = ''
  profileError.value = ''
  savingProfile.value = true
  try {
    await api.patch('/auth/me', {
      display_name: profile.value.display_name || null,
      department: profile.value.department,
      email: profile.value.email || null
    })
    await auth.fetchMe()
    hydrateProfile()
    profileMessage.value = '资料已保存'
  } catch (e: any) {
    profileError.value = e.response?.data?.detail || '保存失败'
  } finally {
    savingProfile.value = false
  }
}

async function changePassword() {
  passwordMessage.value = ''
  passwordError.value = ''
  savingPassword.value = true
  try {
    await api.patch('/auth/me', {
      current_password: password.value.current_password,
      new_password: password.value.new_password
    })
    password.value = { current_password: '', new_password: '' }
    passwordMessage.value = '密码已更新'
  } catch (e: any) {
    passwordError.value = e.response?.data?.detail || '更新失败'
  } finally {
    savingPassword.value = false
  }
}

onMounted(async () => {
  if (!auth.user) await auth.fetchMe()
  hydrateProfile()
})
</script>
