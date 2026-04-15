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
  highlightModel: {
    type: String,
    default: '',
  },
})
</script>

<template>
  <div class="table-box">
    <table>
      <thead>
        <tr>
          <th v-for="column in columns" :key="column">{{ column }}</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, index) in rows"
          :key="row['模型'] || row['月份'] || index"
          :class="{ highlight: row['模型'] === highlightModel }"
        >
          <td v-for="column in columns" :key="column">
            {{ row[column] }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
