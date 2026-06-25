<template>
  <div
    v-if="canRender"
    class="mascot-companion"
    :class="[
      `mascot-companion--${mode}`,
      { 'mascot-companion--visible': visible, 'mascot-companion--reduced': reducedMotion }
    ]"
    :style="{ '--mascot-y': `${positionY}px`, '--mascot-duration': `${durationMs}ms` }"
  >
    <div class="mascot-companion__stage">
      <div v-if="message" class="mascot-companion__bubble" aria-live="polite">
        <span class="mascot-companion__label">{{ currentOutfit.label }}</span>
        {{ message }}
      </div>

      <button
        type="button"
        class="mascot-companion__figure"
        :aria-label="`UTOO 看板娘，${currentOutfit.theme}`"
        @click="reactToClick"
      >
        <img :src="currentOutfit.image || neutralMascotImage" alt="" draggable="false" />
      </button>

      <button
        type="button"
        class="mascot-companion__hide"
        aria-label="隐藏看板娘"
        title="隐藏看板娘"
        @click="hideMascot"
      >
        ×
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { mascotOutfits, neutralMascotImage } from '@/assets/mascot/manifest'

type MascotMode = 'idle' | 'peek' | 'wander' | 'react'

const route = useRoute()
const visible = ref(false)
const hidden = ref(false)
const message = ref('')
const mode = ref<MascotMode>('idle')
const positionY = ref(260)
const durationMs = ref(9000)
const reducedMotion = ref(false)

let timer: number | undefined
let hideTimer: number | undefined
let lastReactionAt = 0
let mediaQuery: MediaQueryList | undefined

const storageKey = 'utoo_mascot_hidden'
const dayOverrideKey = 'utoo_mascot_day'

const routeMessages: Record<string, string[]> = {
  home: ['索引巡检完成', '公告区优先级最高', '搜索结果已同步', '今天也保持冷静阅读'],
  post: ['这串讨论有新线索', '回复前先校准语气', '引用关系已记录', '我在旁边看楼层'],
  login: ['认证入口已就绪', '欢迎回来，先登录', '会话令牌准备中'],
  register: ['新账号登记中', '名字可以短，讨论要长', '注册后就能发帖了']
}

const eventMessages: Record<string, string[]> = {
  'post-created': ['新帖已进入索引', '发布完成，我去巡逻首页'],
  'comment-created': ['回复写入讨论串', '楼层更新完成'],
  'report-sent': ['举报已进入处理队列', '管理员会看到这条线索'],
  'search-applied': ['搜索条件已应用', '我帮你看着结果列表'],
  'empty-list': ['这里暂时没有帖子', '空列表也算一种秩序']
}

const clickMessages = ['收到，继续巡逻', '不要戳太快，我在上班', '今天穿的是：', '索引状态稳定']

const currentOutfit = computed(() => {
  const weekday = readOutfitDay()
  return mascotOutfits.find((outfit) => outfit.weekday === weekday) ?? mascotOutfits[1]
})

const canRender = computed(() => !hidden.value && canAppear())

function canAppear() {
  return route.path === '/' || route.path.startsWith('/post/') || route.path === '/login' || route.path === '/register'
}

function routeContext() {
  if (route.path === '/') return 'home'
  if (route.path.startsWith('/post/')) return 'post'
  if (route.path === '/login') return 'login'
  if (route.path === '/register') return 'register'
  return 'home'
}

function readOutfitDay() {
  const params = new URLSearchParams(window.location.search)
  const raw = params.get('mascotDay') || window.localStorage.getItem(dayOverrideKey)
  if (raw) {
    const normalized = raw.trim().toLowerCase()
    const byName = mascotOutfits.find((outfit) => outfit.id === normalized)
    if (byName) return byName.weekday
    const numeric = Number.parseInt(normalized, 10)
    if (Number.isInteger(numeric) && numeric >= 0 && numeric <= 6) return numeric
  }
  return new Date().getDay()
}

function pickLine(lines: string[]) {
  const line = lines[Math.floor(Math.random() * lines.length)] || '巡逻中'
  return line === '今天穿的是：' ? `${line}${currentOutfit.value.theme}` : line
}

function updateReducedMotion() {
  reducedMotion.value = Boolean(mediaQuery?.matches)
}

function schedule(delay = 9000) {
  window.clearTimeout(timer)
  if (!canAppear() || hidden.value) return
  timer = window.setTimeout(showAmbient, delay)
}

function showAmbient() {
  if (!canAppear() || hidden.value) return
  updateReducedMotion()
  const context = routeContext()
  const isAuthPage = context === 'login' || context === 'register'
  mode.value = reducedMotion.value || isAuthPage ? 'peek' : Math.random() > 0.45 ? 'wander' : 'idle'
  positionY.value = Math.max(170, Math.min(window.innerHeight - 250, Math.round(window.innerHeight * 0.52)))
  durationMs.value = reducedMotion.value ? 5200 : mode.value === 'wander' ? 11500 : 7600
  message.value = pickLine(routeMessages[context])
  visible.value = true

  window.clearTimeout(hideTimer)
  hideTimer = window.setTimeout(() => {
    visible.value = false
    schedule(30000 + Math.random() * 30000)
  }, durationMs.value)
}

function react(messageText?: string) {
  if (!canAppear() || hidden.value) return
  const now = Date.now()
  if (now - lastReactionAt < 2800) return
  lastReactionAt = now
  updateReducedMotion()
  mode.value = reducedMotion.value ? 'peek' : 'react'
  positionY.value = Math.max(170, Math.min(window.innerHeight - 250, Math.round(window.innerHeight * 0.56)))
  durationMs.value = 5200
  message.value = messageText || pickLine(routeMessages[routeContext()])
  visible.value = true
  window.clearTimeout(timer)
  window.clearTimeout(hideTimer)
  hideTimer = window.setTimeout(() => {
    visible.value = false
    schedule(28000 + Math.random() * 24000)
  }, durationMs.value)
}

function reactToClick() {
  react(pickLine(clickMessages))
}

function hideMascot() {
  hidden.value = true
  visible.value = false
  window.localStorage.setItem(storageKey, '1')
  window.clearTimeout(timer)
  window.clearTimeout(hideTimer)
}

function handleMascotEvent(event: Event) {
  const detail = (event as CustomEvent<{ context?: string; message?: string }>).detail
  if (detail?.message) {
    react(detail.message)
    return
  }
  const lines = detail?.context ? eventMessages[detail.context] : null
  if (lines) react(pickLine(lines))
}

onMounted(() => {
  const mascotParam = new URLSearchParams(window.location.search).get('mascot')
  if (mascotParam === 'show') window.localStorage.removeItem(storageKey)
  if (mascotParam === 'hide') window.localStorage.setItem(storageKey, '1')
  hidden.value = window.localStorage.getItem(storageKey) === '1'
  mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  updateReducedMotion()
  mediaQuery.addEventListener?.('change', updateReducedMotion)
  window.addEventListener('utoo:mascot-react', handleMascotEvent)
  schedule(route.path === '/' ? 5500 : 8500)
})

onBeforeUnmount(() => {
  window.clearTimeout(timer)
  window.clearTimeout(hideTimer)
  mediaQuery?.removeEventListener?.('change', updateReducedMotion)
  window.removeEventListener('utoo:mascot-react', handleMascotEvent)
})

watch(() => route.path, () => {
  visible.value = false
  schedule(route.path === '/' ? 5000 : 8500)
})
</script>

<style scoped>
.mascot-companion {
  --mascot-y: 260px;
  --mascot-duration: 9000ms;
  pointer-events: none;
  position: fixed;
  z-index: 35;
  opacity: 0;
}

.mascot-companion--visible {
  opacity: 1;
}

.mascot-companion--wander {
  left: -170px;
  top: var(--mascot-y);
  animation: mascot-wander var(--mascot-duration) linear forwards;
}

.mascot-companion--idle,
.mascot-companion--peek,
.mascot-companion--react {
  bottom: 16px;
  right: max(16px, env(safe-area-inset-right));
}

.mascot-companion--idle {
  animation: mascot-idle var(--mascot-duration) ease-in-out forwards;
}

.mascot-companion--peek {
  animation: mascot-peek var(--mascot-duration) ease-in-out forwards;
}

.mascot-companion--react {
  animation: mascot-react var(--mascot-duration) ease-in-out forwards;
}

.mascot-companion__stage {
  pointer-events: auto;
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 8px;
}

.mascot-companion--idle .mascot-companion__stage,
.mascot-companion--peek .mascot-companion__stage,
.mascot-companion--react .mascot-companion__stage {
  flex-direction: row-reverse;
}

.mascot-companion__figure {
  pointer-events: auto;
  position: relative;
  width: clamp(94px, 11vw, 142px);
  border: 0;
  background: transparent;
  padding: 0;
  cursor: pointer;
  filter: drop-shadow(0 8px 14px rgba(15, 23, 42, 0.16));
  transform-origin: 50% 100%;
}

.mascot-companion__figure:hover {
  transform: translateY(-2px);
}

.mascot-companion__figure img {
  display: block;
  width: 100%;
  height: auto;
  user-select: none;
}

.mascot-companion__bubble {
  max-width: min(220px, calc(100vw - 170px));
  margin-bottom: clamp(54px, 6vw, 78px);
  border: 1px solid #94a3b8;
  background: rgba(248, 250, 252, 0.96);
  color: #0f172a;
  border-radius: 5px;
  padding: 7px 9px;
  font-size: 12px;
  line-height: 1.45;
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
}

.mascot-companion__label {
  margin-right: 6px;
  border: 1px solid #0f766e;
  background: #ccfbf1;
  color: #115e59;
  padding: 0 4px;
  font-size: 10px;
  font-weight: 700;
}

.mascot-companion__hide {
  pointer-events: auto;
  position: absolute;
  right: -4px;
  top: 10px;
  display: grid;
  width: 22px;
  height: 22px;
  place-items: center;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.9);
  color: #475569;
  font-size: 16px;
  line-height: 1;
  opacity: 0;
  transition: opacity 150ms ease, background 150ms ease;
}

.mascot-companion__stage:hover .mascot-companion__hide,
.mascot-companion__hide:focus-visible {
  opacity: 1;
}

.mascot-companion__hide:hover {
  background: #f1f5f9;
  color: #0f172a;
}

@keyframes mascot-wander {
  0% {
    transform: translateX(0) translateY(8px);
    opacity: 0;
  }
  10%,
  82% {
    opacity: 1;
  }
  44% {
    transform: translateX(calc(50vw - 28px)) translateY(0);
  }
  100% {
    transform: translateX(calc(100vw + 210px)) translateY(8px);
    opacity: 0;
  }
}

@keyframes mascot-idle {
  0%,
  100% {
    transform: translateY(18px);
    opacity: 0;
  }
  16%,
  78% {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes mascot-peek {
  0%,
  100% {
    transform: translateY(72px);
    opacity: 0;
  }
  18%,
  78% {
    transform: translateY(28px);
    opacity: 1;
  }
}

@keyframes mascot-react {
  0%,
  100% {
    transform: translateY(20px) scale(0.98);
    opacity: 0;
  }
  18%,
  76% {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
  38% {
    transform: translateY(-5px) scale(1.02);
  }
}

@media (max-width: 640px) {
  .mascot-companion--idle,
  .mascot-companion--peek,
  .mascot-companion--react {
    right: 8px;
    bottom: -18px;
  }

  .mascot-companion--idle .mascot-companion__stage,
  .mascot-companion--peek .mascot-companion__stage,
  .mascot-companion--react .mascot-companion__stage {
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
  }

  .mascot-companion__figure {
    width: 72px;
  }

  .mascot-companion__bubble {
    max-width: min(190px, calc(100vw - 96px));
    margin-right: 8px;
    margin-bottom: 0;
    font-size: 11px;
  }

  .mascot-companion__hide {
    right: -2px;
    top: 38px;
    opacity: 0.9;
  }
}

@media (prefers-reduced-motion: reduce) {
  .mascot-companion,
  .mascot-companion__figure,
  .mascot-companion__hide {
    transition: none;
  }

  .mascot-companion--wander,
  .mascot-companion--idle,
  .mascot-companion--peek,
  .mascot-companion--react {
    animation: mascot-reduced var(--mascot-duration) ease-in-out forwards;
  }
}

@keyframes mascot-reduced {
  0%,
  100% {
    opacity: 0;
  }
  20%,
  78% {
    opacity: 1;
  }
}
</style>
