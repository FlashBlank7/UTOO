<template>
  <div class="max-w-2xl mx-auto px-4 py-8">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-xl font-bold text-gray-800">最新帖子</h1>
      <button v-if="auth.isLoggedIn" @click="showNewPost = true" class="btn-primary text-sm">
        + 发帖
      </button>
    </div>

    <!-- 专攻筛选 -->
    <div class="flex gap-2 flex-wrap mb-4">
      <button
        v-for="dept in departments"
        :key="dept"
        @click="filterDept = filterDept === dept ? null : dept"
        :class="['px-3 py-1 rounded-full text-xs border transition', filterDept === dept ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-white text-gray-600 border-gray-300 hover:border-indigo-400']"
      >{{ dept }}</button>
    </div>

    <div v-if="loading" class="text-center text-gray-400 py-20">加载中…</div>
    <div v-else-if="posts.length === 0" class="text-center text-gray-400 py-20">暂无帖子</div>
    <div v-else class="space-y-3">
      <div
        v-for="post in posts"
        :key="post.id"
        @click="$router.push(`/post/${post.id}`)"
        class="bg-white rounded-lg shadow-sm border border-gray-100 p-4 cursor-pointer hover:shadow transition"
      >
        <div class="flex items-center gap-2 text-xs text-gray-400 mb-2">
          <span class="font-medium text-gray-600">{{ post.author.display_name }}</span>
          <span v-if="post.department_tag" class="bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">{{ post.department_tag }}</span>
          <span class="ml-auto">{{ formatTime(post.created_at) }}</span>
        </div>
        <h2 class="font-semibold text-gray-800 mb-1">{{ post.title }}</h2>
        <p class="text-sm text-gray-500 line-clamp-2">{{ post.content }}</p>
        <div class="text-xs text-gray-400 mt-2">{{ post.comment_count }} 条回复</div>
      </div>
    </div>

    <!-- 发帖 Modal -->
    <div v-if="showNewPost" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 px-4">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-lg font-bold mb-4">发新帖</h2>
        <form @submit.prevent="submitPost" class="space-y-3">
          <input v-model="newPost.title" required class="input" placeholder="标题" />
          <textarea v-model="newPost.content" required class="input h-32 resize-none" placeholder="内容…"></textarea>
          <input v-model="newPost.department_tag" class="input" placeholder="专攻标签（可选）" />
          <label class="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input type="checkbox" v-model="newPost.is_anonymous" class="rounded" />
            匿名发布
          </label>
          <p v-if="postError" class="text-red-500 text-sm">{{ postError }}</p>
          <div class="flex gap-3 justify-end">
            <button type="button" @click="showNewPost = false" class="btn-secondary">取消</button>
            <button type="submit" :disabled="posting" class="btn-primary">{{ posting ? '发布中…' : '发布' }}</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const posts = ref<any[]>([])
const loading = ref(false)
const filterDept = ref<string | null>(null)
const departments = ref<string[]>([])
const showNewPost = ref(false)
const posting = ref(false)
const postError = ref('')
const newPost = ref({ title: '', content: '', department_tag: '', is_anonymous: false })

async function loadPosts() {
  loading.value = true
  try {
    const params: Record<string, string> = {}
    if (filterDept.value) params.department = filterDept.value
    const { data } = await api.get('/posts', { params })
    posts.value = data
    // collect unique department tags for filter chips
    const tags = new Set<string>()
    data.forEach((p: any) => { if (p.department_tag) tags.add(p.department_tag) })
    departments.value = Array.from(tags)
  } finally {
    loading.value = false
  }
}

async function submitPost() {
  postError.value = ''
  posting.value = true
  try {
    const payload: Record<string, any> = {
      title: newPost.value.title,
      content: newPost.value.content,
      is_anonymous: newPost.value.is_anonymous,
    }
    if (newPost.value.department_tag) payload.department_tag = newPost.value.department_tag
    await api.post('/posts', payload)
    showNewPost.value = false
    newPost.value = { title: '', content: '', department_tag: '', is_anonymous: false }
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

watch(filterDept, loadPosts)
onMounted(loadPosts)
</script>
