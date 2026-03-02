const KEY = "chatui.chat_id";

export function getOrCreateChatId(): string {
  let id = localStorage.getItem(KEY);
  if (!id) {
    id = `chat_${crypto.randomUUID()}`;
    localStorage.setItem(KEY, id);
  }
  return id;
}
