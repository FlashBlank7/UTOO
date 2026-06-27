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
    <section
      v-if="selectedSchool"
      :class="[
        'mb-5 overflow-hidden border',
        isZhijiang
          ? 'rounded-[8px] border-fuchsia-200 bg-[linear-gradient(135deg,#fff_0%,#fff7fb_45%,#ecfeff_100%)]'
          : 'panel bg-white'
      ]"
    >
      <div :class="['relative px-4 py-5 md:px-5', isZhijiang ? 'zhijiang-stage' : '']">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div class="min-w-0">
            <p class="meta mb-2">{{ isZhijiang ? t('zhijiangKicker') : t('forumKicker') }}</p>
            <div class="flex flex-wrap items-center gap-3">
              <h1 class="text-2xl font-semibold text-slate-950 md:text-3xl">{{ schoolName(selectedSchool) }}</h1>
              <span v-if="isZhijiang" class="border border-fuchsia-300 bg-white/80 px-2 py-1 text-xs font-semibold text-fuchsia-700">{{ t('publicSquare') }}</span>
              <span v-else class="tag">{{ t('schoolBoard') }}</span>
            </div>
            <p class="mt-3 max-w-4xl text-sm leading-6 text-slate-600">
              {{ schoolDescription }}
            </p>
            <button
              v-if="canEditDescriptions"
              type="button"
              @click="openDescriptionEditor('school')"
              class="mt-2 text-xs font-medium text-slate-600 underline-offset-4 hover:text-slate-950 hover:underline"
            >
              {{ t('editDescription') }}
            </button>
            <div v-if="isZhijiang" class="mt-4 flex flex-wrap gap-2">
              <span v-for="signal in zhijiangSignals" :key="signal" class="border border-fuchsia-200 bg-white/80 px-2 py-1 text-xs font-medium text-fuchsia-800">{{ t(signal) }}</span>
            </div>
          </div>
          <div class="flex flex-col gap-2 sm:flex-row lg:shrink-0">
            <button @click="showSchoolSwitcher = true" class="btn-secondary">{{ t('switchSchool') }}</button>
            <button @click="openNewPost" class="btn-primary">{{ t('newPost') }}</button>
          </div>
        </div>
      </div>
    </section>

    <section v-if="isZhijiang" class="mb-5 grid gap-3 md:grid-cols-3">
      <div v-for="card in zhijiangCards" :key="card.title" class="border border-fuchsia-200 bg-white px-4 py-3">
        <p class="text-sm font-semibold text-slate-950">{{ t(card.title) }}</p>
        <p class="mt-1 text-xs leading-5 text-slate-600">{{ t(card.body) }}</p>
      </div>
    </section>

    <section v-if="selectedSchool" class="panel mb-5 bg-white">
      <div class="border-b border-slate-200 px-4 py-3">
        <div class="flex flex-wrap items-center gap-2 text-sm">
          <router-link :to="`/schools/${selectedSchool.slug}`" class="link font-medium">{{ schoolName(selectedSchool) }}</router-link>
          <span class="text-slate-400">/</span>
          <span v-if="activeParentBoard" class="font-medium text-slate-800">{{ activeParentBoard.name }}</span>
          <span v-else class="font-medium text-slate-800">{{ t('allBoards') }}</span>
          <template v-if="activeChildBoard">
            <span class="text-slate-400">/</span>
            <span class="font-semibold text-slate-950">{{ activeChildBoard.name }}</span>
            <span class="tag-accent">{{ t('subboard') }}</span>
          </template>
        </div>
        <h2 v-if="activeChildBoard" class="mt-2 text-xl font-semibold text-slate-950">
          {{ t('subboardTitle', { parent: activeParentBoard?.name || '', child: activeChildBoard.name }) }}
        </h2>
        <p v-else-if="activeParentBoard" class="mt-2 text-xl font-semibold text-slate-950">{{ activeParentBoard.name }}</p>
        <div v-if="activeBoard" class="mt-2 flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
          <p class="max-w-4xl text-sm leading-6 text-slate-600">
            {{ activeBoardDescription || t('boardIntroFallback') }}
          </p>
          <button
            v-if="canEditDescriptions"
            type="button"
            @click="openDescriptionEditor('board')"
            class="shrink-0 text-xs font-medium text-slate-600 underline-offset-4 hover:text-slate-950 hover:underline"
          >
            {{ t('editDescription') }}
          </button>
        </div>
      </div>

      <div class="border-b border-slate-200 px-3 py-3">
        <div class="flex gap-2 overflow-x-auto pb-1">
          <router-link :to="`/schools/${selectedSchool.slug}`" :class="topBoardClass(null)">
            {{ t('allBoards') }}
          </router-link>
          <router-link v-for="board in boards" :key="board.id" :to="boardPath(board)" :class="topBoardClass(board)">
            <span>{{ board.name }}</span>
            <span v-if="board.children?.length" class="ml-2 text-[11px] opacity-70">{{ board.children.length }}</span>
          </router-link>
        </div>
        <div v-if="childBoardsForActive.length" class="mt-3 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">
          <span class="meta">{{ t('subboardsOf', { board: activeParentBoard?.name || '' }) }}</span>
          <router-link v-for="child in childBoardsForActive" :key="child.id" :to="boardPath(child)" :class="childBoardClass(child)">
            {{ child.name }}
          </router-link>
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

    </section>

    <section v-if="selectedSchool" class="panel mb-5 bg-white p-4">
      <details>
        <summary class="cursor-pointer text-sm font-semibold text-slate-950">{{ t('requestBoard') }}</summary>
        <form @submit.prevent="requestBoard" class="mt-3 grid gap-2 md:grid-cols-[1fr_180px_auto]">
          <input v-model.trim="boardRequest.name" required class="input" :placeholder="t('boardNamePlaceholder')" />
          <select v-model="boardRequest.parent_id" class="select">
            <option :value="null">{{ t('topLevelBoard') }}</option>
            <option v-for="board in requestableParents" :key="board.id" :value="board.id">{{ board.name }}</option>
          </select>
          <button type="submit" :disabled="requestingBoard" class="btn-secondary">{{ requestingBoard ? t('submitting') : t('submitBoardRequest') }}</button>
          <textarea v-model.trim="boardRequest.description" class="input h-20 resize-none md:col-span-3" :placeholder="t('boardDescriptionPlaceholder')"></textarea>
          <p v-if="boardRequestMessage" class="text-xs text-teal-700 md:col-span-3">{{ boardRequestMessage }}</p>
          <p v-if="boardRequestError" class="text-xs text-red-600 md:col-span-3">{{ boardRequestError }}</p>
        </form>
      </details>
    </section>

    <section v-if="announcements.length > 0" class="panel mb-5 overflow-hidden border-teal-700/40">
      <div class="border-b border-slate-200 bg-teal-50 px-4 py-2 text-sm font-semibold text-teal-900">{{ t('pinnedAnnouncements') }}</div>
      <article
        v-for="post in announcements"
        :key="post.id"
        @click="openPost(post.id)"
        class="cursor-pointer border-t border-slate-200 bg-white px-4 py-3 first:border-t-0 hover:bg-slate-50"
      >
        <div class="mb-1 flex flex-wrap items-center gap-2">
          <span class="tag-accent">{{ categoryLabel('公告') }}</span>
          <span v-if="post.board" class="tag">{{ postBoardLabel(post) }}</span>
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
        @click="openPost(post.id)"
        class="cursor-pointer bg-white px-4 py-4 transition-colors hover:bg-slate-50"
      >
        <div class="mb-2 flex flex-wrap items-center gap-2">
          <span :class="post.is_pinned ? 'tag-accent' : 'tag'">{{ post.is_pinned ? t('pinned') : categoryLabel(post.category) }}</span>
          <span v-if="post.school" class="tag">{{ schoolName(post.school) }}</span>
          <span v-if="post.board" class="tag">{{ postBoardLabel(post) }}</span>
          <span v-if="post.parent_board" class="tag-accent">{{ t('subboard') }}</span>
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

    <div v-if="selectedPostId" class="fixed inset-0 z-50 bg-slate-950/35">
      <div class="absolute inset-y-0 right-0 w-full bg-slate-50 shadow-xl md:w-[min(760px,92vw)]">
        <PostDetailPanel
          :post-id="selectedPostId"
          embedded
          @close="closePost"
          @deleted="handlePostDeleted"
          @changed="loadPosts"
        />
      </div>
    </div>

    <div v-if="showSchoolSwitcher" class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/50 px-4">
      <div class="panel w-full max-w-2xl bg-white p-5">
        <div class="mb-4 flex items-center justify-between border-b border-slate-200 pb-3">
          <div>
            <h2 class="text-base font-semibold text-slate-950">{{ t('switchSchool') }}</h2>
            <p class="meta mt-1">{{ t('switchSchoolHint') }}</p>
          </div>
          <button @click="showSchoolSwitcher = false" class="text-sm text-slate-500 hover:text-slate-950">{{ t('close') }}</button>
        </div>
        <input v-model.trim="schoolSearch" class="input mb-3" :placeholder="t('schoolSearchPlaceholder')" />
        <div class="max-h-[420px] divide-y divide-slate-200 overflow-y-auto border border-slate-200">
          <router-link
            v-for="school in filteredSchools"
            :key="school.slug"
            :to="`/schools/${school.slug}`"
            @click="showSchoolSwitcher = false"
            class="block bg-white px-3 py-2 text-sm hover:bg-slate-50"
          >
            <div class="flex items-center justify-between gap-3">
              <span class="font-medium text-slate-950">{{ schoolName(school) }}</span>
              <span v-if="school.kind === 'virtual_public'" class="tag-accent">{{ t('publicArea') }}</span>
            </div>
            <p class="meta mt-1">{{ school.name_en }}</p>
          </router-link>
        </div>
      </div>
    </div>

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
          <textarea
            v-model.trim="descriptionEditor.value"
            class="input h-36 resize-none"
            :placeholder="t('descriptionPlaceholder')"
          ></textarea>
          <p v-if="descriptionSaveError" class="text-sm text-red-600">{{ descriptionSaveError }}</p>
          <div class="flex justify-end gap-3">
            <button type="button" @click="descriptionEditor = null" class="btn-secondary">{{ t('cancel') }}</button>
            <button type="submit" :disabled="savingDescription" class="btn-primary">{{ savingDescription ? t('saving') : t('save') }}</button>
          </div>
        </form>
      </div>
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
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from '@/i18n'
import StickerPicker from '@/components/StickerPicker.vue'
import PostDetailPanel from '@/components/PostDetailPanel.vue'
import { stickerPlainText } from '@/stickers/yutoko'

type School = {
  id: number
  slug: string
  name_zh: string
  name_en: string
  name_ja: string
  kind: string
  theme: string
  description?: string | null
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
const router = useRouter()
const auth = useAuthStore()
const { t, categoryLabel, sourceLabel, formatDate, currentLocale } = useI18n()
const posts = ref<any[]>([])
const announcements = ref<any[]>([])
const schools = ref<School[]>([])
const boards = ref<Board[]>([])
const loading = ref(false)
const searchText = ref('')
const appliedSearch = ref('')
const showNewPost = ref(false)
const posting = ref(false)
const postError = ref('')
const boardRequestMessage = ref('')
const boardRequestError = ref('')
const requestingBoard = ref(false)
const showSchoolSwitcher = ref(false)
const schoolSearch = ref('')
const savingDescription = ref(false)
const descriptionSaveError = ref('')
const descriptionEditor = ref<null | { type: 'school' | 'board'; id: number; title: string; value: string }>(null)
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
const zhijiangSignals = ['zhijiangSignalCheer', 'zhijiangSignalBroadcast', 'zhijiangSignalDorm', 'zhijiangSignalHelp']
const zhijiangCards = [
  { title: 'zhijiangCardSquareTitle', body: 'zhijiangCardSquareBody' },
  { title: 'zhijiangCardBroadcastTitle', body: 'zhijiangCardBroadcastBody' },
  { title: 'zhijiangCardSupportTitle', body: 'zhijiangCardSupportBody' }
]
const writableCategories = computed(() => auth.isAdmin ? ['公告', ...categories] : categories)
const selectedSchoolSlug = computed(() => {
  const routeSlug = typeof route.params.schoolSlug === 'string' ? route.params.schoolSlug : ''
  return routeSlug || auth.user?.school?.slug || 'zhijiang-university'
})
const selectedBoardSlug = computed(() => typeof route.params.boardSlug === 'string' ? route.params.boardSlug : '')
const selectedSchool = computed(() => schools.value.find((school) => school.slug === selectedSchoolSlug.value) || null)
const flatBoards = computed(() => boards.value.flatMap((board) => [board, ...(board.children || [])]))
const activeBoard = computed(() => flatBoards.value.find((board) => board.slug === selectedBoardSlug.value) || null)
const activeParentBoard = computed(() => {
  if (!activeBoard.value) return null
  if (!activeBoard.value.parent_id) return activeBoard.value
  return boards.value.find((board) => board.id === activeBoard.value?.parent_id) || null
})
const activeChildBoard = computed(() => activeBoard.value?.parent_id ? activeBoard.value : null)
const childBoardsForActive = computed(() => {
  const parent = activeParentBoard.value
  if (!parent?.children?.length) return []
  return parent.children.filter((child) => child.parent_id === parent.id && child.id !== parent.id)
})
const isZhijiang = computed(() => selectedSchool.value?.slug === 'zhijiang-university' || selectedSchool.value?.theme === 'zhijiang')
const schoolDescription = computed(() => selectedSchool.value?.description || (isZhijiang.value ? t('zhijiangSpecialIntro') : t('schoolIntro')))
const activeBoardDescription = computed(() => activeBoard.value?.description || '')
const canEditDescriptions = computed(() => auth.isAdmin)
const selectedPostId = computed(() => typeof route.query.post === 'string' ? route.query.post : '')
const filteredSchools = computed(() => {
  const query = schoolSearch.value.trim().toLowerCase()
  if (!query) {
    const current = selectedSchool.value ? [selectedSchool.value] : []
    const publicSchool = schools.value.find((school) => school.slug === 'zhijiang-university')
    const rest = schools.value.filter((school) => school.id !== selectedSchool.value?.id && school.id !== publicSchool?.id)
    return [...current, ...(publicSchool && publicSchool.id !== selectedSchool.value?.id ? [publicSchool] : []), ...rest].slice(0, 30)
  }
  return schools.value.filter((school) => {
    return [school.name_zh, school.name_en, school.name_ja, school.slug].some((value) => value?.toLowerCase().includes(query))
  }).slice(0, 50)
})
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

function topBoardClass(board: Board | null) {
  const active = board ? activeParentBoard.value?.id === board.id : !activeBoard.value
  return [
    'inline-flex shrink-0 items-center border px-3 py-2 text-sm font-medium transition-colors',
    active ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
  ]
}

function childBoardClass(board: Board) {
  const active = activeChildBoard.value?.id === board.id
  return [
    'inline-flex items-center border px-3 py-1.5 text-xs font-medium transition-colors',
    active ? 'border-teal-700 bg-teal-50 text-teal-800' : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
  ]
}

function boardPathLabel(board: Board) {
  const parent = boards.value.find((item) => item.id === board.parent_id)
  return parent ? `${parent.name} / ${board.name}` : board.name
}

function openDescriptionEditor(type: 'school' | 'board') {
  descriptionSaveError.value = ''
  if (type === 'school' && selectedSchool.value) {
    descriptionEditor.value = {
      type,
      id: selectedSchool.value.id,
      title: schoolName(selectedSchool.value),
      value: selectedSchool.value.description || ''
    }
  }
  if (type === 'board' && activeBoard.value) {
    descriptionEditor.value = {
      type,
      id: activeBoard.value.id,
      title: boardPathLabel(activeBoard.value),
      value: activeBoard.value.description || ''
    }
  }
}

async function saveDescription() {
  if (!descriptionEditor.value) return
  savingDescription.value = true
  descriptionSaveError.value = ''
  try {
    if (descriptionEditor.value.type === 'school') {
      await api.patch(`/admin/schools/${descriptionEditor.value.id}`, { description: descriptionEditor.value.value || null })
      await loadSchools()
    } else {
      await api.patch(`/admin/boards/${descriptionEditor.value.id}`, { description: descriptionEditor.value.value || null })
      await loadBoards()
    }
    descriptionEditor.value = null
  } catch (e: any) {
    descriptionSaveError.value = e.response?.data?.detail || t('descriptionSaveFailed')
  } finally {
    savingDescription.value = false
  }
}

function postBoardLabel(post: any) {
  if (post.parent_board && post.board) return `${post.parent_board.name} > ${post.board.name}`
  return post.board?.name || ''
}

function openPost(id: number) {
  router.push({ path: route.path, query: { ...route.query, post: String(id), mascotPose: 'post' } })
}

function closePost() {
  const next = { ...route.query }
  delete next.post
  delete next.mascotPose
  router.push({ path: route.path, query: next })
}

async function handlePostDeleted() {
  await loadPosts()
  await loadAnnouncements()
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

watch(selectedSchoolSlug, async () => {
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
