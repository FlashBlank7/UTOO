<template>
  <div
    v-if="visible"
    class="catgirl-wanderer"
    :class="{ 'catgirl-wanderer--reduced': reducedMotion }"
    :style="{ '--cat-y': `${positionY}px`, '--cat-duration': `${durationMs}ms` }"
    aria-hidden="true"
  >
    <div v-if="message" class="catgirl-wanderer__bubble">{{ message }}</div>
    <div class="catgirl-wanderer__body">
      <span class="catgirl-wanderer__ear catgirl-wanderer__ear--left"></span>
      <span class="catgirl-wanderer__ear catgirl-wanderer__ear--right"></span>
      <span class="catgirl-wanderer__hair"></span>
      <span class="catgirl-wanderer__face">
        <span class="catgirl-wanderer__eye"></span>
        <span class="catgirl-wanderer__eye"></span>
        <span class="catgirl-wanderer__mouth"></span>
      </span>
      <span class="catgirl-wanderer__tail"></span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const visible = ref(false)
const message = ref('')
const positionY = ref(260)
const durationMs = ref(10500)
const reducedMotion = ref(false)
let timer: number | undefined

const messages = [
  '巡逻中',
  '这里有新帖',
  '保持队形',
  '已读完索引',
  '今天也冷静'
]

function canAppear() {
  return route.path === '/' || route.path.startsWith('/post/')
}

function schedule(delay = 9000) {
  window.clearTimeout(timer)
  if (!canAppear()) return
  timer = window.setTimeout(showOnce, delay)
}

function showOnce() {
  if (!canAppear()) return
  reducedMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  positionY.value = Math.max(180, Math.min(window.innerHeight - 160, Math.round(window.innerHeight * 0.58)))
  message.value = messages[Math.floor(Math.random() * messages.length)]
  durationMs.value = reducedMotion.value ? 3200 : 10500
  visible.value = true
  window.setTimeout(() => {
    visible.value = false
    schedule(26000 + Math.random() * 26000)
  }, durationMs.value)
}

onMounted(() => schedule(7000))
onBeforeUnmount(() => window.clearTimeout(timer))
watch(() => route.path, () => {
  visible.value = false
  schedule(9000)
})
</script>

<style scoped>
.catgirl-wanderer {
  --cat-y: 260px;
  --cat-duration: 10500ms;
  pointer-events: none;
  position: fixed;
  left: -96px;
  top: var(--cat-y);
  z-index: 30;
  display: flex;
  align-items: end;
  gap: 8px;
  animation: catgirl-walk var(--cat-duration) linear forwards;
}

.catgirl-wanderer--reduced {
  left: auto;
  right: 18px;
  animation: catgirl-reduced var(--cat-duration) ease-in-out forwards;
}

.catgirl-wanderer__bubble {
  margin-bottom: 48px;
  border: 1px solid #cbd5e1;
  background: rgba(255, 255, 255, 0.94);
  color: #334155;
  border-radius: 4px;
  padding: 5px 8px;
  font-size: 12px;
  white-space: nowrap;
  box-shadow: 0 1px 0 rgba(15, 23, 42, 0.04);
}

.catgirl-wanderer__body {
  position: relative;
  width: 52px;
  height: 62px;
  border: 2px solid #0f172a;
  border-radius: 12px 12px 18px 18px;
  background: linear-gradient(#f8fafc, #dbeafe);
}

.catgirl-wanderer__ear {
  position: absolute;
  top: -13px;
  width: 18px;
  height: 18px;
  border: 2px solid #0f172a;
  background: #f8fafc;
  transform: rotate(45deg);
}

.catgirl-wanderer__ear--left {
  left: 6px;
}

.catgirl-wanderer__ear--right {
  right: 6px;
}

.catgirl-wanderer__hair {
  position: absolute;
  left: 9px;
  top: 9px;
  width: 34px;
  height: 16px;
  border-radius: 10px 10px 6px 6px;
  background: #334155;
}

.catgirl-wanderer__face {
  position: absolute;
  left: 9px;
  top: 23px;
  display: grid;
  width: 34px;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.catgirl-wanderer__eye {
  width: 5px;
  height: 5px;
  border-radius: 999px;
  background: #0f172a;
  justify-self: center;
}

.catgirl-wanderer__mouth {
  grid-column: 1 / 3;
  justify-self: center;
  width: 12px;
  height: 5px;
  border-bottom: 2px solid #0f172a;
  border-radius: 0 0 12px 12px;
}

.catgirl-wanderer__tail {
  position: absolute;
  right: -20px;
  bottom: 10px;
  width: 24px;
  height: 34px;
  border-right: 3px solid #0f172a;
  border-bottom: 3px solid #0f172a;
  border-radius: 0 0 18px 0;
}

@keyframes catgirl-walk {
  0% {
    transform: translateX(0);
    opacity: 0;
  }
  10%,
  80% {
    opacity: 1;
  }
  100% {
    transform: translateX(calc(100vw + 160px));
    opacity: 0;
  }
}

@keyframes catgirl-reduced {
  0%,
  100% {
    opacity: 0;
  }
  20%,
  80% {
    opacity: 0.9;
  }
}
</style>
