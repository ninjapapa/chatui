import { useEffect, useMemo, useState } from "react"
import { getOrCreateChatId } from "./chatId"
import Changelog from "./Changelog"
import { postJson } from "./api"

function getParam(name: string): string | null {
  try {
    return new URLSearchParams(window.location.search).get(name)
  } catch {
    return null
  }
}

type FeedbackType = "feedback" | "feature_request"

type Tab = "feedback" | "changelog"

export default function FeedbackWindow(props: { defaultType?: FeedbackType }) {
  const [chatId, setChatId] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>("feedback")

  const initialType: FeedbackType = props.defaultType ?? "feedback"
  const [kind, setKind] = useState<FeedbackType>(initialType)

  const [feedbackText, setFeedbackText] = useState("")

  const [desc, setDesc] = useState("")
  const [expected, setExpected] = useState("")

  const [status, setStatus] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  // Prefer a provided chat_id, but fall back to shared localStorage id.
  const resolvedChatId = useMemo(() => {
    const fromQuery = getParam("chat_id") || getParam("chatId")
    return fromQuery?.trim() || null
  }, [])

  useEffect(() => {
    setChatId(resolvedChatId ?? getOrCreateChatId())

    // Best-effort focus for popouts
    try {
      window.focus()
    } catch {
      // ignore
    }
  }, [resolvedChatId])

  const canSubmit =
    kind === "feedback" ? !!feedbackText.trim() : !!desc.trim() || !!expected.trim()

  const submit = async () => {
    if (!chatId || !canSubmit) return

    setSaving(true)
    setStatus("Saving...")

    try {
      if (kind === "feedback") {
        await postJson("/api/feedback/freeform", {
          id: `ff_${crypto.randomUUID()}`,
          chat_id: chatId,
          text: feedbackText.trim(),
          metadata: {
            type: "feedback",
          },
        })
        setFeedbackText("")
      } else {
        await postJson("/api/feedback/freeform", {
          id: `ff_${crypto.randomUUID()}`,
          chat_id: chatId,
          text: [
            `Feature request: ${desc.trim() || "(no description)"}`,
            expected.trim() ? `Expected outcome: ${expected.trim()}` : "",
          ]
            .filter(Boolean)
            .join("\n"),
          metadata: {
            type: "feature_request",
            description: desc.trim() || null,
            expected_outcome: expected.trim() || null,
          },
        })

        setDesc("")
        setExpected("")
      }

      setStatus("Saved")
      setTimeout(() => setStatus(null), 1500)
    } catch (e: any) {
      setStatus(`Error: ${e?.message ?? e}`)
    } finally {
      setSaving(false)
    }
  }

  if (!chatId) return null

  return (
    <div className="min-h-screen p-4 max-w-2xl mx-auto">
      <div className="flex items-center justify-between gap-3 mb-3">
        <h1 className="text-lg font-semibold">Feedback</h1>
        <button type="button" className="px-3 py-2 rounded border" onClick={() => window.close()}>
          Close
        </button>
      </div>

      <div className="flex items-center gap-2 mb-3">
        <button
          type="button"
          className={`px-3 py-2 rounded border ${tab === "feedback" ? "bg-gray-900 text-white" : "bg-white"}`}
          onClick={() => setTab("feedback")}
        >
          Feedback
        </button>
        <button
          type="button"
          className={`px-3 py-2 rounded border ${tab === "changelog" ? "bg-gray-900 text-white" : "bg-white"}`}
          onClick={() => setTab("changelog")}
        >
          Changelog
        </button>
      </div>

      {tab === "changelog" ? (
        <div className="border rounded-lg p-3 bg-white">
          <Changelog />
        </div>
      ) : (
        <div className="border rounded-lg p-3 bg-white">
          <div className="text-sm font-medium mb-2">Type</div>
          <div className="flex items-center gap-4 mb-3">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="kind"
                value="feedback"
                checked={kind === "feedback"}
                onChange={() => setKind("feedback")}
              />
              Feedback
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="kind"
                value="feature_request"
                checked={kind === "feature_request"}
                onChange={() => setKind("feature_request")}
              />
              Request feature
            </label>
          </div>

          {kind === "feedback" ? (
            <div className="grid gap-2">
              <textarea
                className="p-2 border rounded text-sm"
                placeholder="Feedback"
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                rows={4}
              />
            </div>
          ) : (
            <div className="grid gap-2">
              <textarea
                className="p-2 border rounded text-sm"
                placeholder="Description"
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                rows={3}
              />
              <textarea
                className="p-2 border rounded text-sm"
                placeholder="Expected result / example"
                value={expected}
                onChange={(e) => setExpected(e.target.value)}
                rows={3}
              />
            </div>
          )}

          <div className="flex items-center gap-2 mt-3">
            <button
              type="button"
              className="px-3 py-2 rounded bg-gray-900 text-white disabled:bg-gray-400"
              disabled={saving || !canSubmit}
              onClick={submit}
            >
              Submit
            </button>
            {status && <div className="text-xs text-gray-600">{status}</div>}
          </div>
        </div>
      )}

      <div className="text-xs text-gray-500 mt-2">This window is linked to your current chat session.</div>
    </div>
  )
}
