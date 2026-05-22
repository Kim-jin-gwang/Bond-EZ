<script setup>
import { riskContent } from '../../../data/guide/risk'
</script>

<template>
  <article class="guide-article">
    <p class="eyebrow">{{ riskContent.eyebrow }}</p>
    <h1>{{ riskContent.title }}</h1>
    <div class="description-content">
      <p v-for="(line, index) in riskContent.description.split('\n')" :key="index">
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
