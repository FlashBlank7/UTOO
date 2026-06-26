<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <nav class="bg-white border-b border-slate-200 px-4 py-3">
      <div class="mx-auto flex max-w-5xl items-center justify-between">
        <router-link to="/" class="text-lg font-semibold tracking-[0.08em] text-slate-950">UTOO</router-link>
        <div class="flex items-center gap-4 text-sm">
          <template v-if="auth.isLoggedIn">
            <router-link to="/account" class="text-slate-600 hover:text-slate-950">{{ auth.displayName }}</router-link>
            <router-link v-if="auth.isAdmin" to="/admin" class="link">{{ t('navAdmin') }}</router-link>
            <button @click="auth.logout(); $router.push('/')" class="text-slate-500 hover:text-slate-950">{{ t('logout') }}</button>
          </template>
          <template v-else>
            <router-link to="/login" class="link">{{ t('login') }}</router-link>
            <router-link to="/register" class="link">{{ t('register') }}</router-link>
          </template>
          <select
            :value="currentLocale"
            class="border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700 rounded-[4px] focus:outline-none focus:ring-2 focus:ring-teal-600/20"
            aria-label="Language"
            @change="handleLocaleChange"
          >
            <option v-for="option in localeOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </div>
      </div>
    </nav>
    <router-view />
    <CatgirlWanderer />
  </div>
</template>

<script setup lang="ts">
import CatgirlWanderer from '@/components/CatgirlWanderer.vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n, type Locale } from '@/i18n'
const auth = useAuthStore()
const { currentLocale, localeOptions, setLocale, t } = useI18n()

function handleLocaleChange(event: Event) {
  const next = (event.target as HTMLSelectElement).value
  if (next === 'zh' || next === 'en' || next === 'ja') setLocale(next as Locale)
}
</script>
