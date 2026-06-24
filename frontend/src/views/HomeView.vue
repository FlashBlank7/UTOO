<template>
  <div class="mx-auto max-w-5xl px-4 py-8">
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
          <span>{{ post.author.display_name }}</span>
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
const loading = ref(false)
const filterCategory = ref<string | null>(null)
const searchText = ref('')
const appliedSearch = ref('')
const showNewPost = ref(false)
const posting = ref(false)
const postError = ref('')
const categories = ['课程', '研究室', '生活', '租房', '就职', '闲聊']
const filterCategories = computed(() => [
  { label: '全部', value: null },
  { label: '公告', value: '公告' },
  ...categories.map((category) => ({ label: category, value: category }))
])
const writableCategories = computed(() => auth.isAdmin ? ['公告', ...categories] : categories)
const newPost = ref({ title: '', content: '', department_tag: '', category: '闲聊', is_anonymous: false })

async function loadPosts() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (filterCategory.value) params.category = filterCategory.value
    if (appliedSearch.value) params.q = appliedSearch.value
    const { data } = await api.get('/posts', { params })
    posts.value = data
  } finally {
    loading.value = false
  }
}

function applySearch() {
  appliedSearch.value = searchText.value.trim()
  loadPosts()
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

watch(filterCategory, loadPosts)
onMounted(loadPosts)
</script>
