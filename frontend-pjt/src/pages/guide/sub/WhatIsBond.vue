<script setup>
import { whatContent } from '../../../data/guide/what'
</script>

<template>
  <article class="guide-article">
    <p class="eyebrow">{{ whatContent.eyebrow }}</p>
    <h1>{{ whatContent.title }}</h1>
    <div class="description-content">
      <p v-for="(line, index) in whatContent.description.split('\n')" :key="index">
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
