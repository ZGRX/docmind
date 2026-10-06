import { defineStore } from "pinia";
import { ref } from "vue";
import { api, errorMessage } from "../api/client";

export const useDocumentsStore = defineStore("documents", () => {
  const items = ref([]);
  const loading = ref(false);
  const error = ref("");

  async function load() {
    loading.value = true;
    error.value = "";
    try {
      items.value = (await api.get("/documents")).data;
    } catch (err) {
      error.value = errorMessage(err);
    } finally {
      loading.value = false;
    }
  }

  async function upload(file) {
    const form = new FormData();
    form.append("file", file);
    await api.post("/documents", form);
    await load();
  }

  async function remove(id) {
    await api.delete(`/documents/${id}`);
    await load();
  }

  return { items, loading, error, load, upload, remove };
});
