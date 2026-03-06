import { useEffect, useMemo, useState } from "react"
import FeatureRequest from "./FeatureRequest"
import { getOrCreateChatId } from "./chatId"

function getParam(name: string): string | null {
  try {
    return new URLSearchParams(window.location.search).get(name)
  } catch {
    return null
  }
}

export default function FeatureRequestWindow() {
  const [chatId, setChatId] = useState<string | null>(null)

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

  if (!chatId) return null

  return (
    <div className="min-h-screen p-4 max-w-2xl mx-auto">
      <div className="flex items-center justify-between gap-3 mb-3">
        <h1 className="text-lg font-semibold">Request a feature</h1>
        <button type="button" className="px-3 py-2 rounded border" onClick={() => window.close()}>
          Close
        </button>
      </div>
      <FeatureRequest chatId={chatId} />
      <div className="text-xs text-gray-500 mt-2">This window is linked to your current chat session.</div>
    </div>
  )
}
