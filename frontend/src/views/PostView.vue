<template>
  <div class="mx-auto max-w-4xl px-4 py-8">
    <button @click="$router.back()" class="mb-4 text-sm text-slate-500 hover:text-slate-950">{{ t('back') }}</button>

    <div v-if="loading" class="py-20 text-center text-sm text-slate-500">{{ t('loading') }}</div>
    <template v-else-if="post">
      <article class="panel mb-6 bg-white p-5">
        <div class="mb-4 flex flex-wrap items-center gap-2 border-b border-slate-200 pb-3">
          <span :class="post.is_pinned ? 'tag-accent' : 'tag'">{{ post.is_pinned ? t('pinned') : categoryLabel(post.category) }}</span>
          <span v-if="post.is_pinned" class="tag">{{ categoryLabel(post.category) }}</span>
          <span v-if="post.department_tag" class="tag">{{ post.department_tag }}</span>
          <span class="meta ml-auto">{{ formatDate(post.created_at) }}</span>
        </div>
        <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <h1 class="text-2xl font-semibold leading-tight text-slate-950">{{ post.title }}</h1>
            <p class="meta mt-2 flex flex-wrap items-center gap-2">
              <span>{{ post.author.display_name }}</span>
              <span v-if="post.author.source === 'agent'" class="tag-accent">{{ sourceLabel(post.author.source) }}</span>
            </p>
          </div>
          <div v-if="post.can_edit || post.can_delete" class="flex shrink-0 gap-2">
            <button v-if="post.can_edit" @click="openEdit" class="btn-secondary">{{ t('edit') }}</button>
            <button v-if="post.can_delete" @click="deletePost" class="btn-danger">{{ t('delete') }}</button>
          </div>
          <button v-else-if="auth.isLoggedIn" @click="openReport('post', post.id)" class="btn-secondary shrink-0">{{ t('report') }}</button>
        </div>
        <p class="text-sm leading-7 text-slate-700">
          <StickerText :text="post.content" />
        </p>
      </article>

      <div class="mb-3 flex items-center justify-between">
        <h2 class="text-base font-semibold text-slate-800">{{ t('commentsCount', { count: post.comment_count }) }}</h2>
      </div>

      <div v-if="auth.isLoggedIn" class="panel mb-4 bg-white p-4">
        <textarea
          ref="commentInput"
          v-model="commentText"
          class="input mb-2 h-24 resize-none"
          :placeholder="replyTo ? t('replyTo', { id: replyTo }) : t('writeReply')"
          @click="rememberCommentCursor"
          @input="rememberCommentCursor"
          @keyup="rememberCommentCursor"
          @select="rememberCommentCursor"
        ></textarea>
        <div class="flex flex-wrap items-center gap-3">
          <StickerPicker @select="insertCommentSticker" />
          <label class="flex cursor-pointer items-center gap-1.5 text-sm text-slate-600">
            <input type="checkbox" v-model="commentAnon" class="rounded border-slate-300" /> {{ t('anonymous') }}
          </label>
          <span v-if="replyTo" class="text-xs text-slate-500">
            {{ t('replyTo', { id: replyTo }) }}
            <button @click="replyTo = null" class="ml-1 text-red-600 hover:underline">{{ t('cancel') }}</button>
          </span>
          <button @click="submitComment" :disabled="!commentText.trim() || submitting" class="btn-primary ml-auto">
            {{ submitting ? t('submitting') : t('reply') }}
          </button>
        </div>
        <p v-if="commentError" class="mt-2 text-xs text-red-600">{{ commentError }}</p>
      </div>
      <p v-else class="mb-4 text-sm text-slate-500">
        <router-link to="/login" class="link">{{ t('login') }}</router-link> {{ t('loginToDiscuss') }}
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
            <h2 class="text-base font-semibold text-slate-950">{{ t('editPost') }}</h2>
            <button @click="showEdit = false" class="text-sm text-slate-500 hover:text-slate-950">{{ t('close') }}</button>
          </div>
          <form @submit.prevent="savePost" class="space-y-3">
            <input v-model.trim="editPost.title" required class="input" :placeholder="t('titlePlaceholder')" />
            <select v-model="editPost.category" class="select">
              <option v-for="category in writableCategories" :key="category" :value="category">{{ categoryLabel(category) }}</option>
            </select>
            <textarea
              ref="editPostContentInput"
              v-model.trim="editPost.content"
              required
              class="input h-36 resize-none"
              :placeholder="t('contentPlaceholder')"
              @click="rememberEditPostCursor"
              @input="rememberEditPostCursor"
              @keyup="rememberEditPostCursor"
              @select="rememberEditPostCursor"
            ></textarea>
            <div class="flex items-center justify-between gap-3">
              <StickerPicker @select="insertEditPostSticker" />
              <span class="text-xs text-slate-500">{{ t('stickerInsertHint') }}</span>
            </div>
            <input v-model.trim="editPost.department_tag" class="input" :placeholder="t('departmentTagPlaceholder')" />
            <label v-if="auth.isAdmin" class="flex cursor-pointer items-center gap-2 text-sm text-slate-600">
              <input type="checkbox" v-model="editPost.is_pinned" class="rounded border-slate-300" />
              {{ t('pinAnnouncement') }}
            </label>
            <p v-if="postError" class="text-sm text-red-600">{{ postError }}</p>
            <div class="flex justify-end gap-3 pt-2">
              <button type="button" @click="showEdit = false" class="btn-secondary">{{ t('cancel') }}</button>
              <button type="submit" :disabled="savingPost" class="btn-primary">{{ savingPost ? t('saving') : t('save') }}</button>
            </div>
          </form>
        </div>
      </div>

      <div v-if="reportTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4">
        <div class="panel w-full max-w-md bg-white p-5">
          <div class="mb-4 border-b border-slate-200 pb-3">
            <h2 class="text-base font-semibold text-slate-950">{{ t('reportContent') }}</h2>
          </div>
          <form @submit.prevent="submitReport" class="space-y-3">
            <select v-model="reportForm.reason" class="select">
              <option value="spam">{{ t('reportReasonSpam') }}</option>
              <option value="abuse">{{ t('reportReasonAbuse') }}</option>
              <option value="privacy">{{ t('reportReasonPrivacy') }}</option>
              <option value="other">{{ t('reportReasonOther') }}</option>
            </select>
            <textarea v-model.trim="reportForm.details" class="input h-24 resize-none" :placeholder="t('reportDetailsPlaceholder')"></textarea>
            <p v-if="reportError" class="text-sm text-red-600">{{ reportError }}</p>
            <p v-if="reportMessage" class="text-sm text-teal-700">{{ reportMessage }}</p>
            <div class="flex justify-end gap-3 pt-2">
              <button type="button" @click="closeReport" class="btn-secondary">{{ t('cancel') }}</button>
              <button type="submit" :disabled="reporting" class="btn-primary">{{ reporting ? t('submitting') : t('submitReport') }}</button>
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
import { useI18n } from '@/i18n'
import StickerPicker from '@/components/StickerPicker.vue'
import StickerText from '@/components/StickerText.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { t, categoryLabel, sourceLabel, formatDate } = useI18n()
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
const commentInput = ref<HTMLTextAreaElement | null>(null)
const editPostContentInput = ref<HTMLTextAreaElement | null>(null)
const commentCursor = ref({ start: 0, end: 0 })
const editPostContentCursor = ref({ start: 0, end: 0 })

const rootComments = computed(() => comments.value.filter((c) => !c.parent_id))
const repliesOf = (id: number) => comments.value.filter((c) => c.parent_id === id)

const CommentBlock = defineComponent({
  props: { comment: { type: Object, required: true } },
  emits: ['reply', 'remove', 'report'],
  setup(props, { emit }) {
    return () => h('div', [
      h('div', { class: 'mb-1 flex flex-wrap items-center gap-2 text-xs text-slate-500' }, [
        (props.comment as any).author.source === 'agent'
          ? h('span', { class: 'inline-grid h-5 w-5 place-items-center rounded-[4px] border border-sky-300 bg-sky-50 text-[10px] font-bold text-sky-700' }, 'Y')
          : null,
        h('span', { class: 'font-medium text-slate-700' }, (props.comment as any).author.display_name),
        (props.comment as any).author.source === 'agent'
          ? h('span', { class: 'tag-accent' }, (props.comment as any).author.display_name === 'Yutoko' ? 'Yutoko' : 'Agent')
          : null,
        h('span', { class: 'ml-auto' }, formatDate((props.comment as any).created_at)),
        auth.isLoggedIn && !(props.comment as any).is_deleted
          ? h('button', { class: 'link text-xs', onClick: () => emit('reply', (props.comment as any).id) }, t('quote', { id: (props.comment as any).id }))
          : null,
        (props.comment as any).can_delete
          ? h('button', { class: 'text-xs text-red-600 hover:underline', onClick: () => emit('remove', (props.comment as any).id) }, t('delete'))
          : null,
        auth.isLoggedIn && !(props.comment as any).is_deleted && !(props.comment as any).can_delete
          ? h('button', { class: 'text-xs text-slate-500 hover:underline', onClick: () => emit('report', (props.comment as any).id) }, t('report'))
          : null
      ]),
      h(
        'p',
        { class: [(props.comment as any).is_deleted ? 'text-slate-400 italic' : 'text-slate-700', 'text-sm leading-6'] },
        h(StickerText, { text: (props.comment as any).content, size: 'small' })
      )
    ])
  }
})

function rememberCursor(target: HTMLTextAreaElement | null, fallbackLength: number) {
  return {
    start: target?.selectionStart ?? fallbackLength,
    end: target?.selectionEnd ?? fallbackLength
  }
}

function rememberCommentCursor() {
  commentCursor.value = rememberCursor(commentInput.value, commentText.value.length)
}

function rememberEditPostCursor() {
  editPostContentCursor.value = rememberCursor(editPostContentInput.value, editPost.value.content.length)
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

function insertCommentSticker(code: string) {
  commentText.value = insertAtCursor(commentInput.value, commentText.value, code, commentCursor.value)
}

function insertEditPostSticker(code: string) {
  editPost.value.content = insertAtCursor(editPostContentInput.value, editPost.value.content, code, editPostContentCursor.value)
}

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
    postError.value = apiErrorMessage(e, t('saveFailed'))
  } finally {
    savingPost.value = false
  }
}

async function deletePost() {
  if (!window.confirm(t('confirmDeletePost'))) return
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
    commentError.value = apiErrorMessage(e, t('submitFailed'))
  } finally {
    submitting.value = false
  }
}

async function deleteComment(id: number) {
  if (!window.confirm(t('confirmDeleteComment'))) return
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
    reportMessage.value = t('reportSubmitted')
    notifyMascot('report-sent')
    window.setTimeout(closeReport, 800)
  } catch (e: any) {
    reportError.value = apiErrorMessage(e, t('submitFailed'))
  } finally {
    reporting.value = false
  }
}

function apiErrorMessage(e: any, fallback: string) {
  if (e.response?.status === 429) return t('rateLimited')
  return e.response?.data?.detail || fallback
}

function notifyMascot(context: string) {
  window.dispatchEvent(new CustomEvent('utoo:mascot-react', { detail: { context } }))
}

onMounted(load)
</script>
