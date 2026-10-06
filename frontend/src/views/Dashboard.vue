<script setup>
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { api, errorMessage } from "../api/client";
import DocumentList from "../components/DocumentList.vue";

const stats = ref({
  document_count: 0,
  chunk_count: 0,
  conversation_count: 0,
  recent_documents: [],
});
const error = ref("");
onMounted(async () => {
  try {
    stats.value = (await api.get("/dashboard/stats")).data;
  } catch (err) {
    error.value = errorMessage(err);
  }
});
</script>

<template>
  <div class="page dashboard-page">
    <div class="eyebrow">YOUR KNOWLEDGE, ORGANIZED</div>
    <div class="page-heading">
      <div>
        <h1>学习工作台<span class="heading-dot">.</span></h1>
        <p>上传资料，建立自己的知识库，然后开始提问。</p>
      </div>
      <RouterLink to="/chat" class="button primary"
        >开始提问 <span>↗</span></RouterLink
      >
    </div>
    <div v-if="error" class="alert">{{ error }}</div>
    <div class="stats-grid">
      <div class="stat-card">
        <span class="stat-icon blue">▤</span
        ><span class="stat-label">知识文档</span
        ><strong>{{ stats.document_count }}</strong
        ><small>已收录的学习资料</small>
      </div>
      <div class="stat-card">
        <span class="stat-icon purple">◈</span
        ><span class="stat-label">知识片段</span
        ><strong>{{ stats.chunk_count }}</strong
        ><small>可被检索的文本块</small>
      </div>
      <div class="stat-card">
        <span class="stat-icon green">✧</span
        ><span class="stat-label">历史会话</span
        ><strong>{{ stats.conversation_count }}</strong
        ><small>已保存的问答记录</small>
      </div>
    </div>
    <div class="dashboard-grid">
      <section class="panel">
        <div class="panel-heading">
          <div>
            <span class="eyebrow">RECENT FILES</span>
            <h2>最近上传</h2>
          </div>
          <RouterLink to="/documents" class="text-link">查看全部 ↗</RouterLink>
        </div>
        <DocumentList :documents="stats.recent_documents" compact />
      </section>
      <section class="panel quick-panel">
        <span class="eyebrow">GET STARTED</span>
        <h2>从资料到答案</h2>
        <p>
          PDF、TXT、Markdown
          都能加入知识库。系统会提取并切分内容，优先从你的资料里寻找答案。
        </p>
        <div class="step-line"><span>01</span> 上传文档</div>
        <div class="step-line"><span>02</span> 检索相关片段</div>
        <div class="step-line"><span>03</span> 获得带引用的回答</div>
        <RouterLink to="/documents" class="button secondary"
          >管理文档 →</RouterLink
        >
      </section>
    </div>
  </div>
</template>
