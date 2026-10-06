import axios from "axios";

export const baseURL = import.meta.env.VITE_API_BASE_URL || "/api";
export const api = axios.create({ baseURL, timeout: 120000 });

export function errorMessage(error) {
  return error.response?.data?.error || error.message || "请求失败";
}

// fetch exposes response.body, which Axios does not in the browser.
export async function streamChat(payload, onEvent, signal) {
  const response = await fetch(`${baseURL}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.error || `请求失败 (${response.status})`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let completed = false;
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const parts = buffer.split("\n\n");
    buffer = parts.pop();
    for (const part of parts) {
      const event = part.match(/^event: (.+)$/m)?.[1];
      const data = part.match(/^data: (.+)$/m)?.[1];
      if (event && data) {
        if (event === "done") completed = true;
        onEvent(event, JSON.parse(data));
      }
    }
    if (done) break;
  }
  if (!completed) throw new Error("连接中断，回答可能未保存");
}
