<script setup>
defineProps({
  columns: {
    type: Array,
    default: () => [],
  },
  rows: {
    type: Array,
    default: () => [],
  },
})
</script>

<template>
  <div class="indicator-table-wrap">
    <table class="indicator-data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column">{{ column }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.join('-')">
          <td v-for="cell in row" :key="cell">{{ cell }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.indicator-table-wrap {
  overflow-x: visible;
}

.indicator-data-table {
  width: 100%;
  min-width: 0;
  table-layout: fixed;
  border-collapse: collapse;
}

.indicator-data-table th,
.indicator-data-table td {
  padding: 13px 14px;
  border: 1px solid var(--line);
  text-align: left;
  word-break: keep-all;
}

.indicator-data-table th {
  color: var(--text);
  background: #f5f8fb;
  font-size: 13px;
  font-weight: 900;
}

.indicator-data-table td {
  font-size: 14px;
}
</style>
