import { createRouter, createWebHistory } from "vue-router";
import Dashboard from "../views/Dashboard.vue";
import Documents from "../views/Documents.vue";
import Chat from "../views/Chat.vue";
import History from "../views/History.vue";

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: Dashboard },
    { path: "/documents", component: Documents },
    { path: "/chat", component: Chat },
    { path: "/history", component: History },
  ],
});
