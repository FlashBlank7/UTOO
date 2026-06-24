<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <h1 class="text-xl font-bold text-gray-800 mb-6">管理后台</h1>

    <!-- Tabs -->
    <div class="flex gap-4 border-b mb-6">
      <button v-for="t in tabs" :key="t.key" @click="activeTab = t.key"
        :class="['pb-2 text-sm font-medium border-b-2 -mb-px transition', activeTab === t.key ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700']">
        {{ t.label }}
      </button>
    </div>

    <!-- 激活码管理 -->
    <template v-if="activeTab === 'codes'">
      <div class="flex items-center gap-3 mb-4">
        <input v-model.number="newMaxUses" type="number" min="1" class="input w-32" placeholder="上限" />
        <button @click="generateCode" :disabled="generating" class="btn-primary text-sm">
          {{ generating ? '生成中…' : '生成激活码' }}
        </button>
      </div>
      <div class="bg-white rounded-lg border overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-500 text-xs">
            <tr>
              <th class="px-4 py-3 text-left">激活码</th>
              <th class="px-4 py-3 text-center">已用 / 上限</th>
              <th class="px-4 py-3 text-center">状态</th>
              <th class="px-4 py-3 text-center">创建时间</th>
              <th class="px-4 py-3 text-center">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="code in codes" :key="code.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 font-mono font-semibold text-gray-700">{{ code.code }}</td>
              <td class="px-4 py-3 text-center">{{ code.use_count }} / {{ code.max_uses }}</td>
              <td class="px-4 py-3 text-center">
                <span :class="['px-2 py-0.5 rounded-full text-xs', code.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500']">
                  {{ code.is_active ? '有效' : '已停用' }}
                </span>
              </td>
              <td class="px-4 py-3 text-center text-gray-400">{{ formatDate(code.created_at) }}</td>
              <td class="px-4 py-3 text-center">
                <button v-if="code.is_active" @click="deactivateCode(code.id)" class="text-red-400 hover:underline text-xs">停用</button>
                <button @click="viewUsages(code)" class="text-indigo-400 hover:underline text-xs ml-2">查看用户</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-if="codes.length === 0" class="text-center text-gray-400 py-8 text-sm">暂无激活码</div>
      </div>

      <!-- 用户使用详情 Modal -->
      <div v-if="selectedCode" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 px-4">
        <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
          <div class="flex justify-between items-center mb-4">
            <h3 class="font-semibold">{{ selectedCode.code }} 注册用户</h3>
            <button @click="selectedCode = null" class="text-gray-400 hover:text-gray-600">✕</button>
          </div>
          <div v-if="usages.length === 0" class="text-gray-400 text-sm text-center py-4">暂无用户</div>
          <ul v-else class="space-y-2 text-sm">
            <li v-for="u in usages" :key="u.user_id" class="flex justify-between text-gray-700">
              <span>{{ u.display_name || u.username || `用户${u.user_id}` }} · {{ u.department }}</span>
              <span class="text-gray-400">{{ formatDate(u.used_at) }}</span>
            </li>
          </ul>
        </div>
      </div>
    </template>

    <!-- 用户列表 -->
    <template v-if="activeTab === 'users'">
      <div class="bg-white rounded-lg border overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-500 text-xs">
            <tr>
              <th class="px-4 py-3 text-left">ID</th>
              <th class="px-4 py-3 text-left">用户名</th>
              <th class="px-4 py-3 text-left">昵称</th>
              <th class="px-4 py-3 text-left">专攻</th>
              <th class="px-4 py-3 text-center">角色</th>
              <th class="px-4 py-3 text-center">注册时间</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="u in users" :key="u.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 text-gray-400">{{ u.id }}</td>
              <td class="px-4 py-3 font-medium text-gray-700">{{ u.username || '—' }}</td>
              <td class="px-4 py-3 text-gray-600">{{ u.display_name || '—' }}</td>
              <td class="px-4 py-3 text-gray-600">{{ u.department }}</td>
              <td class="px-4 py-3 text-center">
                <span :class="['px-2 py-0.5 rounded-full text-xs', u.is_admin ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-500']">
                  {{ u.is_admin ? '管理员' : '用户' }}
                </span>
              </td>
              <td class="px-4 py-3 text-center text-gray-400">{{ formatDate(u.created_at) }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="users.length === 0" class="text-center text-gray-400 py-8 text-sm">暂无用户</div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import api from '@/api'

const tabs = [
  { key: 'codes', label: '激活码管理' },
  { key: 'users', label: '用户列表' }
]
const activeTab = ref('codes')
const codes = ref<any[]>([])
const users = ref<any[]>([])
const newMaxUses = ref(20)
const generating = ref(false)
const selectedCode = ref<any>(null)
const usages = ref<any[]>([])

async function loadCodes() {
  const { data } = await api.get('/admin/codes')
  codes.value = data
}

async function loadUsers() {
  const { data } = await api.get('/admin/users')
  users.value = data
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

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

watch(activeTab, (tab) => {
  if (tab === 'users') loadUsers()
  if (tab === 'codes') loadCodes()
})

onMounted(loadCodes)
</script>
