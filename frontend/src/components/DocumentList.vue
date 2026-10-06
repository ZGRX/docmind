<script setup>
defineProps({ documents: { type: Array, required: true }, compact: Boolean });
const formatDate = (value) => new Date(value).toLocaleDateString("zh-CN");
</script>

<template>
  <div v-if="!documents.length" class="empty-state">
    还没有文档，上传一份资料开始吧。
  </div>
  <div v-else class="document-list">
    <div v-for="doc in documents" :key="doc.id" class="document-row">
      <div class="file-icon" :class="doc.file_type">
        {{ doc.file_type.toUpperCase() }}
      </div>
      <div class="document-info">
        <strong :title="doc.file_name">{{ doc.file_name }}</strong
        ><span
          >{{ formatDate(doc.created_at) }} · {{ doc.chunk_count }} 个片段</span
        >
      </div>
      <span v-if="!compact" class="file-type">{{
        doc.file_type.toUpperCase()
      }}</span>
      <slot name="action" :document="doc" />
    </div>
  </div>
</template>
