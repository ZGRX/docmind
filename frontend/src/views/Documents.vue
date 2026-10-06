<script setup>
import { onMounted, ref } from "vue";
import { useDocumentsStore } from "../stores/documents";
import DocumentList from "../components/DocumentList.vue";
import { errorMessage } from "../api/client";

const store = useDocumentsStore();
const uploading = ref(false);
const error = ref("");
const input = ref(null);
onMounted(store.load);

async function upload(event) {
  const files = Array.from(event.target.files || []);
  if (!files.length) return;
  uploading.value = true;
  error.value = "";
  try {
    for (const file of files) await store.upload(file);
  } catch (err) {
    error.value = errorMessage(err);
  } finally {
    uploading.value = false;
    event.target.value = "";
  }
}

async function remove(doc) {
  if (!window.confirm(`删除「${doc.file_name}」及其向量数据？`)) return;
  error.value = "";
  try {
    await store.remove(doc.id);
  } catch (err) {
    error.value = errorMessage(err);
  }
}
</script>

<template>
  <div class="page">
    <div class="eyebrow">KNOWLEDGE LIBRARY</div>
    <div class="page-heading">
      <div>
        <h1>文档管理<span class="heading-dot">.</span></h1>
        <p>为你的学习资料建立一个可检索的知识库。</p>
      </div>
      <button
        class="button primary"
        :disabled="uploading"
        @click="input.click()"
      >
        {{ uploading ? "正在处理…" : "＋ 上传文档" }}
      </button>
    </div>
    <input
      ref="input"
      class="visually-hidden"
      type="file"
      accept=".pdf,.txt,.md,.markdown"
      multiple
      @change="upload"
    />
    <div v-if="error || store.error" class="alert">
      {{ error || store.error }}
    </div>
    <div class="upload-hint">
      <span>↥</span>
      <div>
        <strong>支持 PDF / TXT / Markdown</strong>
        <p>单个文件最大 15 MB。上传后自动提取文本、生成向量并加入知识库。</p>
      </div>
    </div>
    <section class="panel">
      <div class="panel-heading">
        <div>
          <span class="eyebrow">YOUR FILES</span>
          <h2>
            全部文档 <em>{{ store.items.length }}</em>
          </h2>
        </div>
      </div>
      <div v-if="store.loading" class="empty-state">加载中…</div>
      <DocumentList v-else :documents="store.items"
        ><template #action="{ document }"
          ><button
            class="icon-button danger"
            :aria-label="`删除 ${document.file_name}`"
            @click="remove(document)"
          >
            删除
          </button></template
        ></DocumentList
      >
    </section>
  </div>
</template>
