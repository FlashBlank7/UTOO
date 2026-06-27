<template>
  <PostDetailPanel :post-id="postId" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import PostDetailPanel from '@/components/PostDetailPanel.vue'

const route = useRoute()
const postId = computed(() => route.params.id as string)
</script>
