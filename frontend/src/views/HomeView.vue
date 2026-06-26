<template>
  <div v-if="!auth.isLoggedIn" class="mx-auto max-w-6xl px-4 py-8 md:py-12">
    <section class="border-b border-slate-200 pb-8 md:grid md:grid-cols-[minmax(0,1fr)_360px] md:gap-10 md:pb-10">
      <div>
        <div class="mb-6 flex items-center gap-4">
          <img src="/favicon.svg" alt="" class="h-16 w-16 shrink-0 rounded-[6px] border border-slate-200 bg-white" />
          <div>
            <p class="meta mb-1">Independent UTokyo student community</p>
            <h1 class="text-4xl font-semibold leading-tight text-slate-950 md:text-5xl">UTOO</h1>
          </div>
        </div>
        <p class="max-w-3xl text-lg font-medium leading-8 text-slate-800">
          面向 UTokyo 学生的课程、研究室、生活、租房与就职讨论空间。
        </p>
        <p class="mt-3 max-w-3xl text-sm leading-7 text-slate-600">
          把零散经验沉淀成可检索的社区资料：选课评价、研究室观察、搬家租房、校园生活、实习就职和公告规则都集中在一个克制、清晰的论坛入口里。
        </p>
        <div class="mt-7 flex flex-col gap-3 sm:flex-row">
          <router-link to="/login" class="btn-primary text-center">登录进入论坛</router-link>
          <router-link to="/register" class="btn-secondary text-center">注册账号</router-link>
        </div>
      </div>

      <aside class="mt-8 border-l-0 border-slate-200 pt-6 md:mt-0 md:border-l md:pl-6 md:pt-0">
        <div class="mb-4 flex items-center justify-between border-b border-slate-200 pb-2">
          <span class="text-sm font-semibold text-slate-950">Forum Index</span>
          <span class="meta">login required</span>
        </div>
        <div class="space-y-2">
          <div
            v-for="item in categoryHighlights"
            :key="item.name"
            class="grid grid-cols-[64px_1fr] gap-3 border border-slate-200 bg-white px-3 py-2"
          >
            <span class="tag justify-center">{{ item.name }}</span>
            <span class="text-xs leading-5 text-slate-600">{{ item.summary }}</span>
          </div>
        </div>
        <p class="mt-5 border-t border-slate-200 pt-4 text-xs leading-5 text-slate-500">
          UTOO is an independent student community and is not an official University of Tokyo service.
        </p>
      </aside>
    </section>

    <section class="grid gap-5 py-8 md:grid-cols-[1.15fr_0.85fr]">
      <div class="border-t border-slate-300 pt-4">
        <p class="mb-3 text-sm font-semibold text-slate-950">社区资料层</p>
        <div class="grid gap-3 sm:grid-cols-2">
          <div v-for="item in publicSignals" :key="item.title" class="border-l-2 border-slate-300 pl-3">
            <p class="text-sm font-medium text-slate-950">{{ item.title }}</p>
            <p class="mt-1 text-sm leading-6 text-slate-600">{{ item.body }}</p>
          </div>
        </div>
      </div>
      <div class="border-t border-slate-300 pt-4">
        <p class="mb-3 text-sm font-semibold text-slate-950">访问边界</p>
        <p class="text-sm leading-7 text-slate-600">
          帖子、评论和公告仅对登录用户开放。公开页面用于介绍社区与收录入口，真实讨论内容不开放给搜索引擎抓取。
        </p>
        <div class="mt-4 flex flex-wrap gap-2">
          <span v-for="category in categories" :key="category" class="tag">{{ category }}</span>
        </div>
      </div>
    </section>
  </div>

  <div v-else class="mx-auto max-w-5xl px-4 py-8">
    <div class="mb-6 flex flex-col gap-4 border-b border-slate-200 pb-5 md:flex-row md:items-end md:justify-between">
      <div>
        <p class="meta mb-1">UTOO Forum</p>
        <h1 class="text-2xl font-semibold text-slate-950">帖子索引</h1>
      </div>
      <button v-if="auth.isLoggedIn" @click="showNewPost = true" class="btn-primary w-full md:w-auto">
        发帖
      </button>
    </div>

    <div class="panel mb-5 p-3">
      <div class="grid gap-3 md:grid-cols-[1fr_auto] md:items-center">
        <input
          v-model.trim="searchText"
          class="input"
          placeholder="搜索标题或内容"
          @keyup.enter="applySearch"
        />
        <button @click="applySearch" class="btn-secondary">搜索</button>
      </div>

      <div class="mt-3 flex flex-wrap gap-1 border-t border-slate-200 pt-3">
        <button
          v-for="item in filterCategories"
          :key="item.value || 'all'"
          @click="filterCategory = item.value"
          :class="[
            'border px-3 py-1.5 text-xs font-medium rounded-[3px] transition-colors',
            filterCategory === item.value
              ? 'border-slate-950 bg-slate-950 text-white'
              : 'border-slate-300 bg-white text-slate-600 hover:bg-slate-100 hover:text-slate-950'
          ]"
        >
          {{ item.label }}
        </button>
      </div>
    </div>

    <section v-if="announcements.length > 0" class="panel mb-5 overflow-hidden border-teal-700/40">
      <div class="border-b border-slate-200 bg-teal-50 px-4 py-2 text-sm font-semibold text-teal-900">置顶公告</div>
      <article
        v-for="post in announcements"
        :key="post.id"
        @click="$router.push(`/post/${post.id}`)"
        class="cursor-pointer border-t border-slate-200 bg-white px-4 py-3 first:border-t-0 hover:bg-slate-50"
      >
        <div class="mb-1 flex flex-wrap items-center gap-2">
          <span class="tag-accent">公告</span>
          <span class="meta ml-auto">{{ formatTime(post.created_at) }}</span>
        </div>
        <h2 class="text-sm font-semibold text-slate-950">{{ post.title }}</h2>
        <p class="line-clamp-1 text-sm text-slate-600">{{ post.content }}</p>
      </article>
    </section>

    <div v-if="loading" class="py-20 text-center text-sm text-slate-500">加载中...</div>
    <div v-else-if="posts.length === 0" class="panel py-16 text-center text-sm text-slate-500">暂无帖子</div>
    <div v-else class="panel divide-y divide-slate-200 overflow-hidden">
      <article
        v-for="post in posts"
        :key="post.id"
        @click="$router.push(`/post/${post.id}`)"
        class="cursor-pointer bg-white px-4 py-4 transition-colors hover:bg-slate-50"
      >
        <div class="mb-2 flex flex-wrap items-center gap-2">
          <span :class="post.is_pinned ? 'tag-accent' : 'tag'">{{ post.is_pinned ? '置顶' : post.category }}</span>
          <span v-if="post.is_pinned" class="tag">{{ post.category }}</span>
          <span v-if="post.department_tag" class="tag">{{ post.department_tag }}</span>
          <span class="meta ml-auto">{{ formatTime(post.created_at) }}</span>
        </div>
        <h2 class="mb-1 text-base font-semibold leading-snug text-slate-950">{{ post.title }}</h2>
        <p class="line-clamp-2 text-sm leading-6 text-slate-600">{{ post.content }}</p>
        <div class="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
          <span class="inline-flex items-center gap-2">
            <span>{{ post.author.display_name }}</span>
            <span v-if="post.author.source === 'agent'" class="tag-accent">Agent</span>
          </span>
          <span>{{ post.comment_count }} 条回复</span>
        </div>
      </article>
    </div>

    <div v-if="showNewPost" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4">
      <div class="panel w-full max-w-lg bg-white p-5">
        <div class="mb-4 flex items-center justify-between border-b border-slate-200 pb-3">
          <h2 class="text-base font-semibold text-slate-950">发新帖</h2>
          <button @click="showNewPost = false" class="text-sm text-slate-500 hover:text-slate-950">关闭</button>
        </div>
        <form @submit.prevent="submitPost" class="space-y-3">
          <input v-model.trim="newPost.title" required class="input" placeholder="标题" />
          <select v-model="newPost.category" class="select">
            <option v-for="category in writableCategories" :key="category" :value="category">{{ category }}</option>
          </select>
          <textarea v-model.trim="newPost.content" required class="input h-36 resize-none" placeholder="内容"></textarea>
          <input v-model.trim="newPost.department_tag" class="input" placeholder="专攻标签（可选）" />
          <label class="flex cursor-pointer items-center gap-2 text-sm text-slate-600">
            <input type="checkbox" v-model="newPost.is_anonymous" class="rounded border-slate-300" />
            匿名发布
          </label>
          <p v-if="postError" class="text-sm text-red-600">{{ postError }}</p>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="showNewPost = false" class="btn-secondary">取消</button>
            <button type="submit" :disabled="posting" class="btn-primary">{{ posting ? '发布中...' : '发布' }}</button>
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

const auth = useAuthStore()
const posts = ref<any[]>([])
const announcements = ref<any[]>([])
const loading = ref(false)
const filterCategory = ref<string | null>(null)
const searchText = ref('')
const appliedSearch = ref('')
const showNewPost = ref(false)
const posting = ref(false)
const postError = ref('')
const categories = ['课程', '研究室', '生活', '租房', '就职', '闲聊']
const categoryHighlights = [
  { name: '课程', summary: '选课、作业、考试和授课体验' },
  { name: '研究室', summary: '实验室氛围、申请和研究生活' },
  { name: '生活', summary: '手续、校园服务和日常经验' },
  { name: '租房', summary: '区域、预算、通勤和搬家信息' },
  { name: '就职', summary: '实习、求职、面试和行业讨论' },
  { name: '闲聊', summary: '轻量交流和社区互助' }
]
const publicSignals = [
  { title: '面向学生经验', body: '围绕校园里的真实问题组织讨论，优先沉淀可复用的信息。' },
  { title: '登录后阅读', body: '社区内容保持半封闭，不把帖子和评论直接暴露给搜索引擎。' },
  { title: '公告与规则', body: '管理员可发布置顶公告，集中维护投稿说明和社区规则。' },
  { title: '清晰来源', body: '用户与 Agent 内容明确区分，自动化账号会显示来源标记。' }
]
const filterCategories = computed(() => [
  { label: '全部', value: null },
  { label: '公告', value: '公告' },
  ...categories.map((category) => ({ label: category, value: category }))
])
const writableCategories = computed(() => auth.isAdmin ? ['公告', ...categories] : categories)
const newPost = ref({ title: '', content: '', department_tag: '', category: '闲聊', is_anonymous: false })

async function loadPosts() {
  if (!auth.isLoggedIn) return
  loading.value = true
  try {
    const params: Record<string, string> = {}
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
  const { data } = await api.get('/posts', { params: { category: '公告', page_size: 5 } })
  announcements.value = data.filter((post: any) => post.is_pinned)
}

async function applySearch() {
  appliedSearch.value = searchText.value.trim()
  await loadPosts()
  if (appliedSearch.value) notifyMascot('search-applied')
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
    if (newPost.value.department_tag) payload.department_tag = newPost.value.department_tag
    await api.post('/posts', payload)
    showNewPost.value = false
    newPost.value = { title: '', content: '', department_tag: '', category: '闲聊', is_anonymous: false }
    await loadPosts()
    notifyMascot('post-created')
  } catch (e: any) {
    postError.value = e.response?.data?.detail || '发布失败'
  } finally {
    posting.value = false
  }
}

function formatTime(iso: string) {
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function notifyMascot(context: string) {
  window.dispatchEvent(new CustomEvent('utoo:mascot-react', { detail: { context } }))
}

watch(filterCategory, loadPosts)
watch(() => auth.isLoggedIn, (loggedIn) => {
  if (loggedIn) {
    loadAnnouncements()
    loadPosts()
  } else {
    posts.value = []
    announcements.value = []
  }
})
onMounted(() => {
  if (auth.isLoggedIn) {
    loadAnnouncements()
    loadPosts()
  }
})
</script>
