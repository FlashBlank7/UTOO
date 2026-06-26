<template>
  <div class="sticker-picker" ref="pickerRoot">
    <button type="button" class="btn-secondary sticker-picker__trigger" @click="open = !open">
      Yutoko
    </button>

    <div v-if="open" class="sticker-picker__panel">
      <button
        v-for="sticker in yutokoStickers"
        :key="sticker.code"
        type="button"
        class="sticker-picker__item"
        :title="sticker.label"
        @click="selectSticker(sticker.code)"
      >
        <img :src="sticker.src" :alt="sticker.label" loading="lazy" />
        <span>{{ sticker.label }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { yutokoStickers } from '@/stickers/yutoko'

const emit = defineEmits<{ select: [code: string] }>()
const open = ref(false)
const pickerRoot = ref<HTMLElement | null>(null)

function selectSticker(code: string) {
  emit('select', code)
  open.value = false
}

function onDocumentClick(event: MouseEvent) {
  if (!open.value || !pickerRoot.value) return
  if (!pickerRoot.value.contains(event.target as Node)) open.value = false
}

onMounted(() => document.addEventListener('click', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocumentClick))
</script>

<style scoped>
.sticker-picker {
  position: relative;
  display: inline-flex;
}

.sticker-picker__trigger {
  padding-inline: 0.7rem;
}

.sticker-picker__panel {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  z-index: 70;
  display: grid;
  width: min(340px, calc(100vw - 32px));
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 6px;
  border: 1px solid rgb(203 213 225);
  border-radius: 6px;
  background: rgb(255 255 255);
  padding: 8px;
  box-shadow: 0 18px 40px rgb(15 23 42 / 0.18);
}

.sticker-picker__item {
  display: grid;
  min-width: 0;
  gap: 4px;
  border: 1px solid rgb(226 232 240);
  border-radius: 5px;
  background: rgb(248 250 252);
  padding: 5px;
  text-align: center;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.sticker-picker__item:hover {
  border-color: rgb(14 165 233);
  background: rgb(240 249 255);
}

.sticker-picker__item img {
  aspect-ratio: 1;
  width: 100%;
  object-fit: contain;
}

.sticker-picker__item span {
  overflow: hidden;
  color: rgb(51 65 85);
  font-size: 11px;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 520px) {
  .sticker-picker__panel {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    width: min(220px, calc(100vw - 32px));
  }
}
</style>
