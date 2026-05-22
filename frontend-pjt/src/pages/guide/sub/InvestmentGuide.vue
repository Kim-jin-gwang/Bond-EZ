<script setup>
import { guideContent } from '../../../data/guide/guide'
</script>

<template>
  <article class="guide-article">
    <p class="eyebrow">{{ guideContent.eyebrow }}</p>
    <h1>{{ guideContent.title }}</h1>
    <div class="description-content">
      <p v-for="(line, index) in guideContent.description.split('\n')" :key="index">
        {{ line }}
      </p>
    </div>
  </article>
</template>

<style scoped>
.description-content {
  margin-top: 24px;
  line-height: 1.8;
  color: var(--text);
}
.description-content p {
  margin-bottom: 12px;
}
</style>
