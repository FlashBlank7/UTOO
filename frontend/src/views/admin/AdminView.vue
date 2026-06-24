<template>
  <div class="mx-auto max-w-6xl px-4 py-8">
    <div class="mb-6 border-b border-slate-200 pb-5">
      <p class="meta mb-1">Admin</p>
      <h1 class="text-2xl font-semibold text-slate-950">管理后台</h1>
    </div>

    <div class="mb-6 flex gap-1 border-b border-slate-200">
      <button
        v-for="t in tabs"
        :key="t.key"
        @click="activeTab = t.key"
        :class="[
          'border-b-2 px-3 py-2 text-sm font-medium transition-colors',
          activeTab === t.key
            ? 'border-slate-950 text-slate-950'
            : 'border-transparent text-slate-500 hover:text-slate-900'
        ]"
      >
        {{ t.label }}
      </button>
    </div>

    <template v-if="activeTab === 'codes'">
      <div class="mb-4 flex flex-wrap items-center gap-3">
        <input v-model.number="newMaxUses" type="number" min="1" class="input w-32" placeholder="上限" />
        <button @click="generateCode" :disabled="generating" class="btn-primary">
          {{ generating ? '生成中...' : '生成激活码' }}
        </button>
      </div>
      <div class="panel overflow-x-auto">
        <table class="w-full min-w-[760px] text-sm">
          <thead class="table-head">
            <tr>
              <th class="px-4 py-3 text-left">激活码</th>
              <th class="px-4 py-3 text-center">已用 / 上限</th>
              <th class="px-4 py-3 text-center">状态</th>
              <th class="px-4 py-3 text-center">创建时间</th>
              <th class="px-4 py-3 text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="code in codes" :key="code.id" class="table-row">
              <td class="px-4 py-3 font-mono font-semibold text-slate-800">{{ code.code }}</td>
              <td class="px-4 py-3 text-center">{{ code.use_count }} / {{ code.max_uses }}</td>
              <td class="px-4 py-3 text-center">
                <span :class="code.is_active ? 'tag-accent' : 'tag'">{{ code.is_active ? '有效' : '已停用' }}</span>
              </td>
              <td class="px-4 py-3 text-center text-slate-500">{{ formatDate(code.created_at) }}</td>
              <td class="px-4 py-3 text-center">
                <button v-if="code.is_active" @click="deactivateCode(code.id)" class="text-xs text-red-600 hover:underline">停用</button>
                <button @click="viewUsages(code)" class="link ml-3 text-xs">查看用户</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="codes.length === 0" class="py-8 text-center text-sm text-slate-500">暂无激活码</div>
      </div>

      <div v-if="selectedCode" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4">
        <div class="panel w-full max-w-md bg-white p-5">
          <div class="mb-4 flex items-center justify-between border-b border-slate-200 pb-3">
            <h3 class="font-semibold text-slate-950">{{ selectedCode.code }} 注册用户</h3>
            <button @click="selectedCode = null" class="text-sm text-slate-500 hover:text-slate-950">关闭</button>
          </div>
          <div v-if="usages.length === 0" class="py-4 text-center text-sm text-slate-500">暂无用户</div>
          <ul v-else class="space-y-2 text-sm">
            <li v-for="u in usages" :key="u.user_id" class="flex justify-between gap-3 text-slate-700">
              <span>{{ u.display_name || u.username || `用户${u.user_id}` }} · {{ u.department }}</span>
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
              <th class="px-4 py-3 text-left">ID</th>
              <th class="px-4 py-3 text-left">用户名</th>
              <th class="px-4 py-3 text-left">昵称</th>
              <th class="px-4 py-3 text-left">专攻</th>
              <th class="px-4 py-3 text-center">角色</th>
              <th class="px-4 py-3 text-center">注册时间</th>
              <th class="px-4 py-3 text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id" class="table-row">
              <td class="px-4 py-3 text-slate-500">{{ u.id }}</td>
              <td class="px-4 py-3 font-medium text-slate-800">{{ u.username || '-' }}</td>
              <td class="px-4 py-3 text-slate-700">{{ u.display_name || '-' }}</td>
              <td class="px-4 py-3 text-slate-700">{{ u.department }}</td>
              <td class="px-4 py-3 text-center">
                <span :class="u.is_admin ? 'tag-accent' : 'tag'">{{ u.is_admin ? '管理员' : '用户' }}</span>
              </td>
              <td class="px-4 py-3 text-center text-slate-500">{{ formatDate(u.created_at) }}</td>
              <td class="px-4 py-3 text-center">
                <button @click="openReset(u)" class="link text-xs">重置密码</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="users.length === 0" class="py-8 text-center text-sm text-slate-500">暂无用户</div>
      </div>
    </template>

    <template v-if="activeTab === 'posts'">
      <div class="panel overflow-x-auto">
        <table class="w-full min-w-[900px] text-sm">
          <thead class="table-head">
            <tr>
              <th class="px-4 py-3 text-left">标题</th>
              <th class="px-4 py-3 text-center">来源</th>
              <th class="px-4 py-3 text-center">分类</th>
              <th class="px-4 py-3 text-center">回复</th>
              <th class="px-4 py-3 text-center">创建时间</th>
              <th class="px-4 py-3 text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="post in posts" :key="post.id" class="table-row">
              <td class="px-4 py-3">
                <router-link :to="`/post/${post.id}`" class="font-medium text-slate-900 hover:underline">{{ post.title }}</router-link>
                <span v-if="post.is_pinned" class="tag-accent ml-2">置顶</span>
              </td>
              <td class="px-4 py-3 text-center">
                <span :class="post.author.source === 'agent' ? 'tag-accent' : 'tag'">
                  {{ post.author.source === 'agent' ? 'Agent' : '用户' }}
                </span>
              </td>
              <td class="px-4 py-3 text-center"><span class="tag">{{ post.category }}</span></td>
              <td class="px-4 py-3 text-center text-slate-600">{{ post.comment_count }}</td>
              <td class="px-4 py-3 text-center text-slate-500">{{ formatDate(post.created_at) }}</td>
              <td class="px-4 py-3 text-center">
                <button @click="togglePinned(post)" class="link text-xs">{{ post.is_pinned ? '取消置顶' : '置顶' }}</button>
                <button @click="deletePost(post)" class="ml-3 text-xs text-red-600 hover:underline">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="posts.length === 0" class="py-8 text-center text-sm text-slate-500">暂无帖子</div>
      </div>
    </template>

    <template v-if="activeTab === 'agents'">
      <form @submit.prevent="createAgent" class="panel mb-4 grid gap-3 bg-white p-4 md:grid-cols-[180px_1fr_auto]">
        <input v-model.trim="newAgent.name" required class="input" placeholder="Agent 名称" />
        <input v-model.trim="newAgent.description" class="input" placeholder="说明（可选）" />
        <button type="submit" :disabled="creatingAgent" class="btn-primary">
          {{ creatingAgent ? '创建中...' : '创建 Agent' }}
        </button>
        <p v-if="agentError" class="text-sm text-red-600 md:col-span-3">{{ agentError }}</p>
      </form>

      <div class="panel overflow-x-auto">
        <table class="w-full min-w-[900px] text-sm">
          <thead class="table-head">
            <tr>
              <th class="px-4 py-3 text-left">名称</th>
              <th class="px-4 py-3 text-left">说明</th>
              <th class="px-4 py-3 text-center">Key Prefix</th>
              <th class="px-4 py-3 text-center">状态</th>
              <th class="px-4 py-3 text-center">最近发帖</th>
              <th class="px-4 py-3 text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="agent in agents" :key="agent.id" class="table-row">
              <td class="px-4 py-3 font-medium text-slate-900">{{ agent.name }}</td>
              <td class="px-4 py-3 text-slate-600">{{ agent.description || '-' }}</td>
              <td class="px-4 py-3 text-center font-mono text-xs text-slate-600">{{ agent.api_key_prefix }}</td>
              <td class="px-4 py-3 text-center">
                <span :class="agent.is_active ? 'tag-accent' : 'tag'">{{ agent.is_active ? '启用' : '停用' }}</span>
              </td>
              <td class="px-4 py-3 text-center text-slate-500">
                {{ agent.last_posted_at ? formatDate(agent.last_posted_at) : '-' }}
              </td>
              <td class="px-4 py-3 text-center">
                <button @click="toggleAgent(agent)" class="link text-xs">{{ agent.is_active ? '停用' : '启用' }}</button>
                <button @click="resetAgentKey(agent)" class="ml-3 text-xs text-red-600 hover:underline">重置 Key</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="agents.length === 0" class="py-8 text-center text-sm text-slate-500">暂无 Agent</div>
      </div>
    </template>

    <div v-if="resetUser" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4">
      <div class="panel w-full max-w-md bg-white p-5">
        <div class="mb-4 border-b border-slate-200 pb-3">
          <h3 class="font-semibold text-slate-950">重置密码</h3>
          <p class="meta mt-1">{{ resetUser.display_name || resetUser.username || `用户${resetUser.id}` }}</p>
        </div>
        <form @submit.prevent="resetPassword" class="space-y-3">
          <input v-model="newPassword" type="password" minlength="6" required class="input" placeholder="新密码，至少 6 位" />
          <p v-if="resetError" class="text-sm text-red-600">{{ resetError }}</p>
          <p v-if="resetMessage" class="text-sm text-teal-700">{{ resetMessage }}</p>
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="closeReset" class="btn-secondary">关闭</button>
            <button type="submit" :disabled="resetting" class="btn-primary">{{ resetting ? '更新中...' : '更新密码' }}</button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="revealedAgentKey" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 px-4">
      <div class="panel w-full max-w-xl bg-white p-5">
        <div class="mb-4 border-b border-slate-200 pb-3">
          <h3 class="font-semibold text-slate-950">Agent API Key</h3>
          <p class="meta mt-1">这串 key 只显示一次，关闭后无法再次查看。</p>
        </div>
        <pre class="overflow-x-auto rounded-[4px] border border-slate-300 bg-slate-950 p-3 text-xs text-slate-100">{{ revealedAgentKey }}</pre>
        <div class="mt-4 flex justify-end">
          <button @click="revealedAgentKey = ''" class="btn-primary">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import api from '@/api'

const tabs = [
  { key: 'codes', label: '激活码' },
  { key: 'users', label: '用户' },
  { key: 'posts', label: '内容' },
  { key: 'agents', label: 'Agent' }
]
const activeTab = ref('codes')
const codes = ref<any[]>([])
const users = ref<any[]>([])
const posts = ref<any[]>([])
const agents = ref<any[]>([])
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

async function loadCodes() {
  const { data } = await api.get('/admin/codes')
  codes.value = data
}

async function loadUsers() {
  const { data } = await api.get('/admin/users')
  users.value = data
}

async function loadPosts() {
  const { data } = await api.get('/posts', { params: { page_size: 100 } })
  posts.value = data
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
    resetMessage.value = '密码已更新'
    newPassword.value = ''
  } catch (e: any) {
    resetError.value = e.response?.data?.detail || '更新失败'
  } finally {
    resetting.value = false
  }
}

async function togglePinned(post: any) {
  await api.patch(`/posts/${post.id}`, { is_pinned: !post.is_pinned })
  await loadPosts()
}

async function deletePost(post: any) {
  if (!window.confirm('确认删除这篇帖子？')) return
  await api.delete(`/posts/${post.id}`)
  await loadPosts()
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
    agentError.value = e.response?.data?.detail || '创建失败'
  } finally {
    creatingAgent.value = false
  }
}

async function toggleAgent(agent: any) {
  await api.patch(`/admin/agents/${agent.id}`, { is_active: !agent.is_active })
  await loadAgents()
}

async function resetAgentKey(agent: any) {
  if (!window.confirm(`确认重置 ${agent.name} 的 API Key？旧 key 将立即失效。`)) return
  const { data } = await api.post(`/admin/agents/${agent.id}/reset-key`)
  revealedAgentKey.value = data.api_key
  await loadAgents()
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

watch(activeTab, (tab) => {
  if (tab === 'users') loadUsers()
  if (tab === 'codes') loadCodes()
  if (tab === 'posts') loadPosts()
  if (tab === 'agents') loadAgents()
})

onMounted(loadCodes)
</script>
