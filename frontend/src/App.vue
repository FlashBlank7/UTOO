<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
      <router-link to="/" class="text-lg font-bold text-indigo-600">UTOO</router-link>
      <div class="flex items-center gap-4 text-sm">
        <template v-if="auth.isLoggedIn">
          <span class="text-gray-500">{{ auth.user?.username || '匿名' }}</span>
          <router-link v-if="auth.isAdmin" to="/admin" class="text-indigo-500 hover:underline">管理</router-link>
          <button @click="auth.logout(); $router.push('/')" class="text-gray-400 hover:text-gray-600">退出</button>
        </template>
        <template v-else>
          <router-link to="/login" class="text-indigo-500 hover:underline">登录</router-link>
          <router-link to="/register" class="text-indigo-500 hover:underline">注册</router-link>
        </template>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
</script>
