<template>
  <div class="mx-auto max-w-4xl px-4 py-8">
    <button @click="$router.back()" class="mb-4 text-sm text-slate-500 hover:text-slate-950">返回</button>

    <div v-if="loading" class="py-20 text-center text-sm text-slate-500">加载中...</div>
    <template v-else-if="post">
      <article class="panel mb-6 bg-white p-5">
        <div class="mb-4 flex flex-wrap items-center gap-2 border-b border-slate-200 pb-3">
          <span :class="post.is_pinned ? 'tag-accent' : 'tag'">{{ post.is_pinned ? '置顶' : post.category }}</span>
          <span v-if="post.is_pinned" class="tag">{{ post.category }}</span>
          <span v-if="post.department_tag" class="tag">{{ post.department_tag }}</span>
          <span class="meta ml-auto">{{ formatTime(post.created_at) }}</span>
        </div>
        <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <h1 class="text-2xl font-semibold leading-tight text-slate-950">{{ post.title }}</h1>
            <p class="meta mt-2 flex flex-wrap items-center gap-2">
              <span>{{ post.author.display_name }}</span>
              <span v-if="post.author.source === 'agent'" class="tag-accent">Agent</span>
            </p>
          </div>
          <div v-if="post.can_edit || post.can_delete" class="flex shrink-0 gap-2">
            <button v-if="post.can_edit" @click="openEdit" class="btn-secondary">编辑</button>
            <button v-if="post.can_delete" @click="deletePost" class="btn-danger">删除</button>
          </div>
          <button v-else-if="auth.isLoggedIn" @click="openReport('post', post.id)" class="btn-secondary shrink-0">举报</button>
        </div>
        <p class="whitespace-pre-wrap text-sm leading-7 text-slate-700">{{ post.content }}</p>
      </article>

      <div class="mb-3 flex items-center justify-between">
        <h2 class="text-base font-semibold text-slate-800">{{ post.comment_count }} 条回复</h2>
      </div>

      <div v-if="auth.isLoggedIn" class="panel mb-4 bg-white p-4">
        <textarea
          v-model="commentText"
          class="input mb-2 h-24 resize-none"
          :placeholder="replyTo ? `回复 #${replyTo}` : '写下你的回复'"
        ></textarea>
        <div class="flex flex-wrap items-center gap-3">
          <label class="flex cursor-pointer items-center gap-1.5 text-sm text-slate-600">
            <input type="checkbox" v-model="commentAnon" class="rounded border-slate-300" /> 匿名
          </label>
          <span v-if="replyTo" class="text-xs text-slate-500">
            回复 #{{ replyTo }}
            <button @click="replyTo = null" class="ml-1 text-red-600 hover:underline">取消</button>
          </span>
          <button @click="submitComment" :disabled="!commentText.trim() || submitting" class="btn-primary ml-auto">
            {{ submitting ? '提交中...' : '回复' }}
          </button>
        </div>
        <p v-if="commentError" class="mt-2 text-xs text-red-600">{{ commentError }}</p>
      </div>
      <p v-else class="mb-4 text-sm text-slate-500">
        <router-link to="/login" class="link">登录</router-link> 后参与讨论
      </p>

      <div class="space-y-3">
        <section
          v-for="c in rootComments"
          :key="c.id"
          class="panel bg-white p-4"
          :class="c.is_deleted ? 'bg-slate-50' : ''"
        >
          <CommentBlock :comment="c" @reply="replyTo = $event" @remove="deleteComment" @report="openReport('comment', $event)" />

          <div v-for="r in repliesOf(c.id)" :key="r.id" class="ml-4 mt-3 border-l border-slate-200 pl-3">
            <CommentBlock :comment="r" @reply="replyTo = $event" @remove="deleteComment" @report="openReport('comment', $event)" />
          </div>
        </section>
      </div>

      <div v-if="showEdit" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4">
        <div class="panel w-full max-w-lg bg-white p-5">
          <div class="mb-4 flex items-center justify-between border-b border-slate-200 pb-3">
            <h2 class="text-base font-semibold text-slate-950">编辑帖子</h2>
            <button @click="showEdit = false" class="text-sm text-slate-500 hover:text-slate-950">关闭</button>
          </div>
          <form @submit.prevent="savePost" class="space-y-3">
            <input v-model.trim="editPost.title" required class="input" placeholder="标题" />
            <select v-model="editPost.category" class="select">
              <option v-for="category in writableCategories" :key="category" :value="category">{{ category }}</option>
            </select>
            <textarea v-model.trim="editPost.content" required class="input h-36 resize-none" placeholder="内容"></textarea>
            <input v-model.trim="editPost.department_tag" class="input" placeholder="专攻标签（可选）" />
            <label v-if="auth.isAdmin" class="flex cursor-pointer items-center gap-2 text-sm text-slate-600">
              <input type="checkbox" v-model="editPost.is_pinned" class="rounded border-slate-300" />
              置顶公告
            </label>
            <p v-if="postError" class="text-sm text-red-600">{{ postError }}</p>
            <div class="flex justify-end gap-3 pt-2">
              <button type="button" @click="showEdit = false" class="btn-secondary">取消</button>
              <button type="submit" :disabled="savingPost" class="btn-primary">{{ savingPost ? '保存中...' : '保存' }}</button>
            </div>
          </form>
        </div>
      </div>

      <div v-if="reportTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4">
        <div class="panel w-full max-w-md bg-white p-5">
          <div class="mb-4 border-b border-slate-200 pb-3">
            <h2 class="text-base font-semibold text-slate-950">举报内容</h2>
          </div>
          <form @submit.prevent="submitReport" class="space-y-3">
            <select v-model="reportForm.reason" class="select">
              <option value="spam">广告 / 灌水</option>
              <option value="abuse">攻击 / 骚扰</option>
              <option value="privacy">隐私风险</option>
              <option value="other">其他</option>
            </select>
            <textarea v-model.trim="reportForm.details" class="input h-24 resize-none" placeholder="补充说明（可选）"></textarea>
            <p v-if="reportError" class="text-sm text-red-600">{{ reportError }}</p>
            <p v-if="reportMessage" class="text-sm text-teal-700">{{ reportMessage }}</p>
            <div class="flex justify-end gap-3 pt-2">
              <button type="button" @click="closeReport" class="btn-secondary">取消</button>
              <button type="submit" :disabled="reporting" class="btn-primary">{{ reporting ? '提交中...' : '提交举报' }}</button>
            </div>
          </form>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const postId = route.params.id as string
const categories = ['课程', '研究室', '生活', '租房', '就职', '闲聊']
const writableCategories = computed(() => auth.isAdmin ? ['公告', ...categories] : categories)

const post = ref<any>(null)
const comments = ref<any[]>([])
const loading = ref(true)
const commentText = ref('')
const commentAnon = ref(false)
const replyTo = ref<number | null>(null)
const submitting = ref(false)
const commentError = ref('')
const showEdit = ref(false)
const savingPost = ref(false)
const postError = ref('')
const editPost = ref({ title: '', content: '', department_tag: '', category: '闲聊', is_pinned: false })
const reportTarget = ref<{ type: string; id: number } | null>(null)
const reportForm = ref({ reason: 'spam', details: '' })
const reportError = ref('')
const reportMessage = ref('')
const reporting = ref(false)

const rootComments = computed(() => comments.value.filter((c) => !c.parent_id))
const repliesOf = (id: number) => comments.value.filter((c) => c.parent_id === id)

const CommentBlock = defineComponent({
  props: { comment: { type: Object, required: true } },
  emits: ['reply', 'remove', 'report'],
  setup(props, { emit }) {
    return () => h('div', [
      h('div', { class: 'mb-1 flex flex-wrap items-center gap-2 text-xs text-slate-500' }, [
        h('span', { class: 'font-medium text-slate-700' }, (props.comment as any).author.display_name),
        h('span', { class: 'ml-auto' }, formatTime((props.comment as any).created_at)),
        auth.isLoggedIn && !(props.comment as any).is_deleted
          ? h('button', { class: 'link text-xs', onClick: () => emit('reply', (props.comment as any).id) }, `# ${(props.comment as any).id} 引用`)
          : null,
        (props.comment as any).can_delete
          ? h('button', { class: 'text-xs text-red-600 hover:underline', onClick: () => emit('remove', (props.comment as any).id) }, '删除')
          : null,
        auth.isLoggedIn && !(props.comment as any).is_deleted && !(props.comment as any).can_delete
          ? h('button', { class: 'text-xs text-slate-500 hover:underline', onClick: () => emit('report', (props.comment as any).id) }, '举报')
          : null
      ]),
      h(
        'p',
        { class: [(props.comment as any).is_deleted ? 'text-slate-400 italic' : 'text-slate-700', 'whitespace-pre-wrap text-sm leading-6'] },
        (props.comment as any).content
      )
    ])
  }
})

async function load() {
  loading.value = true
  try {
    await refreshPostAndComments()
  } finally {
    loading.value = false
  }
}

async function refreshPostAndComments() {
  const [postRes, commentsRes] = await Promise.all([
    api.get(`/posts/${postId}`),
    api.get(`/comments/post/${postId}`)
  ])
  post.value = postRes.data
  comments.value = commentsRes.data
}

function openEdit() {
  editPost.value = {
    title: post.value.title,
    content: post.value.content,
    department_tag: post.value.department_tag || '',
    category: post.value.category,
    is_pinned: post.value.is_pinned
  }
  postError.value = ''
  showEdit.value = true
}

async function savePost() {
  savingPost.value = true
  postError.value = ''
  try {
    const payload: Record<string, any> = {
      title: editPost.value.title,
      content: editPost.value.content,
      category: editPost.value.category,
      department_tag: editPost.value.department_tag || null
    }
    if (auth.isAdmin) payload.is_pinned = editPost.value.is_pinned
    const { data } = await api.patch(`/posts/${postId}`, payload)
    post.value = data
    showEdit.value = false
  } catch (e: any) {
    postError.value = e.response?.data?.detail || '保存失败'
  } finally {
    savingPost.value = false
  }
}

async function deletePost() {
  if (!window.confirm('确认删除这篇帖子？')) return
  await api.delete(`/posts/${postId}`)
  router.push('/')
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
    await refreshPostAndComments()
    notifyMascot('comment-created')
  } catch (e: any) {
    commentError.value = e.response?.data?.detail || '提交失败'
  } finally {
    submitting.value = false
  }
}

async function deleteComment(id: number) {
  if (!window.confirm('确认删除这条评论？')) return
  await api.delete(`/comments/${id}`)
  await refreshPostAndComments()
}

function openReport(type: string, id: number) {
  reportTarget.value = { type, id }
  reportForm.value = { reason: 'spam', details: '' }
  reportError.value = ''
  reportMessage.value = ''
}

function closeReport() {
  reportTarget.value = null
  reportError.value = ''
  reportMessage.value = ''
}

async function submitReport() {
  if (!reportTarget.value) return
  reporting.value = true
  reportError.value = ''
  reportMessage.value = ''
  try {
    await api.post('/reports', {
      target_type: reportTarget.value.type,
      target_id: reportTarget.value.id,
      reason: reportForm.value.reason,
      details: reportForm.value.details || null
    })
    reportMessage.value = '举报已提交'
    notifyMascot('report-sent')
    window.setTimeout(closeReport, 800)
  } catch (e: any) {
    reportError.value = e.response?.data?.detail || '提交失败'
  } finally {
    reporting.value = false
  }
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function notifyMascot(context: string) {
  window.dispatchEvent(new CustomEvent('utoo:mascot-react', { detail: { context } }))
}

onMounted(load)
</script>
