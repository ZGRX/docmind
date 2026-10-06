<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useChatStore } from "../stores/chat";
import { errorMessage } from "../api/client";

const chat = useChatStore();
const router = useRouter();
const error = ref("");
onMounted(chat.loadConversations);

async function open(id) {
  await router.push({ path: "/chat", query: { id } });
}
async function remove(item) {
  if (!window.confirm(`删除会话「${item.title}」？`)) return;
  try {
    await chat.removeConversation(item.id);
  } catch (err) {
    error.value = errorMessage(err);
  }
}
const formatDate = (value) => new Date(value).toLocaleString("zh-CN");
</script>

<template>
  <div class="page">
    <div class="eyebrow">PAST CONVERSATIONS</div>
    <div class="page-heading">
      <div>
        <h1>历史会话<span class="heading-dot">.</span></h1>
        <p>回看以前的问题，继续你的学习。</p>
      </div>
    </div>
    <div v-if="error || chat.error" class="alert">
      {{ error || chat.error }}
    </div>
    <section class="panel">
      <div class="panel-heading">
        <div>
          <span class="eyebrow">ARCHIVE</span>
          <h2>
            全部会话 <em>{{ chat.conversations.length }}</em>
          </h2>
        </div>
      </div>
      <div v-if="!chat.conversations.length" class="empty-state">
        暂无会话。去文档问答开始第一次提问吧。
      </div>
      <div
        v-for="item in chat.conversations"
        :key="item.id"
        class="history-row"
      >
        <button class="history-open" @click="open(item.id)">
          <span class="history-icon">✧</span
          ><span
            ><strong>{{ item.title }}</strong
            ><small>{{ formatDate(item.created_at) }}</small></span
          ></button
        ><button class="icon-button danger" @click="remove(item)">删除</button>
      </div>
    </section>
  </div>
</template>
