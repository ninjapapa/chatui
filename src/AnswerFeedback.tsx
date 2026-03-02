import { useState } from "react";
import { postJson } from "./api";

export default function AnswerFeedback(props: { chatId: string; messageId: string }) {
  const { chatId, messageId } = props;
  const [comment, setComment] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const submit = async (thumbs: 1 | -1) => {
    setSaving(true);
    setStatus("Saving...");
    try {
      await postJson("/api/feedback/answer", {
        id: `fb_${crypto.randomUUID()}`,
        chat_id: chatId,
        message_id: messageId,
        thumbs,
        comment: comment.trim() ? comment.trim() : null,
      });
      setStatus("Saved");
      setTimeout(() => setStatus(null), 1500);
    } catch (e: any) {
      setStatus(`Error: ${e?.message ?? e}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mt-3">
      <div className="flex gap-2 items-center">
        <button type="button" className="px-2 py-1 border rounded hover:bg-gray-50" disabled={saving} onClick={() => submit(1)}>
          👍
        </button>
        <button type="button" className="px-2 py-1 border rounded hover:bg-gray-50" disabled={saving} onClick={() => submit(-1)}>
          👎
        </button>
        <input
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Optional comment…"
          className="flex-1 p-2 border rounded text-sm"
        />
      </div>
      {status && <div className="text-xs text-gray-600 mt-1">{status}</div>}
    </div>
  );
}
