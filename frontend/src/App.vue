<script setup>
import { ref } from "vue";
import { RouterLink, RouterView, useRoute } from "vue-router";

const route = useRoute();
const menuOpen = ref(false);
const links = [
  { to: "/", icon: "◫", label: "概览" },
  { to: "/documents", icon: "▤", label: "文档管理" },
  { to: "/chat", icon: "✧", label: "文档问答" },
  { to: "/history", icon: "◷", label: "历史会话" },
];
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar" :class="{ open: menuOpen }">
      <div class="brand">
        <div class="brand-mark">D</div>
        <div><strong>DocMind</strong><span>AI STUDY ASSISTANT</span></div>
      </div>
      <div class="nav-label">工作空间</div>
      <nav>
        <RouterLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          class="nav-link"
          :class="{ active: route.path === link.to }"
          @click="menuOpen = false"
        >
          <span class="nav-icon">{{ link.icon }}</span
          >{{ link.label }}<span class="nav-arrow">↗</span>
        </RouterLink>
      </nav>
      <div class="sidebar-bottom">
        <div class="status-dot"></div>
        本地知识工作台 <small>v1.0</small>
      </div>
    </aside>
    <div v-if="menuOpen" class="mobile-shade" @click="menuOpen = false"></div>
    <main class="main-area">
      <header class="topbar">
        <button
          class="menu-button"
          aria-label="打开菜单"
          @click="menuOpen = true"
        >
          ☰</button
        ><span>让每份资料都能被提问</span
        ><span class="topbar-badge">RAG POWERED</span>
      </header>
      <RouterView />
    </main>
  </div>
</template>
