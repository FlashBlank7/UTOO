<template>
  <div class="mx-auto max-w-7xl px-4 py-8">
    <div class="mb-5 flex flex-col gap-3 border-b border-slate-200 pb-4 md:flex-row md:items-end md:justify-between">
      <div>
        <p class="meta mb-1">{{ t('manageKicker') }}</p>
        <h1 class="text-2xl font-semibold text-slate-950">{{ t('manageTitle') }}</h1>
        <p class="mt-2 text-sm leading-6 text-slate-600">{{ t('manageIntro') }}</p>
      </div>
      <router-link v-if="auth.isAdmin" to="/admin" class="btn-primary">{{ t('openFullAdmin') }}</router-link>
    </div>

    <div v-if="loading" class="panel py-16 text-center text-sm text-slate-500">{{ t('loading') }}</div>

    <template v-else>
      <section v-if="scopes.length === 0" class="panel bg-white p-5">
        <h2 class="text-base font-semibold text-slate-950">{{ t('noManageScope') }}</h2>
        <p class="mt-2 text-sm leading-6 text-slate-600">{{ t('noManageScopeHint') }}</p>
      </section>

      <section v-else class="grid gap-5 lg:grid-cols-[280px_1fr]">
        <aside class="panel h-fit bg-white p-3">
          <p class="mb-2 text-sm font-semibold text-slate-950">{{ t('manageableSchools') }}</p>
          <button
            v-for="scope in scopes"
            :key="scope.school.id"
            @click="selectedSchoolId = scope.school.id"
            :class="[
              'mb-2 block w-full border px-3 py-2 text-left text-sm',
              selectedSchoolId === scope.school.id ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
            ]"
          >
            {{ schoolName(scope.school) }}
          </button>
        </aside>

        <main v-if="selectedScope" class="space-y-5">
          <section class="panel bg-white p-4">
            <div class="mb-3 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
              <div>
                <p class="meta">{{ t('currentManageScope') }}</p>
                <h2 class="text-xl font-semibold text-slate-950">{{ schoolName(selectedScope.school) }}</h2>
              </div>
              <button @click="openSchoolDescription" class="btn-secondary">{{ t('editDescription') }}</button>
            </div>
            <p class="text-sm leading-6 text-slate-600">{{ selectedScope.school.description || t('schoolIntro') }}</p>
          </section>

          <section class="panel bg-white p-4">
            <details>
              <summary class="cursor-pointer text-sm font-semibold text-slate-950">{{ t('createBoard') }}</summary>
              <form @submit.prevent="createBoard" class="mt-3 grid gap-2 md:grid-cols-[1fr_180px_auto]">
                <input v-model.trim="newBoard.name" required class="input" :placeholder="t('boardNamePlaceholder')" />
                <select v-model="newBoard.parent_id" class="select">
                  <option :value="null">{{ t('topLevelBoard') }}</option>
                  <option v-for="board in rootBoards" :key="board.id" :value="board.id">{{ board.name }}</option>
                </select>
                <button type="submit" :disabled="savingBoard" class="btn-primary">{{ savingBoard ? t('saving') : t('createBoard') }}</button>
                <textarea v-model.trim="newBoard.description" class="input h-20 resize-none md:col-span-3" :placeholder="t('boardDescriptionPlaceholder')"></textarea>
              </form>
            </details>
          </section>

          <section class="panel overflow-hidden bg-white">
            <div class="border-b border-slate-200 px-4 py-3">
              <h2 class="text-base font-semibold text-slate-950">{{ t('boardManagement') }}</h2>
            </div>
            <div class="divide-y divide-slate-200">
              <div v-for="board in flatBoards" :key="board.id" class="grid gap-3 px-4 py-3 md:grid-cols-[1fr_auto] md:items-center">
                <div>
                  <p class="font-medium text-slate-950">
                    <span v-if="board.parent_name" class="tag-accent mr-2">{{ t('subboard') }}</span>
                    {{ board.parent_name ? `${board.parent_name} / ${board.name}` : board.name }}
                  </p>
                  <p class="mt-1 text-sm text-slate-600">{{ board.description || '-' }}</p>
                  <span class="tag mt-2">{{ boardStatusLabel(board.status) }}</span>
                </div>
                <div class="flex flex-wrap gap-2">
                  <button @click="openBoardDescription(board)" class="btn-secondary">{{ t('editDescription') }}</button>
                  <button v-if="board.status !== 'approved'" @click="patchBoard(board, 'approved')" class="btn-secondary">{{ t('approve') }}</button>
                  <button v-if="board.status !== 'hidden'" @click="patchBoard(board, 'hidden')" class="btn-secondary">{{ t('archiveBoard') }}</button>
                </div>
              </div>
              <div v-if="flatBoards.length === 0" class="py-10 text-center text-sm text-slate-500">{{ t('noBoardRequests') }}</div>
            </div>
          </section>

          <section class="panel overflow-hidden bg-white">
            <div class="border-b border-slate-200 px-4 py-3">
              <h2 class="text-base font-semibold text-slate-950">{{ t('managedReports') }}</h2>
            </div>
            <div class="divide-y divide-slate-200">
              <div v-for="report in reports" :key="report.id" class="grid gap-3 px-4 py-3 md:grid-cols-[1fr_auto] md:items-center">
                <div>
                  <p class="font-medium text-slate-950">{{ report.target_type }} #{{ report.target_id }}</p>
                  <p class="mt-1 text-sm text-slate-600">{{ report.reason }} · {{ report.details || '-' }}</p>
                </div>
                <div class="flex flex-wrap gap-2">
                  <button @click="handleReport(report, 'resolve')" class="btn-secondary">{{ t('markResolved') }}</button>
                  <button @click="handleReport(report, 'hide')" class="btn-secondary">{{ t('hide') }}</button>
                  <button @click="handleReport(report, 'delete')" class="btn-secondary text-red-700">{{ t('delete') }}</button>
                </div>
              </div>
              <div v-if="reports.length === 0" class="py-10 text-center text-sm text-slate-500">{{ t('noReports') }}</div>
            </div>
          </section>
        </main>
      </section>

      <section class="panel mt-5 bg-white p-4">
        <h2 class="text-base font-semibold text-slate-950">{{ t('myModeratorApplications') }}</h2>
        <div class="mt-3 divide-y divide-slate-200 border border-slate-200">
          <div v-for="application in applications" :key="application.id" class="flex flex-wrap items-center gap-2 px-3 py-2 text-sm">
            <span class="font-medium text-slate-950">{{ schoolName(application.school) }}</span>
            <span class="text-slate-400">/</span>
            <span>{{ application.board.name }}</span>
            <span class="tag ml-auto">{{ boardStatusLabel(application.status) }}</span>
          </div>
          <div v-if="applications.length === 0" class="py-8 text-center text-sm text-slate-500">{{ t('noModeratorApplications') }}</div>
        </div>
      </section>
    </template>

    <div v-if="descriptionEditor" class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/50 px-4">
      <div class="panel w-full max-w-xl bg-white p-5">
        <div class="mb-4 flex items-center justify-between border-b border-slate-200 pb-3">
          <div>
            <h2 class="text-base font-semibold text-slate-950">{{ t('editDescription') }}</h2>
            <p class="meta mt-1">{{ descriptionEditor.title }}</p>
          </div>
          <button @click="descriptionEditor = null" class="text-sm text-slate-500 hover:text-slate-950">{{ t('close') }}</button>
        </div>
        <form @submit.prevent="saveDescription" class="space-y-3">
          <textarea v-model.trim="descriptionEditor.value" class="input h-36 resize-none" :placeholder="t('descriptionPlaceholder')"></textarea>
          <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
          <div class="flex justify-end gap-3">
            <button type="button" @click="descriptionEditor = null" class="btn-secondary">{{ t('cancel') }}</button>
            <button type="submit" :disabled="savingDescription" class="btn-primary">{{ savingDescription ? t('saving') : t('save') }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from '@/i18n'

const auth = useAuthStore()
const { t, currentLocale } = useI18n()
const loading = ref(true)
const scopes = ref<any[]>([])
const applications = ref<any[]>([])
const reports = ref<any[]>([])
const selectedSchoolId = ref<number | null>(null)
const newBoard = ref<{ name: string; description: string; parent_id: number | null }>({ name: '', description: '', parent_id: null })
const savingBoard = ref(false)
const savingDescription = ref(false)
const error = ref('')
const descriptionEditor = ref<null | { type: 'school' | 'board'; id: number; title: string; value: string }>(null)

const selectedScope = computed(() => scopes.value.find((scope) => scope.school.id === selectedSchoolId.value) || scopes.value[0] || null)
const rootBoards = computed(() => selectedScope.value?.boards || [])
const flatBoards = computed(() => {
  const roots = selectedScope.value?.boards || []
  return roots.flatMap((board: any) => [board, ...(board.children || []).map((child: any) => ({ ...child, parent_name: board.name }))])
})

function schoolName(school: any) {
  if (!school) return '-'
  if (currentLocale.value === 'en') return school.name_en || school.name_zh
  if (currentLocale.value === 'ja') return school.name_ja || school.name_zh
  return school.name_zh || school.name_en
}

function boardStatusLabel(status: string) {
  if (status === 'pending') return t('pending')
  if (status === 'approved') return t('approved')
  if (status === 'rejected') return t('rejected')
  if (status === 'hidden') return t('visibilityHidden')
  return status
}

async function loadManage() {
  loading.value = true
  try {
    const [scopesResponse, applicationsResponse] = await Promise.all([
      api.get('/management/scopes'),
      api.get('/moderator-applications/me')
    ])
    scopes.value = scopesResponse.data.scopes || []
    applications.value = applicationsResponse.data || []
    if (!selectedSchoolId.value && scopes.value.length > 0) selectedSchoolId.value = scopes.value[0].school.id
    await loadReports()
  } finally {
    loading.value = false
  }
}

async function refreshScopes() {
  const { data } = await api.get('/management/scopes')
  scopes.value = data.scopes || []
}

async function loadReports() {
  if (!selectedSchoolId.value) {
    reports.value = []
    return
  }
  const { data } = await api.get('/management/reports', { params: { school_id: selectedSchoolId.value, status: 'pending' } })
  reports.value = data
}

async function createBoard() {
  if (!selectedScope.value) return
  savingBoard.value = true
  try {
    await api.post('/management/boards', {
      school_id: selectedScope.value.school.id,
      parent_id: newBoard.value.parent_id,
      name: newBoard.value.name,
      description: newBoard.value.description || null
    })
    newBoard.value = { name: '', description: '', parent_id: null }
    await refreshScopes()
  } finally {
    savingBoard.value = false
  }
}

async function patchBoard(board: any, status: string) {
  await api.patch(`/management/boards/${board.id}`, { status })
  await refreshScopes()
}

function openSchoolDescription() {
  if (!selectedScope.value) return
  error.value = ''
  descriptionEditor.value = {
    type: 'school',
    id: selectedScope.value.school.id,
    title: schoolName(selectedScope.value.school),
    value: selectedScope.value.school.description || ''
  }
}

function openBoardDescription(board: any) {
  error.value = ''
  descriptionEditor.value = {
    type: 'board',
    id: board.id,
    title: board.parent_name ? `${board.parent_name} / ${board.name}` : board.name,
    value: board.description || ''
  }
}

async function saveDescription() {
  if (!descriptionEditor.value) return
  savingDescription.value = true
  error.value = ''
  try {
    if (descriptionEditor.value.type === 'school') {
      await api.patch(`/management/schools/${descriptionEditor.value.id}`, { description: descriptionEditor.value.value || null })
    } else {
      await api.patch(`/management/boards/${descriptionEditor.value.id}`, { description: descriptionEditor.value.value || null })
    }
    descriptionEditor.value = null
    await refreshScopes()
  } catch (e: any) {
    error.value = e.response?.data?.detail || t('descriptionSaveFailed')
  } finally {
    savingDescription.value = false
  }
}

async function handleReport(report: any, action: string) {
  await api.patch(`/management/reports/${report.id}`, { action, resolution: action })
  await loadReports()
}

watch(selectedSchoolId, loadReports)
onMounted(loadManage)
</script>
