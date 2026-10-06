<script setup>
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { useDocumentsStore } from "../stores/documents";
import { useChatStore } from "../stores/chat";
import MarkdownMessage from "../components/MarkdownMessage.vue";

const route = useRoute();
const router = useRouter();
const documents = useDocumentsStore();
const chat = useChatStore();
const question = ref("");
const scroller = ref(null);
const hasDocuments = computed(() => documents.items.length > 0);

onMounted(async () => {
  await Promise.all([documents.load(), chat.loadConversations()]);
  if (route.query.id) await chat.openConversation(Number(route.query.id));
});
watch(
  () => route.query.id,
  async (id) => {
    if (id) await chat.openConversation(Number(id));
    else chat.clear();
  },
);
watch(
  () => chat.messages.map((message) => message.content.length).join(","),
  async () => {
    await nextTick();
    if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight;
  },
);

async function send() {
  const text = question.value.trim();
  if (!text || chat.loading) return;
  question.value = "";
  await chat.send(text);
}
function newConversation() {
  chat.clear();
  router.replace("/chat");
}
</script>

<template>
  <div class="chat-layout">
    <aside class="chat-docs">
      <div class="eyebrow">KNOWLEDGE BASE</div>
      <h2>已连接的文档</h2>
      <div class="doc-count">{{ documents.items.length }} 份资料可供检索</div>
      <div class="chat-doc-list">
        <div v-for="doc in documents.items" :key="doc.id" class="chat-doc">
          <span class="mini-file">▤</span
          ><span :title="doc.file_name">{{ doc.file_name }}</span
          ><span class="online-dot"></span>
        </div>
        <p v-if="!hasDocuments" class="muted">尚无文档</p>
      </div>
      <RouterLink to="/documents" class="add-doc-link">＋ 添加资料</RouterLink>
    </aside>
    <section class="chat-main">
      <div class="chat-header">
        <div>
          <span class="eyebrow">AI DOCUMENT CHAT</span>
          <h1>文档问答<span class="heading-dot">.</span></h1>
        </div>
        <button
          class="button ghost"
          title="清空当前聊天窗口，历史会话仍会保存"
          :disabled="chat.loading"
          @click="newConversation"
        >
          清空对话
        </button>
      </div>
      <div ref="scroller" class="message-scroll">
        <div v-if="!chat.messages.length" class="chat-welcome">
          <div class="welcome-icon">✧</div>
          <div class="eyebrow">ASK YOUR DOCUMENTS</div>
          <h2>有什么想了解的？</h2>
          <p>提问后，DocMind 会先查找相关文档片段，再生成附带引用的回答。</p>
          <div class="suggestions">
            <button @click="question = '请总结这些文档的主要内容'">
              总结文档重点 ↗</button
            ><button @click="question = '这些资料中有哪些关键概念？'">
              提取关键概念 ↗
            </button>
          </div>
        </div>
        <div v-else class="messages">
          <div
            v-for="(message, index) in chat.messages"
            :key="index"
            class="message"
            :class="message.role"
          >
            <div class="message-avatar">
              {{ message.role === "user" ? "我" : "✧" }}
            </div>
            <div class="message-content">
              <div class="message-label">
                {{ message.role === "user" ? "YOU" : "DOCMIND" }}
              </div>
              <MarkdownMessage
                :content="message.content || (chat.loading ? '正在思考…' : '')"
              />
              <div v-if="message.sources?.length" class="sources">
                <div class="sources-title">
                  引用来源 · {{ message.sources.length }}
                </div>
                <details
                  v-for="(source, sourceIndex) in message.sources"
                  :key="sourceIndex"
                >
                  <summary>
                    [{{ sourceIndex + 1 }}] {{ source.file_name }} · chunk
                    {{ source.chunk_index }}
                  </summary>
                  <p>{{ source.content }}</p>
                </details>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="chat-composer">
        <div v-if="chat.error" class="alert">{{ chat.error }}</div>
        <form @submit.prevent="send">
          <textarea
            v-model="question"
            rows="2"
            placeholder="向你的文档提问…"
            :disabled="chat.loading"
            @keydown.enter.exact.prevent="send"
          ></textarea
          ><button
            class="send-button"
            type="submit"
            :disabled="chat.loading || !question.trim()"
          >
            {{ chat.loading ? "生成中" : "发送 ↑" }}
          </button>
        </form>
        <small>Enter 发送 · Shift+Enter 换行 · 回答仅供学习参考</small>
      </div>
    </section>
  </div>
</template>
