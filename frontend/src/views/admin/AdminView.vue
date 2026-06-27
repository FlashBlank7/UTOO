<template>
  <div class="mx-auto max-w-6xl px-4 py-8">
    <div class="mb-6 border-b border-slate-200 pb-5">
      <p class="meta mb-1">Admin</p>
      <h1 class="text-2xl font-semibold text-slate-950">{{ t('adminTitle') }}</h1>
    </div>

    <div class="mb-6 flex gap-1 border-b border-slate-200">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="activeTab = tab.key"
        :class="[
          'border-b-2 px-3 py-2 text-sm font-medium transition-colors',
          activeTab === tab.key
            ? 'border-slate-950 text-slate-950'
            : 'border-transparent text-slate-500 hover:text-slate-900'
        ]"
      >
        {{ t(tab.labelKey) }}
      </button>
    </div>

    <template v-if="activeTab === 'codes'">
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <input v-model.number="newMaxUses" type="number" min="1" class="input w-32" :placeholder="t('maxUsesPlaceholder')" />
        <button @click="generateCode" :disabled="generating" class="btn-primary">
          {{ generating ? t('generatingCode') : t('generateCode') }}
        </button>
      </div>
      <div class="panel overflow-x-auto">
        <table class="w-full min-w-[760px] text-sm">
          <thead class="table-head">
            <tr>
              <th class="px-4 py-3 text-left">{{ t('activationCodeColumn') }}</th>
              <th class="px-4 py-3 text-center">{{ t('usedLimit') }}</th>
              <th class="px-4 py-3 text-center">{{ t('status') }}</th>
              <th class="px-4 py-3 text-center">{{ t('createdAt') }}</th>
              <th class="px-4 py-3 text-center">{{ t('action') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="code in codes" :key="code.id" class="table-row">
              <td class="px-4 py-3 font-mono font-semibold text-slate-800">{{ code.code }}</td>
              <td class="px-4 py-3 text-center">{{ code.use_count }} / {{ code.max_uses }}</td>
              <td class="px-4 py-3 text-center">
                <span :class="code.is_active ? 'tag-accent' : 'tag'">{{ code.is_active ? t('active') : t('inactive') }}</span>
              </td>
              <td class="px-4 py-3 text-center text-slate-500">{{ formatDate(code.created_at) }}</td>
              <td class="px-4 py-3 text-center">
                <button v-if="code.is_active" @click="deactivateCode(code.id)" class="text-xs text-red-600 hover:underline">{{ t('deactivate') }}</button>
                <button @click="viewUsages(code)" class="link ml-3 text-xs">{{ t('viewUsers') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="codes.length === 0" class="py-8 text-center text-sm text-slate-500">{{ t('noActivationCodes') }}</div>
      </div>

      <div v-if="selectedCode" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4">
        <div class="panel w-full max-w-md bg-white p-5">
          <div class="mb-4 flex items-center justify-between border-b border-slate-200 pb-3">
            <h3 class="font-semibold text-slate-950">{{ t('registeredUsersTitle', { code: selectedCode.code }) }}</h3>
            <button @click="selectedCode = null" class="text-sm text-slate-500 hover:text-slate-950">{{ t('close') }}</button>
          </div>
          <div v-if="usages.length === 0" class="py-4 text-center text-sm text-slate-500">{{ t('noUsers') }}</div>
          <ul v-else class="space-y-2 text-sm">
            <li v-for="u in usages" :key="u.user_id" class="flex justify-between gap-3 text-slate-700">
              <span>{{ u.display_name || u.username || t('navAccountFallback', { id: u.user_id }) }} · {{ u.department || '-' }}</span>
              <span class="shrink-0 text-slate-500">{{ formatDate(u.used_at) }}</span>
            </li>
          </ul>
        </div>
      </div>
    </template>

    <template v-if="activeTab === 'users'">
      <div class="panel overflow-x-auto">
        <table class="w-full min-w-[860px] text-sm">
          <thead class="table-head">
            <tr>
              <th class="px-4 py-3 text-left">{{ t('id') }}</th>
              <th class="px-4 py-3 text-left">{{ t('username') }}</th>
              <th class="px-4 py-3 text-left">{{ t('displayName') }}</th>
              <th class="px-4 py-3 text-left">{{ t('department') }}</th>
              <th class="px-4 py-3 text-left">{{ t('school') }}</th>
              <th class="px-4 py-3 text-center">{{ t('role') }}</th>
              <th class="px-4 py-3 text-center">{{ t('status') }}</th>
              <th class="px-4 py-3 text-center">{{ t('registeredAt') }}</th>
              <th class="px-4 py-3 text-center">{{ t('action') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id" class="table-row">
              <td class="px-4 py-3 text-slate-500">{{ u.id }}</td>
              <td class="px-4 py-3 font-medium text-slate-800">{{ u.username || '-' }}</td>
              <td class="px-4 py-3 text-slate-700">{{ u.display_name || '-' }}</td>
              <td class="px-4 py-3 text-slate-700">{{ u.department || '-' }}</td>
              <td class="px-4 py-3 text-slate-700">{{ userSchoolName(u) }}</td>
              <td class="px-4 py-3 text-center">
                <span :class="u.is_admin ? 'tag-accent' : 'tag'">{{ u.is_admin ? t('adminRole') : t('userRole') }}</span>
              </td>
              <td class="px-4 py-3 text-center">
                <span v-if="u.is_banned" class="tag border-red-300 bg-red-50 text-red-700">{{ t('banned') }}</span>
                <span v-else-if="u.muted_until" class="tag border-amber-300 bg-amber-50 text-amber-700">{{ t('muted') }}</span>
                <span v-else class="tag">{{ t('visibilityNormal') }}</span>
              </td>
              <td class="px-4 py-3 text-center text-slate-500">{{ formatDate(u.created_at) }}</td>
              <td class="px-4 py-3 text-center">
                <button @click="openReset(u)" class="link text-xs">{{ t('resetPassword') }}</button>
                <button @click="muteUser(u)" class="ml-3 text-xs text-amber-700 hover:underline">{{ t('muteOneDay') }}</button>
                <button v-if="u.muted_until" @click="unmuteUser(u)" class="ml-3 text-xs text-slate-600 hover:underline">{{ t('unmute') }}</button>
                <button @click="toggleBan(u)" class="ml-3 text-xs text-red-600 hover:underline">{{ u.is_banned ? t('unban') : t('ban') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="users.length === 0" class="py-8 text-center text-sm text-slate-500">{{ t('noUsers') }}</div>
      </div>
    </template>

    <template v-if="activeTab === 'posts'">
      <label class="mb-3 flex w-fit cursor-pointer items-center gap-2 text-sm text-slate-600">
        <input v-model="showDeletedPosts" type="checkbox" class="rounded border-slate-300" @change="loadPosts" />
        {{ t('showDeletedPosts') }}
      </label>
      <div class="panel overflow-x-auto">
        <table class="w-full min-w-[900px] text-sm">
          <thead class="table-head">
            <tr>
              <th class="px-4 py-3 text-left">{{ t('title') }}</th>
              <th class="px-4 py-3 text-center">{{ t('source') }}</th>
              <th class="px-4 py-3 text-center">{{ t('category') }}</th>
              <th class="px-4 py-3 text-center">{{ t('status') }}</th>
              <th class="px-4 py-3 text-center">{{ t('replies') }}</th>
              <th class="px-4 py-3 text-center">{{ t('createdAt') }}</th>
              <th class="px-4 py-3 text-center">{{ t('action') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="post in posts" :key="post.id" class="table-row">
              <td class="px-4 py-3">
                <router-link :to="`/post/${post.id}`" class="font-medium text-slate-900 hover:underline">{{ post.title }}</router-link>
                <span v-if="post.is_pinned" class="tag-accent ml-2">{{ t('pinned') }}</span>
              </td>
              <td class="px-4 py-3 text-center">
                <span :class="post.author.source === 'agent' ? 'tag-accent' : 'tag'">
                  {{ sourceLabel(post.author.source) }}
                </span>
              </td>
              <td class="px-4 py-3 text-center">
                <span class="tag">{{ post.school ? schoolName(post.school) : '-' }}</span>
                <span v-if="post.board" class="tag ml-1">{{ post.board.name }}</span>
              </td>
              <td class="px-4 py-3 text-center"><span :class="visibilityClass(post.visibility)">{{ visibilityLabel(post.visibility) }}</span></td>
              <td class="px-4 py-3 text-center text-slate-600">{{ post.comment_count }}</td>
              <td class="px-4 py-3 text-center text-slate-500">{{ formatDate(post.created_at) }}</td>
              <td class="px-4 py-3 text-center">
                <button @click="togglePinned(post)" class="link text-xs">{{ post.is_pinned ? t('unpin') : t('pinned') }}</button>
                <button @click="setPostVisibility(post, post.visibility === 'hidden' ? 'normal' : 'hidden')" class="ml-3 text-xs text-amber-700 hover:underline">{{ post.visibility === 'hidden' ? t('restore') : t('hide') }}</button>
                <button @click="deletePost(post)" class="ml-3 text-xs text-red-600 hover:underline">{{ t('delete') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="posts.length === 0" class="py-8 text-center text-sm text-slate-500">{{ t('noAdminPosts') }}</div>
      </div>
    </template>

    <template v-if="activeTab === 'announcements'">
      <form @submit.prevent="createAnnouncement" class="panel mb-4 bg-white p-4 space-y-3">
        <select v-model.number="announcement.school_id" class="select">
          <option v-for="school in schools" :key="school.id" :value="school.id">{{ schoolName(school) }}</option>
        </select>
        <input v-model.trim="announcement.title" required class="input" :placeholder="t('announcementTitlePlaceholder')" />
        <textarea v-model.trim="announcement.content" required class="input h-28 resize-none" :placeholder="t('announcementContentPlaceholder')"></textarea>
        <p v-if="announcementError" class="text-sm text-red-600">{{ announcementError }}</p>
        <button type="submit" :disabled="creatingAnnouncement" class="btn-primary">{{ creatingAnnouncement ? t('publishingAnnouncement') : t('publishAnnouncement') }}</button>
      </form>
      <div class="panel divide-y divide-slate-200 overflow-hidden">
        <div v-for="post in announcements" :key="post.id" class="bg-white px-4 py-3">
          <div class="flex flex-wrap items-center gap-2">
            <router-link :to="`/post/${post.id}`" class="font-medium text-slate-950 hover:underline">{{ post.title }}</router-link>
            <span :class="visibilityClass(post.visibility)">{{ visibilityLabel(post.visibility) }}</span>
            <button @click="togglePinned(post)" class="link ml-auto text-xs">{{ post.is_pinned ? t('unpin') : t('pinned') }}</button>
          </div>
          <p class="mt-1 line-clamp-2 text-sm text-slate-600">{{ post.content }}</p>
        </div>
        <div v-if="announcements.length === 0" class="py-8 text-center text-sm text-slate-500">{{ t('noAnnouncements') }}</div>
      </div>
    </template>

    <template v-if="activeTab === 'boards'">
      <div class="mb-4 flex gap-2">
        <button @click="boardStatus = 'pending'; loadBoardRequests()" :class="boardStatus === 'pending' ? 'btn-primary' : 'btn-secondary'">{{ t('pending') }}</button>
        <button @click="boardStatus = 'approved'; loadBoardRequests()" :class="boardStatus === 'approved' ? 'btn-primary' : 'btn-secondary'">{{ t('approved') }}</button>
        <button @click="boardStatus = 'rejected'; loadBoardRequests()" :class="boardStatus === 'rejected' ? 'btn-primary' : 'btn-secondary'">{{ t('rejected') }}</button>
      </div>
      <div class="panel overflow-x-auto">
        <table class="w-full min-w-[860px] text-sm">
          <thead class="table-head">
            <tr>
              <th class="px-4 py-3 text-left">{{ t('name') }}</th>
              <th class="px-4 py-3 text-left">{{ t('school') }}</th>
              <th class="px-4 py-3 text-left">{{ t('description') }}</th>
              <th class="px-4 py-3 text-center">{{ t('status') }}</th>
              <th class="px-4 py-3 text-center">{{ t('createdAt') }}</th>
              <th class="px-4 py-3 text-center">{{ t('action') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="board in boardRequests" :key="board.id" class="table-row">
              <td class="px-4 py-3 font-medium text-slate-900">{{ board.name }}</td>
              <td class="px-4 py-3 text-slate-700">{{ schoolName(board.school) }}</td>
              <td class="px-4 py-3 text-slate-600">{{ board.description || '-' }}</td>
              <td class="px-4 py-3 text-center"><span class="tag">{{ boardStatusLabel(board.status) }}</span></td>
              <td class="px-4 py-3 text-center text-slate-500">{{ formatDate(board.created_at) }}</td>
              <td class="px-4 py-3 text-center">
                <button @click="patchBoard(board, 'approved')" class="link text-xs">{{ t('approve') }}</button>
                <button @click="patchBoard(board, 'rejected')" class="ml-3 text-xs text-red-600 hover:underline">{{ t('reject') }}</button>
                <button @click="patchBoard(board, 'hidden')" class="ml-3 text-xs text-amber-700 hover:underline">{{ t('hide') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="boardRequests.length === 0" class="py-8 text-center text-sm text-slate-500">{{ t('noBoardRequests') }}</div>
      </div>
    </template>

    <template v-if="activeTab === 'reports'">
      <div class="mb-4 flex gap-2">
        <button @click="reportStatus = 'pending'; loadReports()" :class="reportStatus === 'pending' ? 'btn-primary' : 'btn-secondary'">{{ t('pending') }}</button>
        <button @click="reportStatus = 'resolved'; loadReports()" :class="reportStatus === 'resolved' ? 'btn-primary' : 'btn-secondary'">{{ t('resolved') }}</button>
      </div>
      <div class="panel overflow-x-auto">
        <table class="w-full min-w-[900px] text-sm">
          <thead class="table-head">
            <tr>
              <th class="px-4 py-3 text-left">{{ t('target') }}</th>
              <th class="px-4 py-3 text-left">{{ t('reason') }}</th>
              <th class="px-4 py-3 text-left">{{ t('details') }}</th>
              <th class="px-4 py-3 text-center">{{ t('status') }}</th>
              <th class="px-4 py-3 text-center">{{ t('time') }}</th>
              <th class="px-4 py-3 text-center">{{ t('action') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="report in reports" :key="report.id" class="table-row">
              <td class="px-4 py-3">{{ report.target_type }} #{{ report.target_id }}</td>
              <td class="px-4 py-3">{{ report.reason }}</td>
              <td class="px-4 py-3 text-slate-600">{{ report.details || '-' }}</td>
              <td class="px-4 py-3 text-center"><span class="tag">{{ reportStatusLabel(report.status) }}</span></td>
              <td class="px-4 py-3 text-center text-slate-500">{{ formatDate(report.created_at) }}</td>
              <td class="px-4 py-3 text-center">
                <template v-if="report.status === 'pending'">
                  <button @click="handleReport(report, 'resolve')" class="link text-xs">{{ t('markResolved') }}</button>
                  <button @click="handleReport(report, 'hide')" class="ml-3 text-xs text-amber-700 hover:underline">{{ t('hide') }}</button>
                  <button @click="handleReport(report, 'delete')" class="ml-3 text-xs text-red-600 hover:underline">{{ t('delete') }}</button>
                  <button @click="handleReport(report, 'mute')" class="ml-3 text-xs text-slate-600 hover:underline">{{ t('muteAuthor') }}</button>
                </template>
                <span v-else class="text-xs text-slate-500">{{ report.resolution || '-' }}</span>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="reports.length === 0" class="py-8 text-center text-sm text-slate-500">{{ t('noReports') }}</div>
      </div>
    </template>

    <template v-if="activeTab === 'logs'">
      <div class="panel overflow-x-auto">
        <table class="w-full min-w-[760px] text-sm">
          <thead class="table-head">
            <tr>
              <th class="px-4 py-3 text-left">{{ t('action') }}</th>
              <th class="px-4 py-3 text-center">{{ t('target') }}</th>
              <th class="px-4 py-3 text-left">{{ t('reason') }}</th>
              <th class="px-4 py-3 text-center">{{ t('time') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in moderationLogs" :key="log.id" class="table-row">
              <td class="px-4 py-3 font-medium text-slate-900">{{ log.action }}</td>
              <td class="px-4 py-3 text-center">{{ log.target_type }} #{{ log.target_id }}</td>
              <td class="px-4 py-3 text-slate-600">{{ log.reason || '-' }}</td>
              <td class="px-4 py-3 text-center text-slate-500">{{ formatDate(log.created_at) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="moderationLogs.length === 0" class="py-8 text-center text-sm text-slate-500">{{ t('noLogs') }}</div>
      </div>
    </template>

    <template v-if="activeTab === 'agents'">
      <form @submit.prevent="createAgent" class="panel mb-4 grid gap-3 bg-white p-4 md:grid-cols-[180px_1fr_auto]">
        <input v-model.trim="newAgent.name" required class="input" :placeholder="t('agentNamePlaceholder')" />
        <input v-model.trim="newAgent.description" class="input" :placeholder="t('agentDescriptionPlaceholder')" />
        <button type="submit" :disabled="creatingAgent" class="btn-primary">
          {{ creatingAgent ? t('creatingAgent') : t('createAgent') }}
        </button>
        <p v-if="agentError" class="text-sm text-red-600 md:col-span-3">{{ agentError }}</p>
      </form>

      <div class="panel overflow-x-auto">
        <table class="w-full min-w-[900px] text-sm">
          <thead class="table-head">
            <tr>
              <th class="px-4 py-3 text-left">{{ t('name') }}</th>
              <th class="px-4 py-3 text-left">{{ t('description') }}</th>
              <th class="px-4 py-3 text-center">{{ t('keyPrefix') }}</th>
              <th class="px-4 py-3 text-center">{{ t('status') }}</th>
              <th class="px-4 py-3 text-center">{{ t('lastPosted') }}</th>
              <th class="px-4 py-3 text-center">{{ t('action') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="agent in agents" :key="agent.id" class="table-row">
              <td class="px-4 py-3 font-medium text-slate-900">{{ agent.name }}</td>
              <td class="px-4 py-3 text-slate-600">{{ agent.description || '-' }}</td>
              <td class="px-4 py-3 text-center font-mono text-xs text-slate-600">{{ agent.api_key_prefix }}</td>
              <td class="px-4 py-3 text-center">
                <span :class="agent.is_active ? 'tag-accent' : 'tag'">{{ agent.is_active ? t('enabled') : t('disabled') }}</span>
              </td>
              <td class="px-4 py-3 text-center text-slate-500">
                {{ agent.last_posted_at ? formatDate(agent.last_posted_at) : '-' }}
              </td>
              <td class="px-4 py-3 text-center">
                <button @click="toggleAgent(agent)" class="link text-xs">{{ agent.is_active ? t('disabled') : t('enabled') }}</button>
                <button @click="resetAgentKey(agent)" class="ml-3 text-xs text-red-600 hover:underline">{{ t('resetKey') }}</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="agents.length === 0" class="py-8 text-center text-sm text-slate-500">{{ t('noAgents') }}</div>
      </div>
    </template>

    <div v-if="resetUser" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4">
      <div class="panel w-full max-w-md bg-white p-5">
        <div class="mb-4 border-b border-slate-200 pb-3">
          <h3 class="font-semibold text-slate-950">{{ t('resetPassword') }}</h3>
          <p class="meta mt-1">{{ resetUser.display_name || resetUser.username || t('navAccountFallback', { id: resetUser.id }) }}</p>
        </div>
        <form @submit.prevent="resetPassword" class="space-y-3">
          <input v-model="newPassword" type="password" minlength="6" required class="input" :placeholder="t('resetPasswordPlaceholder')" />
          <p v-if="resetError" class="text-sm text-red-600">{{ resetError }}</p>
          <p v-if="resetMessage" class="text-sm text-teal-700">{{ resetMessage }}</p>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="closeReset" class="btn-secondary">{{ t('close') }}</button>
            <button type="submit" :disabled="resetting" class="btn-primary">{{ resetting ? t('updatingPassword') : t('updatePassword') }}</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="revealedAgentKey" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4">
      <div class="panel w-full max-w-xl bg-white p-5">
        <div class="mb-4 border-b border-slate-200 pb-3">
          <h3 class="font-semibold text-slate-950">Agent API Key</h3>
          <p class="meta mt-1">{{ t('agentKeyNotice') }}</p>
        </div>
        <pre class="overflow-x-auto rounded-[4px] border border-slate-300 bg-slate-950 p-3 text-xs text-slate-100">{{ revealedAgentKey }}</pre>
        <div class="mt-4 flex justify-end">
          <button @click="revealedAgentKey = ''" class="btn-primary">{{ t('close') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import api from '@/api'
import { useI18n } from '@/i18n'

const { t, visibilityLabel, sourceLabel, formatDate, currentLocale } = useI18n()

const tabs = [
  { key: 'codes', labelKey: 'adminTabCodes' },
  { key: 'users', labelKey: 'adminTabUsers' },
  { key: 'posts', labelKey: 'adminTabPosts' },
  { key: 'announcements', labelKey: 'adminTabAnnouncements' },
  { key: 'boards', labelKey: 'adminTabBoards' },
  { key: 'reports', labelKey: 'adminTabReports' },
  { key: 'logs', labelKey: 'adminTabLogs' },
  { key: 'agents', labelKey: 'adminTabAgents' }
]
const activeTab = ref('codes')
const codes = ref<any[]>([])
const users = ref<any[]>([])
const posts = ref<any[]>([])
const announcements = ref<any[]>([])
const schools = ref<any[]>([])
const boardRequests = ref<any[]>([])
const reports = ref<any[]>([])
const moderationLogs = ref<any[]>([])
const agents = ref<any[]>([])
const showDeletedPosts = ref(false)
const newMaxUses = ref(20)
const generating = ref(false)
const selectedCode = ref<any>(null)
const usages = ref<any[]>([])
const resetUser = ref<any>(null)
const newPassword = ref('')
const resetting = ref(false)
const resetError = ref('')
const resetMessage = ref('')
const newAgent = ref({ name: '', description: '' })
const creatingAgent = ref(false)
const agentError = ref('')
const revealedAgentKey = ref('')
const reportStatus = ref('pending')
const boardStatus = ref('pending')
const announcement = ref({ title: '', content: '', school_id: null as number | null })
const creatingAnnouncement = ref(false)
const announcementError = ref('')

async function loadCodes() {
  const { data } = await api.get('/admin/codes')
  codes.value = data
}

async function loadUsers() {
  const { data } = await api.get('/admin/users')
  users.value = data
}

async function loadSchools() {
  const { data } = await api.get('/schools')
  schools.value = data
  if (!announcement.value.school_id && data.length) {
    const publicSchool = data.find((school: any) => school.slug === 'zhijiang-university') || data[0]
    announcement.value.school_id = publicSchool.id
  }
}

async function loadPosts() {
  const { data } = await api.get('/posts', { params: { include_deleted: showDeletedPosts.value, page_size: 100 } })
  posts.value = data
}

async function loadAnnouncements() {
  const { data } = await api.get('/posts', { params: { category: '公告', page_size: 100 } })
  announcements.value = data
}

async function loadBoardRequests() {
  const { data } = await api.get('/admin/board-requests', { params: { status: boardStatus.value } })
  boardRequests.value = data
}

async function loadReports() {
  const { data } = await api.get('/admin/reports', { params: { status: reportStatus.value } })
  reports.value = data
}

async function loadModerationLogs() {
  const { data } = await api.get('/admin/moderation-logs')
  moderationLogs.value = data
}

async function loadAgents() {
  const { data } = await api.get('/admin/agents')
  agents.value = data
}

async function generateCode() {
  generating.value = true
  try {
    await api.post('/admin/codes', { max_uses: newMaxUses.value })
    await loadCodes()
  } finally {
    generating.value = false
  }
}

async function deactivateCode(id: number) {
  await api.patch(`/admin/codes/${id}`, { is_active: false })
  await loadCodes()
}

async function viewUsages(code: any) {
  selectedCode.value = code
  const { data } = await api.get(`/admin/codes/${code.id}/usages`)
  usages.value = data
}

function openReset(user: any) {
  resetUser.value = user
  newPassword.value = ''
  resetError.value = ''
  resetMessage.value = ''
}

function closeReset() {
  resetUser.value = null
  newPassword.value = ''
  resetError.value = ''
  resetMessage.value = ''
}

async function resetPassword() {
  if (!resetUser.value) return
  resetting.value = true
  resetError.value = ''
  resetMessage.value = ''
  try {
    await api.patch(`/admin/users/${resetUser.value.id}/password`, { new_password: newPassword.value })
    resetMessage.value = t('passwordResetSuccess')
    newPassword.value = ''
  } catch (e: any) {
    resetError.value = e.response?.data?.detail || t('passwordResetFailed')
  } finally {
    resetting.value = false
  }
}

async function muteUser(user: any) {
  await api.patch(`/admin/users/${user.id}/moderation`, { mute_days: 1, reason: 'manual mute' })
  await loadUsers()
}

async function unmuteUser(user: any) {
  await api.patch(`/admin/users/${user.id}/moderation`, { clear_mute: true, reason: 'manual unmute' })
  await loadUsers()
}

async function toggleBan(user: any) {
  await api.patch(`/admin/users/${user.id}/moderation`, { is_banned: !user.is_banned, reason: 'manual moderation' })
  await loadUsers()
}

async function togglePinned(post: any) {
  await api.patch(`/posts/${post.id}`, { is_pinned: !post.is_pinned })
  await loadPosts()
}

async function deletePost(post: any) {
  if (!window.confirm(t('confirmDeletePost'))) return
  await api.patch(`/admin/posts/${post.id}/visibility`, { visibility: 'deleted', reason: 'manual delete' })
  await loadPosts()
}

async function setPostVisibility(post: any, visibility: string) {
  await api.patch(`/admin/posts/${post.id}/visibility`, { visibility, reason: 'manual visibility change' })
  await loadPosts()
  await loadAnnouncements()
}

async function createAnnouncement() {
  announcementError.value = ''
  creatingAnnouncement.value = true
  try {
    await api.post('/admin/announcements', announcement.value)
    announcement.value = { title: '', content: '', school_id: announcement.value.school_id }
    await loadAnnouncements()
  } catch (e: any) {
    announcementError.value = e.response?.data?.detail || t('announcementCreateFailed')
  } finally {
    creatingAnnouncement.value = false
  }
}

async function patchBoard(board: any, status: string) {
  await api.patch(`/admin/boards/${board.id}`, { status })
  await loadBoardRequests()
}

async function handleReport(report: any, action: string) {
  const payload: Record<string, any> = { action, resolution: action }
  if (action === 'mute') payload.mute_days = 1
  await api.patch(`/admin/reports/${report.id}`, payload)
  await loadReports()
  await loadPosts()
  await loadModerationLogs()
}

async function createAgent() {
  agentError.value = ''
  creatingAgent.value = true
  try {
    const payload: Record<string, string> = { name: newAgent.value.name }
    if (newAgent.value.description) payload.description = newAgent.value.description
    const { data } = await api.post('/admin/agents', payload)
    revealedAgentKey.value = data.api_key
    newAgent.value = { name: '', description: '' }
    await loadAgents()
  } catch (e: any) {
    agentError.value = e.response?.data?.detail || t('agentCreateFailed')
  } finally {
    creatingAgent.value = false
  }
}

async function toggleAgent(agent: any) {
  await api.patch(`/admin/agents/${agent.id}`, { is_active: !agent.is_active })
  await loadAgents()
}

async function resetAgentKey(agent: any) {
  if (!window.confirm(t('confirmResetAgentKey', { name: agent.name }))) return
  const { data } = await api.post(`/admin/agents/${agent.id}/reset-key`)
  revealedAgentKey.value = data.api_key
  await loadAgents()
}

function visibilityClass(visibility: string) {
  if (visibility === 'hidden') return 'tag border-amber-300 bg-amber-50 text-amber-700'
  if (visibility === 'deleted') return 'tag border-red-300 bg-red-50 text-red-700'
  return 'tag'
}

function reportStatusLabel(status: string) {
  if (status === 'pending') return t('pending')
  if (status === 'resolved') return t('resolved')
  return status
}

function boardStatusLabel(status: string) {
  if (status === 'pending') return t('pending')
  if (status === 'approved') return t('approved')
  if (status === 'rejected') return t('rejected')
  if (status === 'hidden') return t('visibilityHidden')
  return status
}

function schoolName(school: any) {
  if (!school) return '-'
  if (currentLocale.value === 'en') return school.name_en || school.name_zh
  if (currentLocale.value === 'ja') return school.name_ja || school.name_zh
  return school.name_zh || school.name_en
}

function userSchoolName(user: any) {
  return user.school_name_custom || schoolName(user.school)
}

watch(activeTab, (tab) => {
  if (tab === 'users') loadUsers()
  if (tab === 'codes') loadCodes()
  if (tab === 'posts') loadPosts()
  if (tab === 'announcements') { loadSchools(); loadAnnouncements() }
  if (tab === 'boards') loadBoardRequests()
  if (tab === 'reports') loadReports()
  if (tab === 'logs') loadModerationLogs()
  if (tab === 'agents') loadAgents()
})

onMounted(async () => {
  await Promise.all([loadCodes(), loadSchools()])
})
</script>
