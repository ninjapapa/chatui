import { useState } from "react";
import { postJson } from "./api";

export default function FeatureRequest(props: { chatId: string }) {
  const { chatId } = props;
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [outcome, setOutcome] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const submit = async () => {
    if (!title.trim() && !desc.trim() && !outcome.trim()) return;
    setSaving(true);
    setStatus("Saving...");
    try {
      await postJson("/api/feedback/freeform", {
        id: `ff_${crypto.randomUUID()}`,
        chat_id: chatId,
        text: [
          `Feature request: ${title.trim() || "(no title)"}`,
          desc.trim() ? `Description: ${desc.trim()}` : "",
          outcome.trim() ? `Expected outcome: ${outcome.trim()}` : "",
        ]
          .filter(Boolean)
          .join("\n"),
        metadata: {
          type: "feature_request",
          title: title.trim() || null,
          description: desc.trim() || null,
          expected_outcome: outcome.trim() || null,
        },
      });
      setTitle("");
      setDesc("");
      setOutcome("");
      setStatus("Saved");
      setTimeout(() => setStatus(null), 1500);
    } catch (e: any) {
      setStatus(`Error: ${e?.message ?? e}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mt-3 w-full max-w-4xl mx-auto">
      <div className="border rounded-lg p-3 bg-white">
        <div className="font-medium mb-2">Request a feature</div>
        <div className="grid gap-2">
          <input
            className="p-2 border rounded text-sm"
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <textarea
            className="p-2 border rounded text-sm"
            placeholder="Description"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            rows={2}
          />
          <textarea
            className="p-2 border rounded text-sm"
            placeholder="Expected outcome"
            value={outcome}
            onChange={(e) => setOutcome(e.target.value)}
            rows={2}
          />
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="px-3 py-2 rounded bg-gray-900 text-white disabled:bg-gray-400"
              disabled={saving || (!title.trim() && !desc.trim() && !outcome.trim())}
              onClick={submit}
            >
              Submit
            </button>
            {status && <div className="text-xs text-gray-600">{status}</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
