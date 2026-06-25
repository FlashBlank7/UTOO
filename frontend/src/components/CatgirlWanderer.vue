<template>
  <div
    v-if="canRender"
    ref="rootEl"
    class="mascot-companion"
    :class="{
      'mascot-companion--ready': ready,
      'mascot-companion--dragging': dragging,
      'mascot-companion--fallback': usingFallback,
      'mascot-companion--live2d': live2dReady,
      'mascot-companion--reduced': reducedMotion
    }"
    :style="positionStyle"
    @pointermove="focusLive2D"
  >
    <div v-if="message" class="mascot-companion__bubble" aria-live="polite">
      <span class="mascot-companion__label">{{ currentOutfit.label }}</span>
      {{ message }}
    </div>

    <div
      ref="dragEl"
      class="mascot-companion__body"
      role="button"
      tabindex="0"
      :aria-label="companionLabel"
      @click="reactToClick"
      @keydown.enter.prevent="reactToClick"
      @keydown.space.prevent="reactToClick"
      @pointerdown="startDrag"
    >
      <div
        ref="live2dHost"
        class="mascot-companion__live2d"
        :class="{ 'mascot-companion__live2d--visible': live2dReady && !usingFallback }"
        aria-hidden="true"
      ></div>

      <img
        v-if="usingFallback"
        class="mascot-companion__fallback"
        :src="currentOutfit.image || neutralMascotImage"
        alt=""
        draggable="false"
      />

      <span v-if="loadState === 'loading'" class="mascot-companion__status">Live2D</span>
    </div>

    <div class="mascot-companion__tools">
      <button
        type="button"
        class="mascot-companion__tool"
        :title="live2dDisabled ? '启用 Live2D' : '关闭 Live2D'"
        :aria-label="live2dDisabled ? '启用 Live2D' : '关闭 Live2D'"
        @click="toggleLive2D"
      >
        {{ live2dDisabled ? '2D' : 'PNG' }}
      </button>
      <button
        type="button"
        class="mascot-companion__tool"
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
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { mascotOutfits, neutralMascotImage } from '@/assets/mascot/manifest'

type LoadState = 'idle' | 'loading' | 'ready' | 'fallback'

const MODEL_URL = '/live2d/utoo-neko/model.model3.json'
const CUBISM_CORE_URL = '/live2d/runtime/live2dcubismcore.min.js'
const storageKey = 'utoo_mascot_hidden'
const live2dDisabledKey = 'utoo_live2d_disabled'
const positionKey = 'utoo_mascot_position'
const dayOverrideKey = 'utoo_mascot_day'

const route = useRoute()
const rootEl = ref<HTMLElement | null>(null)
const dragEl = ref<HTMLElement | null>(null)
const live2dHost = ref<HTMLElement | null>(null)
const ready = ref(false)
const hidden = ref(false)
const message = ref('')
const reducedMotion = ref(false)
const live2dDisabled = ref(false)
const live2dReady = ref(false)
const loadState = ref<LoadState>('idle')
const position = ref({ x: 0, y: 0 })
const dragging = ref(false)

let mediaQuery: MediaQueryList | undefined
let bubbleTimer: number | undefined
let idleTimer: number | undefined
let loadTimer: number | undefined
let live2dApp: any
let live2dModel: any
let dragStart: { pointerId: number; x: number; y: number; originX: number; originY: number; moved: boolean } | null = null

const routeMessages: Record<string, string[]> = {
  home: ['索引巡检完成', '我在右下角值班', '公告区优先级最高', '搜索结果已同步'],
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

const clickMessages = ['收到，继续值班', '不要戳太快，我在上班', '今天穿的是：', 'Live2D 插槽已准备好']

const currentOutfit = computed(() => {
  const weekday = readOutfitDay()
  return mascotOutfits.find((outfit) => outfit.weekday === weekday) ?? mascotOutfits[1]
})

const canRender = computed(() => !hidden.value && canAppear())
const usingFallback = computed(() => live2dDisabled.value || !live2dReady.value)
const companionLabel = computed(() => `UTOO 常驻看板娘，${currentOutfit.value.theme}`)
const positionStyle = computed(() => ({
  transform: `translate3d(${Math.round(position.value.x)}px, ${Math.round(position.value.y)}px, 0)`
}))

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
  const line = lines[Math.floor(Math.random() * lines.length)] || '值班中'
  return line === '今天穿的是：' ? `${line}${currentOutfit.value.theme}` : line
}

function updateReducedMotion() {
  reducedMotion.value = Boolean(mediaQuery?.matches)
}

function readQueryFlags() {
  const params = new URLSearchParams(window.location.search)
  if (params.get('mascot') === 'show') window.localStorage.removeItem(storageKey)
  if (params.get('mascot') === 'hide') window.localStorage.setItem(storageKey, '1')
  if (params.get('live2d') === 'off') window.localStorage.setItem(live2dDisabledKey, '1')
  if (params.get('live2d') === 'on') window.localStorage.removeItem(live2dDisabledKey)
}

function initPosition() {
  const saved = readStoredPosition()
  const size = getCompanionSize()
  if (saved) {
    position.value = clampPosition(saved.x, saved.y, size)
    return
  }
  position.value = clampPosition(
    window.innerWidth - size.width - 24,
    window.innerHeight - size.height - 20,
    size
  )
}

function getCompanionSize() {
  const mobile = window.innerWidth <= 640
  return {
    width: mobile ? 165 : 270,
    height: mobile ? 230 : 350
  }
}

function readStoredPosition() {
  try {
    const raw = window.localStorage.getItem(positionKey)
    if (!raw) return null
    const data = JSON.parse(raw) as { x?: number; y?: number }
    if (typeof data.x !== 'number' || typeof data.y !== 'number') return null
    return { x: data.x, y: data.y }
  } catch {
    return null
  }
}

function storePosition() {
  window.localStorage.setItem(positionKey, JSON.stringify(position.value))
}

function clampPosition(x: number, y: number, size = getCompanionSize()) {
  const margin = 8
  return {
    x: Math.min(Math.max(margin, x), Math.max(margin, window.innerWidth - size.width - margin)),
    y: Math.min(Math.max(margin, y), Math.max(margin, window.innerHeight - size.height - margin))
  }
}

function showMessage(text: string, duration = 5200) {
  message.value = text
  window.clearTimeout(bubbleTimer)
  bubbleTimer = window.setTimeout(() => {
    message.value = ''
    scheduleIdleMessage()
  }, duration)
}

function scheduleIdleMessage() {
  window.clearTimeout(idleTimer)
  if (!canAppear() || hidden.value) return
  idleTimer = window.setTimeout(() => {
    showMessage(pickLine(routeMessages[routeContext()]), 4600)
  }, 26000 + Math.random() * 28000)
}

function react(messageText?: string) {
  if (!canAppear() || hidden.value) return
  showMessage(messageText || pickLine(routeMessages[routeContext()]))
  playLive2DReaction()
}

function reactToClick() {
  if (dragStart?.moved) return
  react(pickLine(clickMessages))
}

function hideMascot() {
  hidden.value = true
  window.localStorage.setItem(storageKey, '1')
  disposeLive2D()
  window.clearTimeout(bubbleTimer)
  window.clearTimeout(idleTimer)
}

function toggleLive2D() {
  live2dDisabled.value = !live2dDisabled.value
  if (live2dDisabled.value) {
    window.localStorage.setItem(live2dDisabledKey, '1')
    disposeLive2D()
    loadState.value = 'fallback'
    showMessage('已切换到 PNG 模式')
  } else {
    window.localStorage.removeItem(live2dDisabledKey)
    showMessage('正在尝试加载 Live2D')
    scheduleLive2DLoad(150)
  }
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

function startDrag(event: PointerEvent) {
  if (!dragEl.value) return
  dragStart = {
    pointerId: event.pointerId,
    x: event.clientX,
    y: event.clientY,
    originX: position.value.x,
    originY: position.value.y,
    moved: false
  }
  dragging.value = true
  dragEl.value.setPointerCapture(event.pointerId)
  window.addEventListener('pointermove', dragMove)
  window.addEventListener('pointerup', endDrag)
  window.addEventListener('pointercancel', endDrag)
}

function dragMove(event: PointerEvent) {
  if (!dragStart || event.pointerId !== dragStart.pointerId) return
  const dx = event.clientX - dragStart.x
  const dy = event.clientY - dragStart.y
  if (Math.abs(dx) + Math.abs(dy) > 6) dragStart.moved = true
  position.value = clampPosition(dragStart.originX + dx, dragStart.originY + dy)
}

function endDrag(event: PointerEvent) {
  if (dragStart && event.pointerId === dragStart.pointerId) {
    storePosition()
    window.setTimeout(() => {
      dragStart = null
    }, 0)
  }
  dragging.value = false
  window.removeEventListener('pointermove', dragMove)
  window.removeEventListener('pointerup', endDrag)
  window.removeEventListener('pointercancel', endDrag)
}

function handleResize() {
  position.value = clampPosition(position.value.x, position.value.y)
  resizeLive2D()
}

function scheduleLive2DLoad(delay = 900) {
  window.clearTimeout(loadTimer)
  if (live2dDisabled.value || reducedMotion.value || !canAppear()) {
    loadState.value = 'fallback'
    return
  }
  loadTimer = window.setTimeout(loadLive2D, delay)
}

async function loadLive2D() {
  if (!live2dHost.value || live2dDisabled.value || live2dReady.value) return
  loadState.value = 'loading'

  try {
    if (!isWebGLAvailable()) throw new Error('WebGL is not available')
    const modelInfo = await fetchModelInfo()
    if (modelInfo?.UTOOPlaceholder) throw new Error('Live2D model placeholder is active')

    await loadScriptOnce(CUBISM_CORE_URL, 'utoo-cubism-core')
    const [{ Application, Ticker }, { Live2DModel }] = await Promise.all([
      import('pixi.js'),
      import('pixi-live2d-display/cubism4')
    ])

    Live2DModel.registerTicker(Ticker)
    live2dApp = new Application({
      width: getLive2DCanvasSize().width,
      height: getLive2DCanvasSize().height,
      backgroundAlpha: 0,
      antialias: true,
      autoDensity: true,
      resolution: Math.min(window.devicePixelRatio || 1, 2)
    })

    live2dHost.value.innerHTML = ''
    live2dHost.value.appendChild(live2dApp.view as HTMLCanvasElement)
    live2dModel = await Live2DModel.from(MODEL_URL, { autoInteract: false })
    live2dModel.anchor.set(0.5, 1)
    fitLive2DModel()
    live2dApp.stage.addChild(live2dModel)
    live2dReady.value = true
    loadState.value = 'ready'
    showMessage('Live2D 已就绪')
  } catch (error) {
    console.info('[UTOO mascot] Live2D fallback:', error)
    disposeLive2D()
    loadState.value = 'fallback'
    live2dReady.value = false
  }
}

async function fetchModelInfo() {
  const response = await fetch(MODEL_URL, { cache: 'no-cache' })
  if (!response.ok) throw new Error(`model not found: ${response.status}`)
  return response.json()
}

function isWebGLAvailable() {
  const canvas = document.createElement('canvas')
  return Boolean(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
}

function loadScriptOnce(src: string, id: string) {
  if (document.getElementById(id)) return Promise.resolve()
  return new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    script.id = id
    script.src = src
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error(`failed to load ${src}`))
    document.head.appendChild(script)
  })
}

function getLive2DCanvasSize() {
  const mobile = window.innerWidth <= 640
  return {
    width: mobile ? 140 : 240,
    height: mobile ? 205 : 330
  }
}

function resizeLive2D() {
  if (!live2dApp?.renderer) return
  const size = getLive2DCanvasSize()
  live2dApp.renderer.resize(size.width, size.height)
  fitLive2DModel()
}

function fitLive2DModel() {
  if (!live2dApp || !live2dModel) return
  const size = getLive2DCanvasSize()
  const bounds = live2dModel.getLocalBounds?.()
  const width = Math.max(1, bounds?.width || live2dModel.width || 1)
  const height = Math.max(1, bounds?.height || live2dModel.height || 1)
  const scale = Math.min(size.width / width, size.height / height) * 0.92
  live2dModel.scale.set(scale)
  live2dModel.x = size.width / 2
  live2dModel.y = size.height
}

function focusLive2D(event: PointerEvent) {
  if (!live2dReady.value || !live2dModel?.focus || reducedMotion.value) return
  const rect = rootEl.value?.getBoundingClientRect()
  if (!rect) return
  const x = ((event.clientX - rect.left) / rect.width - 0.5) * 2
  const y = ((event.clientY - rect.top) / rect.height - 0.5) * -2
  live2dModel.focus(Math.max(-1, Math.min(1, x)), Math.max(-1, Math.min(1, y)))
}

function playLive2DReaction() {
  if (!live2dReady.value || !live2dModel?.motion) return
  live2dModel.motion('TapBody').catch(() => {
    live2dModel.motion('Idle').catch(() => undefined)
  })
}

function disposeLive2D() {
  live2dReady.value = false
  if (live2dModel?.destroy) live2dModel.destroy()
  if (live2dApp?.destroy) live2dApp.destroy(true, { children: true, texture: true, baseTexture: true })
  live2dModel = undefined
  live2dApp = undefined
  if (live2dHost.value) live2dHost.value.innerHTML = ''
}

onMounted(async () => {
  readQueryFlags()
  hidden.value = window.localStorage.getItem(storageKey) === '1'
  live2dDisabled.value = window.localStorage.getItem(live2dDisabledKey) === '1'
  mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  updateReducedMotion()
  mediaQuery.addEventListener?.('change', updateReducedMotion)
  window.addEventListener('utoo:mascot-react', handleMascotEvent)
  window.addEventListener('resize', handleResize)
  initPosition()
  await nextTick()
  ready.value = true
  showMessage(pickLine(routeMessages[routeContext()]), 4800)
  scheduleLive2DLoad()
})

onBeforeUnmount(() => {
  window.clearTimeout(bubbleTimer)
  window.clearTimeout(idleTimer)
  window.clearTimeout(loadTimer)
  mediaQuery?.removeEventListener?.('change', updateReducedMotion)
  window.removeEventListener('utoo:mascot-react', handleMascotEvent)
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('pointermove', dragMove)
  window.removeEventListener('pointerup', endDrag)
  window.removeEventListener('pointercancel', endDrag)
  disposeLive2D()
})

watch(() => route.path, () => {
  if (!canAppear()) return
  showMessage(pickLine(routeMessages[routeContext()]), 4200)
  scheduleLive2DLoad(250)
})
</script>

<style scoped>
.mascot-companion {
  pointer-events: none;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 35;
  width: 270px;
  height: 350px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  grid-template-rows: 1fr;
  align-items: end;
  gap: 6px 8px;
  opacity: 0;
  transition: opacity 120ms ease;
  will-change: transform;
}

.mascot-companion--ready {
  opacity: 1;
}

.mascot-companion--dragging {
  transition: none;
}

.mascot-companion__bubble {
  pointer-events: auto;
  position: absolute;
  right: 36px;
  bottom: 268px;
  max-width: min(240px, calc(100vw - 120px));
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

.mascot-companion__body {
  pointer-events: auto;
  position: relative;
  grid-column: 1 / 2;
  width: 220px;
  height: 320px;
  cursor: grab;
  touch-action: none;
  user-select: none;
  outline: none;
  filter: drop-shadow(0 10px 16px rgba(15, 23, 42, 0.16));
}

.mascot-companion--dragging .mascot-companion__body {
  cursor: grabbing;
}

.mascot-companion__body:focus-visible {
  border-radius: 6px;
  box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.22);
}

.mascot-companion__live2d {
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 180ms ease;
}

.mascot-companion__live2d--visible {
  opacity: 1;
}

.mascot-companion__live2d :deep(canvas) {
  display: block;
  width: 100%;
  height: 100%;
}

.mascot-companion__fallback {
  position: absolute;
  right: 10px;
  bottom: 0;
  display: block;
  width: 160px;
  height: auto;
  user-select: none;
  animation: mascot-breathe 4.8s ease-in-out infinite;
}

.mascot-companion__status {
  position: absolute;
  right: 8px;
  bottom: 12px;
  border: 1px solid #0f766e;
  background: rgba(204, 251, 241, 0.88);
  color: #115e59;
  border-radius: 4px;
  padding: 1px 5px;
  font-size: 10px;
  font-weight: 700;
}

.mascot-companion__tools {
  pointer-events: auto;
  grid-column: 2 / 3;
  display: grid;
  gap: 5px;
  align-self: end;
  padding-bottom: 28px;
  opacity: 0;
  transition: opacity 150ms ease;
}

.mascot-companion:hover .mascot-companion__tools,
.mascot-companion__tools:focus-within {
  opacity: 1;
}

.mascot-companion__tool {
  display: grid;
  min-width: 28px;
  height: 24px;
  place-items: center;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.92);
  color: #475569;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}

.mascot-companion__tool:hover {
  background: #f1f5f9;
  color: #0f172a;
}

@keyframes mascot-breathe {
  0%,
  100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-3px) scale(1.01);
  }
}

@media (max-width: 640px) {
  .mascot-companion {
    width: 165px;
    height: 230px;
    gap: 4px 5px;
  }

  .mascot-companion__body {
    width: 125px;
    height: 205px;
  }

  .mascot-companion__fallback {
    right: 3px;
    width: 96px;
  }

  .mascot-companion__bubble {
    right: 28px;
    bottom: 168px;
    max-width: min(210px, calc(100vw - 52px));
    font-size: 11px;
  }

  .mascot-companion__tools {
    padding-bottom: 22px;
    opacity: 0.9;
  }
}

@media (prefers-reduced-motion: reduce) {
  .mascot-companion,
  .mascot-companion__live2d,
  .mascot-companion__tools {
    transition: none;
  }

  .mascot-companion__fallback {
    animation: none;
  }
}
</style>
