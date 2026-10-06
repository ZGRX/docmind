import { defineStore } from "pinia";
import { reactive, ref } from "vue";
import { api, errorMessage, streamChat } from "../api/client";

export const useChatStore = defineStore("chat", () => {
  const conversations = ref([]);
  const conversationId = ref(null);
  const messages = ref([]);
  const loading = ref(false);
  const error = ref("");

  async function loadConversations() {
    error.value = "";
    try {
      conversations.value = (await api.get("/conversations")).data;
    } catch (err) {
      error.value = errorMessage(err);
    }
  }

  async function openConversation(id) {
    error.value = "";
    try {
      const data = (await api.get(`/conversations/${id}`)).data;
      conversationId.value = data.id;
      messages.value = data.messages;
    } catch (err) {
      error.value = errorMessage(err);
    }
  }

  function clear() {
    conversationId.value = null;
    messages.value = [];
    error.value = "";
  }

  async function removeConversation(id) {
    await api.delete(`/conversations/${id}`);
    if (conversationId.value === id) clear();
    await loadConversations();
  }

  async function send(question) {
    if (loading.value || !question.trim()) return;
    error.value = "";
    const previousId = conversationId.value;
    const user = { role: "user", content: question.trim(), sources: [] };
    const assistant = reactive({ role: "assistant", content: "", sources: [] });
    messages.value.push(user, assistant);
    loading.value = true;
    try {
      await streamChat(
        { question: user.content, conversation_id: previousId },
        (event, data) => {
          if (event === "meta") {
            conversationId.value = data.conversation_id;
            assistant.sources = data.sources;
          }
          if (event === "token") assistant.content += data.text;
          if (event === "error") throw new Error(data.message);
        },
      );
      await loadConversations();
    } catch (err) {
      error.value = errorMessage(err);
      if (!assistant.content) messages.value.pop();
      // A user message may already be saved server-side if the stream failed.
      if (conversationId.value) await openConversation(conversationId.value);
      else messages.value.pop();
    } finally {
      loading.value = false;
    }
  }

  return {
    conversations,
    conversationId,
    messages,
    loading,
    error,
    loadConversations,
    openConversation,
    clear,
    removeConversation,
    send,
  };
});
