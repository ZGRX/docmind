<script setup>
import { computed } from "vue";
import { marked } from "marked";
import DOMPurify from "dompurify";

const props = defineProps({ content: { type: String, default: "" } });
marked.setOptions({ breaks: true, gfm: true });
const html = computed(() => DOMPurify.sanitize(marked.parse(props.content)));
</script>

<template><div class="markdown-body" v-html="html"></div></template>
