<template>
  <div class="mx-auto max-w-xl px-4 py-8">
    <div class="mb-6 border-b border-slate-200 pb-5">
      <p class="meta mb-1">{{ t('account') }}</p>
      <h1 class="text-2xl font-semibold text-slate-950">{{ t('accountTitle') }}</h1>
    </div>

    <form @submit.prevent="saveProfile" class="panel bg-white p-5 space-y-4">
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">{{ t('username') }}</label>
        <input :value="auth.user?.username || ''" disabled class="input" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">{{ t('displayName') }}</label>
        <input v-model.trim="profile.display_name" class="input" :placeholder="t('displayNamePlaceholder')" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">{{ t('departmentOptional') }}</label>
        <input v-model.trim="profile.department" class="input" :placeholder="t('departmentPlaceholder')" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">{{ t('schoolOptional') }}</label>
        <input v-model.trim="profile.school_input" class="input" list="account-school-options" :placeholder="t('schoolPlaceholder')" />
        <datalist id="account-school-options">
          <option v-for="school in schools" :key="school.id" :value="schoolName(school)" />
        </datalist>
        <p class="mt-1 text-xs text-slate-500">{{ t('schoolDefaultHint') }}</p>
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">{{ t('email') }}</label>
        <input v-model.trim="profile.email" type="email" class="input" :placeholder="t('optional')" />
      </div>

      <p v-if="profileMessage" class="text-sm text-teal-700">{{ profileMessage }}</p>
      <p v-if="profileError" class="text-sm text-red-600">{{ profileError }}</p>

      <button type="submit" :disabled="savingProfile" class="btn-primary">
        {{ savingProfile ? t('savingProfile') : t('saveProfile') }}
      </button>
    </form>

    <form @submit.prevent="changePassword" class="panel mt-6 bg-white p-5 space-y-4">
      <h2 class="font-semibold text-slate-950">{{ t('changePassword') }}</h2>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">{{ t('currentPassword') }}</label>
        <input v-model="password.current_password" type="password" required class="input" />
      </div>
      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">{{ t('newPassword') }}</label>
        <input v-model="password.new_password" type="password" required minlength="6" class="input" />
      </div>

      <p v-if="passwordMessage" class="text-sm text-teal-700">{{ passwordMessage }}</p>
      <p v-if="passwordError" class="text-sm text-red-600">{{ passwordError }}</p>

      <button type="submit" :disabled="savingPassword" class="btn-primary">
        {{ savingPassword ? t('updatingPassword') : t('updatePassword') }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from '@/i18n'

const auth = useAuthStore()
const { t, currentLocale } = useI18n()

const profile = ref({ display_name: '', department: '', school_input: '', email: '' })
const password = ref({ current_password: '', new_password: '' })
const schools = ref<any[]>([])
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
    school_input: auth.user?.school_name_custom || (auth.user?.school ? schoolName(auth.user.school) : ''),
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
      department: profile.value.department || null,
      school_input: profile.value.school_input || null,
      email: profile.value.email || null
    })
    await auth.fetchMe()
    hydrateProfile()
    profileMessage.value = t('profileSaved')
  } catch (e: any) {
    profileError.value = e.response?.data?.detail || t('profileSaveFailed')
  } finally {
    savingProfile.value = false
  }
}

function schoolName(school: any) {
  if (currentLocale.value === 'en') return school.name_en || school.name_zh
  if (currentLocale.value === 'ja') return school.name_ja || school.name_zh
  return school.name_zh || school.name_en
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
    passwordMessage.value = t('passwordUpdated')
  } catch (e: any) {
    passwordError.value = e.response?.data?.detail || t('passwordUpdateFailed')
  } finally {
    savingPassword.value = false
  }
}

onMounted(async () => {
  if (!auth.user) await auth.fetchMe()
  const { data } = await api.get('/schools')
  schools.value = data
  hydrateProfile()
})
</script>
