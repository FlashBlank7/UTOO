<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <nav class="bg-white border-b border-slate-200 px-4 py-3">
      <div class="mx-auto flex max-w-5xl items-center justify-between">
        <router-link to="/" class="text-lg font-semibold tracking-[0.08em] text-slate-950">UTOO</router-link>
        <div class="flex items-center gap-4 text-sm">
        <template v-if="auth.isLoggedIn">
          <router-link to="/account" class="text-slate-600 hover:text-slate-950">{{ auth.displayName }}</router-link>
          <router-link v-if="auth.isAdmin" to="/admin" class="link">管理</router-link>
          <button @click="auth.logout(); $router.push('/')" class="text-slate-500 hover:text-slate-950">退出</button>
        </template>
        <template v-else>
          <router-link to="/login" class="link">登录</router-link>
          <router-link to="/register" class="link">注册</router-link>
        </template>
        </div>
      </div>
    </nav>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
</script>
