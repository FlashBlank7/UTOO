<template>
  <span class="sticker-text" :class="sizeClass">
    <template v-for="(part, index) in parts" :key="`${part.type}-${index}`">
      <span v-if="part.type === 'text'">{{ part.text }}</span>
      <img
        v-else
        class="sticker-text__image"
        :src="part.src"
        :alt="part.label"
        :title="part.label"
        loading="lazy"
      />
    </template>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { parseStickerText } from '@/stickers/yutoko'

const props = withDefaults(defineProps<{ text: string; size?: 'normal' | 'small' }>(), {
  size: 'normal'
})

const parts = computed(() => parseStickerText(props.text))
const sizeClass = computed(() => props.size === 'small' ? 'sticker-text--small' : 'sticker-text--normal')
</script>

<style scoped>
.sticker-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.sticker-text__image {
  display: inline-block;
  height: 112px;
  width: 112px;
  max-width: min(112px, 46vw);
  object-fit: contain;
  vertical-align: middle;
}

.sticker-text--small .sticker-text__image {
  height: 88px;
  width: 88px;
  max-width: min(88px, 40vw);
}
</style>
