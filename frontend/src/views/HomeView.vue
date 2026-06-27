<template>
  <div v-if="!auth.isLoggedIn" class="mx-auto max-w-6xl px-4 py-8 md:py-12">
    <section class="border-b border-slate-200 pb-8 md:grid md:grid-cols-[minmax(0,1fr)_360px] md:gap-10 md:pb-10">
      <div>
        <div class="mb-6 flex items-center gap-4">
          <img src="/favicon.svg" alt="" class="h-16 w-16 shrink-0 rounded-[6px] border border-slate-200 bg-white" />
          <div>
            <p class="meta mb-1">{{ t('homeKicker') }}</p>
            <h1 class="text-4xl font-semibold leading-tight text-slate-950 md:text-5xl">{{ t('homeHeadline') }}</h1>
          </div>
        </div>
        <p class="max-w-3xl text-lg font-medium leading-8 text-slate-800">
          {{ t('homeLead') }}
        </p>
        <p class="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
          {{ t('homeBody') }}
        </p>
        <div class="mt-7 flex flex-col gap-3 sm:flex-row">
          <router-link to="/login" class="btn-primary text-center">{{ t('homeLogin') }}</router-link>
          <router-link to="/register" class="btn-secondary text-center">{{ t('homeRegister') }}</router-link>
        </div>
      </div>

      <aside class="mt-8 border-l-0 border-slate-200 pt-6 md:mt-0 md:border-l md:pl-6 md:pt-0">
        <div class="mb-4 flex items-center justify-between border-b border-slate-200 pb-2">
          <span class="text-sm font-semibold text-slate-950">{{ t('homeIndexTitle') }}</span>
          <span class="meta">{{ t('homeLoginRequired') }}</span>
        </div>
        <div class="space-y-2">
          <div
            v-for="item in publicSignals"
            :key="item.title"
            class="border border-slate-200 bg-white px-3 py-2"
          >
            <p class="text-sm font-medium text-slate-950">{{ t(item.title) }}</p>
            <p class="mt-1 text-xs leading-5 text-slate-600">{{ t(item.body) }}</p>
          </div>
        </div>
        <p class="mt-5 border-t border-slate-200 pt-4 text-xs leading-5 text-slate-500">
          {{ t('homeIndependentNotice') }}
        </p>
      </aside>
    </section>

    <section class="grid gap-5 py-8 md:grid-cols-[1.15fr_0.85fr]">
      <div class="border-t border-slate-300 pt-4">
        <p class="mb-3 text-sm font-semibold text-slate-950">{{ t('homeSchoolsLayer') }}</p>
        <div class="grid gap-3 sm:grid-cols-2">
          <div v-for="item in schoolPreview" :key="item.title" class="border-l-2 border-slate-300 pl-3">
            <p class="text-sm font-medium text-slate-950">{{ t(item.title) }}</p>
            <p class="mt-1 text-sm leading-6 text-slate-600">{{ t(item.body) }}</p>
          </div>
        </div>
      </div>
      <div class="border-t border-slate-300 pt-4">
        <p class="mb-3 text-sm font-semibold text-slate-950">{{ t('homeAccessBoundary') }}</p>
        <p class="text-sm leading-7 text-slate-600">
          {{ t('homeAccessBody') }}
        </p>
        <div class="mt-4 flex flex-wrap gap-2">
          <span v-for="category in categories" :key="category" class="tag">{{ categoryLabel(category) }}</span>
        </div>
      </div>
    </section>
  </div>

  <div v-else class="mx-auto max-w-7xl px-4 py-8">
    <div class="mb-6 flex flex-col gap-4 border-b border-slate-200 pb-5 md:flex-row md:items-end md:justify-between">
      <div>
        <p class="meta mb-1">{{ t('forumKicker') }}</p>
        <h1 class="text-2xl font-semibold text-slate-950">{{ t('forumIndex') }}</h1>
      </div>
      <button @click="openNewPost" class="btn-primary w-full md:w-auto">
        {{ t('newPost') }}
      </button>
    </div>

    <div class="grid gap-5 lg:grid-cols-[280px_minmax(0,1fr)]">
      <aside class="space-y-4">
        <section class="panel bg-white p-3">
          <div class="mb-3 flex items-center justify-between border-b border-slate-200 pb-2">
            <span class="text-sm font-semibold text-slate-950">{{ t('schools') }}</span>
            <span class="meta">{{ schools.length }}</span>
          </div>
          <div class="max-h-[360px] space-y-1 overflow-y-auto pr-1">
            <router-link
              v-for="school in schools"
              :key="school.slug"
              :to="`/schools/${school.slug}`"
              :class="[
                'block border px-3 py-2 text-sm transition-colors',
                selectedSchool?.slug === school.slug
                  ? 'border-slate-950 bg-slate-950 text-white'
                  : school.theme === 'zhijiang'
                    ? 'border-fuchsia-200 bg-fuchsia-50/60 text-fuchsia-950 hover:border-fuchsia-300'
                    : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
              ]"
            >
              <span class="font-medium">{{ schoolName(school) }}</span>
              <span v-if="school.kind === 'virtual_public'" class="ml-2 text-[11px] opacity-75">{{ t('publicArea') }}</span>
            </router-link>
          </div>
        </section>

        <section class="panel bg-white p-3">
          <div class="mb-3 border-b border-slate-200 pb-2">
            <p class="text-sm font-semibold text-slate-950">{{ t('boards') }}</p>
            <p class="meta mt-1">{{ selectedSchool ? schoolName(selectedSchool) : '-' }}</p>
          </div>
          <div class="space-y-1">
            <router-link
              v-if="selectedSchool"
              :to="`/schools/${selectedSchool.slug}`"
              :class="boardClass(null)"
            >
              {{ t('allBoards') }}
            </router-link>
            <template v-for="board in boards" :key="board.id">
              <router-link
                :to="boardPath(board)"
                :class="boardClass(board)"
              >
                {{ board.name }}
              </router-link>
              <router-link
                v-for="child in board.children || []"
                :key="child.id"
                :to="boardPath(child)"
                :class="[boardClass(child), 'ml-4']"
              >
                {{ child.name }}
              </router-link>
            </template>
          </div>
        </section>

        <section v-if="selectedSchool" class="panel bg-white p-3">
          <p class="mb-2 text-sm font-semibold text-slate-950">{{ t('requestBoard') }}</p>
          <form @submit.prevent="requestBoard" class="space-y-2">
            <input v-model.trim="boardRequest.name" required class="input" :placeholder="t('boardNamePlaceholder')" />
            <select v-model="boardRequest.parent_id" class="select">
              <option :value="null">{{ t('topLevelBoard') }}</option>
              <option v-for="board in requestableParents" :key="board.id" :value="board.id">{{ board.name }}</option>
            </select>
            <textarea v-model.trim="boardRequest.description" class="input h-20 resize-none" :placeholder="t('boardDescriptionPlaceholder')"></textarea>
            <p v-if="boardRequestMessage" class="text-xs text-teal-700">{{ boardRequestMessage }}</p>
            <p v-if="boardRequestError" class="text-xs text-red-600">{{ boardRequestError }}</p>
            <button type="submit" :disabled="requestingBoard" class="btn-secondary w-full">{{ requestingBoard ? t('submitting') : t('submitBoardRequest') }}</button>
          </form>
        </section>
      </aside>

      <main>
        <section
          v-if="selectedSchool"
          :class="[
            'panel mb-5 overflow-hidden bg-white',
            selectedSchool.theme === 'zhijiang' ? 'border-fuchsia-200 bg-gradient-to-br from-white via-fuchsia-50/40 to-cyan-50/50' : ''
          ]"
        >
          <div class="border-b border-slate-200 px-4 py-4">
            <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <p class="meta mb-1">{{ selectedSchool.kind === 'virtual_public' ? t('publicArea') : t('schoolBoard') }}</p>
                <h2 class="text-2xl font-semibold text-slate-950">{{ schoolName(selectedSchool) }}</h2>
                <p class="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
                  {{ selectedSchool.theme === 'zhijiang' ? t('zhijiangIntro') : t('schoolIntro') }}
                </p>
              </div>
              <div v-if="activeBoard" class="shrink-0 border border-slate-200 bg-white px-3 py-2 text-sm">
                <span class="meta">{{ activeBoard.parent_id ? t('subboard') : t('board') }}</span>
                <p class="font-semibold text-slate-950">{{ activeBoard.name }}</p>
              </div>
            </div>
          </div>

          <div class="grid gap-3 p-3 md:grid-cols-[1fr_auto] md:items-center">
            <input
              v-model.trim="searchText"
              class="input"
              :placeholder="t('searchPlaceholder')"
              @keyup.enter="applySearch"
            />
            <button @click="applySearch" class="btn-secondary">{{ t('search') }}</button>
          </div>

          <div class="flex flex-wrap gap-1 border-t border-slate-200 px-3 py-3">
            <button
              v-for="item in filterCategories"
              :key="item.value || 'all'"
              @click="filterCategory = item.value"
              :class="[
                'rounded-[3px] border px-3 py-1.5 text-xs font-medium transition-colors',
                filterCategory === item.value
                  ? 'border-slate-950 bg-slate-950 text-white'
                  : 'border-slate-300 bg-white text-slate-600 hover:bg-slate-100 hover:text-slate-950'
              ]"
            >
              {{ item.label }}
            </button>
          </div>
        </section>

        <section v-if="announcements.length > 0" class="panel mb-5 overflow-hidden border-teal-700/40">
          <div class="border-b border-slate-200 bg-teal-50 px-4 py-2 text-sm font-semibold text-teal-900">{{ t('pinnedAnnouncements') }}</div>
          <article
            v-for="post in announcements"
            :key="post.id"
            @click="$router.push(`/post/${post.id}`)"
            class="cursor-pointer border-t border-slate-200 bg-white px-4 py-3 first:border-t-0 hover:bg-slate-50"
          >
            <div class="mb-1 flex flex-wrap items-center gap-2">
              <span class="tag-accent">{{ categoryLabel('公告') }}</span>
              <span v-if="post.board" class="tag">{{ post.board.name }}</span>
              <span class="meta ml-auto">{{ formatDate(post.created_at) }}</span>
            </div>
            <h2 class="text-sm font-semibold text-slate-950">{{ post.title }}</h2>
            <p class="line-clamp-1 text-sm text-slate-600">{{ stickerPlainText(post.content) }}</p>
          </article>
        </section>

        <div v-if="loading" class="py-20 text-center text-sm text-slate-500">{{ t('loading') }}</div>
        <div v-else-if="posts.length === 0" class="panel py-16 text-center text-sm text-slate-500">{{ t('noPosts') }}</div>
        <div v-else class="panel divide-y divide-slate-200 overflow-hidden">
          <article
            v-for="post in posts"
            :key="post.id"
            @click="$router.push(`/post/${post.id}`)"
            class="cursor-pointer bg-white px-4 py-4 transition-colors hover:bg-slate-50"
          >
            <div class="mb-2 flex flex-wrap items-center gap-2">
              <span :class="post.is_pinned ? 'tag-accent' : 'tag'">{{ post.is_pinned ? t('pinned') : categoryLabel(post.category) }}</span>
              <span v-if="post.school" class="tag">{{ schoolName(post.school) }}</span>
              <span v-if="post.parent_board" class="tag">{{ post.parent_board.name }}</span>
              <span v-if="post.board" class="tag">{{ post.board.name }}</span>
              <span v-if="post.department_tag" class="tag">{{ post.department_tag }}</span>
              <span class="meta ml-auto">{{ formatDate(post.created_at) }}</span>
            </div>
            <h2 class="mb-1 text-base font-semibold leading-snug text-slate-950">{{ post.title }}</h2>
            <p class="line-clamp-2 text-sm leading-6 text-slate-600">{{ stickerPlainText(post.content) }}</p>
            <div class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
              <span class="inline-flex items-center gap-2">
                <span>{{ post.author.display_name }}</span>
                <span v-if="post.author.source === 'agent'" class="tag-accent">{{ sourceLabel(post.author.source) }}</span>
              </span>
              <span>{{ t('commentsCount', { count: post.comment_count }) }}</span>
            </div>
          </article>
        </div>
      </main>
    </div>

    <div v-if="showNewPost" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4">
      <div class="panel w-full max-w-lg bg-white p-5">
        <div class="mb-4 flex items-center justify-between border-b border-slate-200 pb-3">
          <h2 class="text-base font-semibold text-slate-950">{{ t('newPostTitle') }}</h2>
          <button @click="showNewPost = false" class="text-sm text-slate-500 hover:text-slate-950">{{ t('close') }}</button>
        </div>
        <form @submit.prevent="submitPost" class="space-y-3">
          <input v-model.trim="newPost.title" required class="input" :placeholder="t('titlePlaceholder')" />
          <select v-model.number="newPost.board_id" class="select">
            <option v-for="board in writableBoards" :key="board.id" :value="board.id">{{ boardPathLabel(board) }}</option>
          </select>
          <select v-model="newPost.category" class="select">
            <option v-for="category in writableCategories" :key="category" :value="category">{{ categoryLabel(category) }}</option>
          </select>
          <textarea
            ref="newPostContentInput"
            v-model.trim="newPost.content"
            required
            class="input h-36 resize-none"
            :placeholder="t('contentPlaceholder')"
            @click="rememberNewPostCursor"
            @input="rememberNewPostCursor"
            @keyup="rememberNewPostCursor"
            @select="rememberNewPostCursor"
          ></textarea>
          <div class="flex items-center justify-between gap-3">
            <StickerPicker @select="insertNewPostSticker" />
            <span class="text-xs text-slate-500">{{ t('stickerInsertHint') }}</span>
          </div>
          <input v-model.trim="newPost.department_tag" class="input" :placeholder="t('departmentTagPlaceholder')" />
          <label class="flex cursor-pointer items-center gap-2 text-sm text-slate-600">
            <input type="checkbox" v-model="newPost.is_anonymous" class="rounded border-slate-300" />
            {{ t('postAnonymous') }}
          </label>
          <p v-if="postError" class="text-sm text-red-600">{{ postError }}</p>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="showNewPost = false" class="btn-secondary">{{ t('cancel') }}</button>
            <button type="submit" :disabled="posting" class="btn-primary">{{ posting ? t('publishing') : t('publish') }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from '@/i18n'
import StickerPicker from '@/components/StickerPicker.vue'
import { stickerPlainText } from '@/stickers/yutoko'

type School = {
  id: number
  slug: string
  name_zh: string
  name_en: string
  name_ja: string
  kind: string
  theme: string
}

type Board = {
  id: number
  school_id: number
  parent_id: number | null
  slug: string
  name: string
  description?: string | null
  status: string
  children?: Board[]
}

const route = useRoute()
const auth = useAuthStore()
const { t, categoryLabel, sourceLabel, formatDate, currentLocale } = useI18n()
const posts = ref<any[]>([])
const announcements = ref<any[]>([])
const schools = ref<School[]>([])
const boards = ref<Board[]>([])
const loading = ref(false)
const filterCategory = ref<string | null>(null)
const searchText = ref('')
const appliedSearch = ref('')
const showNewPost = ref(false)
const posting = ref(false)
const postError = ref('')
const boardRequestMessage = ref('')
const boardRequestError = ref('')
const requestingBoard = ref(false)
const newPostContentInput = ref<HTMLTextAreaElement | null>(null)
const newPostContentCursor = ref({ start: 0, end: 0 })
const categories = ['课程', '研究室', '生活', '租房', '就职', '闲聊']
const publicSignals = [
  { title: 'homeSignalSchoolsTitle', body: 'homeSignalSchoolsBody' },
  { title: 'homeSignalPublicTitle', body: 'homeSignalPublicBody' },
  { title: 'homeSignalLoginTitle', body: 'homeSignalLoginBody' },
  { title: 'homeSignalRulesTitle', body: 'homeSignalRulesBody' }
]
const schoolPreview = [
  { title: 'homeSchoolPreviewRealTitle', body: 'homeSchoolPreviewRealBody' },
  { title: 'homeSchoolPreviewPublicTitle', body: 'homeSchoolPreviewPublicBody' },
  { title: 'homeSchoolPreviewBoardsTitle', body: 'homeSchoolPreviewBoardsBody' },
  { title: 'homeSchoolPreviewAgentTitle', body: 'homeSchoolPreviewAgentBody' }
]
const filterCategories = computed(() => [
  { label: t('categoryAll'), value: null },
  { label: categoryLabel('公告'), value: '公告' },
  ...categories.map((category) => ({ label: categoryLabel(category), value: category }))
])
const writableCategories = computed(() => auth.isAdmin ? ['公告', ...categories] : categories)
const selectedSchoolSlug = computed(() => {
  const routeSlug = typeof route.params.schoolSlug === 'string' ? route.params.schoolSlug : ''
  return routeSlug || auth.user?.school?.slug || 'zhijiang-university'
})
const selectedBoardSlug = computed(() => typeof route.params.boardSlug === 'string' ? route.params.boardSlug : '')
const selectedSchool = computed(() => schools.value.find((school) => school.slug === selectedSchoolSlug.value) || null)
const flatBoards = computed(() => boards.value.flatMap((board) => [board, ...(board.children || [])]))
const activeBoard = computed(() => flatBoards.value.find((board) => board.slug === selectedBoardSlug.value) || null)
const requestableParents = computed(() => boards.value.filter((board) => board.slug !== 'notice'))
const writableBoards = computed(() => flatBoards.value.filter((board) => auth.isAdmin || board.slug !== 'notice'))
const boardRequest = ref<{ name: string; description: string; parent_id: number | null }>({ name: '', description: '', parent_id: null })
const newPost = ref({ title: '', content: '', department_tag: '', category: '闲聊', is_anonymous: false, board_id: null as number | null })

function schoolName(school: School | null | undefined) {
  if (!school) return ''
  if (currentLocale.value === 'en') return school.name_en || school.name_zh
  if (currentLocale.value === 'ja') return school.name_ja || school.name_zh
  return school.name_zh || school.name_en
}

function boardPath(board: Board) {
  return selectedSchool.value ? `/schools/${selectedSchool.value.slug}/boards/${board.slug}` : '/'
}

function boardClass(board: Board | null) {
  const active = board ? activeBoard.value?.id === board.id : !activeBoard.value
  return [
    'block border px-3 py-2 text-sm transition-colors',
    active ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
  ]
}

function boardPathLabel(board: Board) {
  const parent = boards.value.find((item) => item.id === board.parent_id)
  return parent ? `${parent.name} / ${board.name}` : board.name
}

function rememberNewPostCursor() {
  const target = newPostContentInput.value
  if (!target) return
  newPostContentCursor.value = {
    start: target.selectionStart ?? newPost.value.content.length,
    end: target.selectionEnd ?? newPost.value.content.length
  }
}

function insertAtCursor(target: HTMLTextAreaElement | null, current: string, token: string, cursor: { start: number; end: number }) {
  const insert = current && !/[\s\n]$/.test(current) ? ` ${token} ` : `${token} `
  const start = Math.min(cursor.start, current.length)
  const end = Math.min(cursor.end, current.length)
  if (!target) return `${current.slice(0, start)}${insert}${current.slice(end)}`

  const next = `${current.slice(0, start)}${insert}${current.slice(end)}`
  requestAnimationFrame(() => {
    target.focus()
    const position = start + insert.length
    target.setSelectionRange(position, position)
    cursor.start = position
    cursor.end = position
  })
  return next
}

function insertNewPostSticker(code: string) {
  rememberNewPostCursor()
  newPost.value.content = insertAtCursor(newPostContentInput.value, newPost.value.content, code, newPostContentCursor.value)
}

async function loadSchools() {
  if (!auth.isLoggedIn) return
  const { data } = await api.get('/schools')
  schools.value = data
}

async function loadBoards() {
  if (!auth.isLoggedIn || !selectedSchoolSlug.value) return
  const { data } = await api.get(`/schools/${selectedSchoolSlug.value}/boards`)
  boards.value = data
}

async function loadPosts() {
  if (!auth.isLoggedIn) return
  loading.value = true
  try {
    const params: Record<string, string | number> = { school_slug: selectedSchoolSlug.value }
    if (activeBoard.value) params.board_id = activeBoard.value.id
    if (filterCategory.value) params.category = filterCategory.value
    if (appliedSearch.value) params.q = appliedSearch.value
    const { data } = await api.get('/posts', { params })
    posts.value = data
    if (data.length === 0) notifyMascot('empty-list')
  } finally {
    loading.value = false
  }
}

async function loadAnnouncements() {
  if (!auth.isLoggedIn) return
  const { data } = await api.get('/posts', { params: { school_slug: selectedSchoolSlug.value, category: '公告', page_size: 5 } })
  announcements.value = data.filter((post: any) => post.is_pinned)
}

async function refreshForum() {
  if (!auth.isLoggedIn) return
  await loadBoards()
  await Promise.all([loadAnnouncements(), loadPosts()])
}

async function applySearch() {
  appliedSearch.value = searchText.value.trim()
  await loadPosts()
  if (appliedSearch.value) notifyMascot('search-applied')
}

function openNewPost() {
  const candidate = activeBoard.value && (auth.isAdmin || activeBoard.value.slug !== 'notice')
    ? activeBoard.value
    : writableBoards.value.find((board) => board.slug !== 'notice') || writableBoards.value[0]
  newPost.value.board_id = candidate?.id ?? null
  if (candidate?.name && categories.includes(candidate.name)) newPost.value.category = candidate.name
  showNewPost.value = true
}

async function submitPost() {
  postError.value = ''
  posting.value = true
  try {
    const payload: Record<string, any> = {
      title: newPost.value.title,
      content: newPost.value.content,
      category: newPost.value.category,
      is_anonymous: newPost.value.is_anonymous,
    }
    if (newPost.value.board_id) payload.board_id = newPost.value.board_id
    if (newPost.value.department_tag) payload.department_tag = newPost.value.department_tag
    await api.post('/posts', payload)
    showNewPost.value = false
    newPost.value = { title: '', content: '', department_tag: '', category: '闲聊', is_anonymous: false, board_id: null }
    await loadPosts()
    notifyMascot('post-created')
  } catch (e: any) {
    postError.value = apiErrorMessage(e, t('postFailed'))
  } finally {
    posting.value = false
  }
}

async function requestBoard() {
  if (!selectedSchool.value) return
  requestingBoard.value = true
  boardRequestMessage.value = ''
  boardRequestError.value = ''
  try {
    await api.post('/boards', {
      school_id: selectedSchool.value.id,
      parent_id: boardRequest.value.parent_id,
      name: boardRequest.value.name,
      description: boardRequest.value.description || null
    })
    boardRequest.value = { name: '', description: '', parent_id: null }
    boardRequestMessage.value = t('boardRequestSubmitted')
  } catch (e: any) {
    boardRequestError.value = e.response?.data?.detail || t('boardRequestFailed')
  } finally {
    requestingBoard.value = false
  }
}

function apiErrorMessage(e: any, fallback: string) {
  if (e.response?.status === 429) return t('rateLimited')
  return e.response?.data?.detail || fallback
}

function notifyMascot(context: string) {
  window.dispatchEvent(new CustomEvent('utoo:mascot-react', { detail: { context } }))
}

watch(filterCategory, loadPosts)
watch(selectedSchoolSlug, async () => {
  filterCategory.value = null
  searchText.value = ''
  appliedSearch.value = ''
  boardRequest.value = { name: '', description: '', parent_id: null }
  await refreshForum()
})
watch(selectedBoardSlug, loadPosts)
watch(() => auth.isLoggedIn, async (loggedIn) => {
  if (loggedIn) {
    await loadSchools()
    await refreshForum()
  } else {
    schools.value = []
    boards.value = []
    posts.value = []
    announcements.value = []
  }
})
onMounted(async () => {
  if (auth.isLoggedIn) {
    await loadSchools()
    await refreshForum()
  }
})
</script>
