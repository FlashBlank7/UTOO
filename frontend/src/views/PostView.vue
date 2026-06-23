<template>
  <div class="max-w-2xl mx-auto px-4 py-8">
    <button @click="$router.back()" class="text-sm text-gray-400 hover:text-gray-600 mb-4">← 返回</button>

    <div v-if="loading" class="text-center text-gray-400 py-20">加载中…</div>
    <template v-else-if="post">
      <!-- 帖子 -->
      <div class="bg-white rounded-lg shadow-sm border border-gray-100 p-6 mb-6">
        <div class="flex items-center gap-2 text-xs text-gray-400 mb-3">
          <span class="font-medium text-gray-600">{{ post.author.display_name }}</span>
          <span v-if="post.department_tag" class="bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">{{ post.department_tag }}</span>
          <span class="ml-auto">{{ formatTime(post.created_at) }}</span>
        </div>
        <h1 class="text-xl font-bold text-gray-800 mb-3">{{ post.title }}</h1>
        <p class="text-gray-700 whitespace-pre-wrap">{{ post.content }}</p>
      </div>

      <!-- 评论区 -->
      <h2 class="font-semibold text-gray-700 mb-3">{{ comments.length }} 条回复</h2>

      <!-- 发评论 -->
      <div v-if="auth.isLoggedIn" class="bg-white rounded-lg border border-gray-200 p-4 mb-4">
        <textarea v-model="commentText" class="input h-20 resize-none mb-2" :placeholder="replyTo ? `回复 #${replyTo}` : '写下你的回复…'"></textarea>
        <div class="flex items-center gap-3">
          <label class="flex items-center gap-1.5 text-sm text-gray-600 cursor-pointer">
            <input type="checkbox" v-model="commentAnon" class="rounded" /> 匿名
          </label>
          <span v-if="replyTo" class="text-xs text-gray-400">回复 #{{ replyTo }} <button @click="replyTo = null" class="ml-1 text-red-400">×</button></span>
          <button @click="submitComment" :disabled="!commentText.trim() || submitting" class="btn-primary text-sm ml-auto">
            {{ submitting ? '提交中…' : '回复' }}
          </button>
        </div>
        <p v-if="commentError" class="text-red-500 text-xs mt-1">{{ commentError }}</p>
      </div>
      <p v-else class="text-sm text-gray-400 mb-4">
        <router-link to="/login" class="text-indigo-500 hover:underline">登录</router-link> 后参与讨论
      </p>

      <!-- 评论列表 -->
      <div class="space-y-3">
        <div
          v-for="c in rootComments"
          :key="c.id"
          class="bg-white rounded-lg border border-gray-100 p-4"
        >
          <div class="flex items-center gap-2 text-xs text-gray-400 mb-1">
            <span class="font-medium text-gray-600">{{ c.author.display_name }}</span>
            <span class="ml-auto">{{ formatTime(c.created_at) }}</span>
            <button v-if="auth.isLoggedIn" @click="replyTo = c.id" class="text-indigo-400 hover:underline"># {{ c.id }} 引用</button>
          </div>
          <p class="text-gray-700 text-sm whitespace-pre-wrap">{{ c.content }}</p>

          <!-- 二级回复 -->
          <div v-for="r in repliesOf(c.id)" :key="r.id" class="ml-4 mt-2 border-l-2 border-gray-100 pl-3">
            <div class="flex items-center gap-2 text-xs text-gray-400 mb-0.5">
              <span class="font-medium text-gray-600">{{ r.author.display_name }}</span>
              <span class="ml-auto">{{ formatTime(r.created_at) }}</span>
            </div>
            <p class="text-gray-700 text-sm whitespace-pre-wrap">{{ r.content }}</p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()
const postId = route.params.id as string

const post = ref<any>(null)
const comments = ref<any[]>([])
const loading = ref(true)
const commentText = ref('')
const commentAnon = ref(false)
const replyTo = ref<number | null>(null)
const submitting = ref(false)
const commentError = ref('')

const rootComments = computed(() => comments.value.filter((c) => !c.parent_id))
const repliesOf = (id: number) => comments.value.filter((c) => c.parent_id === id)

async function load() {
  loading.value = true
  try {
    const [postRes, commentsRes] = await Promise.all([
      api.get(`/posts/${postId}`),
      api.get(`/comments/post/${postId}`)
    ])
    post.value = postRes.data
    comments.value = commentsRes.data
  } finally {
    loading.value = false
  }
}

async function submitComment() {
  commentError.value = ''
  submitting.value = true
  try {
    await api.post(`/comments/post/${postId}`, {
      content: commentText.value,
      is_anonymous: commentAnon.value,
      parent_id: replyTo.value ?? undefined
    })
    commentText.value = ''
    replyTo.value = null
    const { data } = await api.get(`/comments/post/${postId}`)
    comments.value = data
  } catch (e: any) {
    commentError.value = e.response?.data?.detail || '提交失败'
  } finally {
    submitting.value = false
  }
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(load)
</script>
