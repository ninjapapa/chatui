"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Send } from "lucide-react"
import ReactMarkdown from "react-markdown"
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter"
import { dracula } from "react-syntax-highlighter/dist/esm/styles/prism"
import "./App.css"
import { getJson, postJson, backendWsBase } from "./api"
import { getOrCreateChatId } from "./chatId"
import Changelog from "./Changelog"
import Backlog from "./Backlog"
import AnswerFeedback from "./AnswerFeedback"

interface Message {
  id?: string
  chat_id?: string
  role: string
  content: string
  thinking?: string
  markdown?: string
  parent_message_id?: string
}

function parseIncomingMessage(data: any): Message {
  const content: string = data.content ?? ""
  const thinkMatch = content.match(/<think>(.*?)<\/think>/s)
  const thinking = thinkMatch ? thinkMatch[1].trim() : ""
  let markdown = content
  if (thinkMatch) markdown = content.replace(/<think>.*?<\/think>/s, "").trim()

  return {
    id: data.id,
    chat_id: data.chat_id,
    role: data.role,
    content,
    thinking,
    markdown,
    parent_message_id: data.parent_message_id,
  }
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isConnected, setIsConnected] = useState(false)
  const [chatId, setChatId] = useState<string | null>(null)
  const [freeformText, setFreeformText] = useState("")
  const [freeformStatus, setFreeformStatus] = useState<string | null>(null)
  const [view, setView] = useState<"chat" | "changelog" | "backlog">("chat")

  const socketRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Initialize chat id + hydrate history
  useEffect(() => {
    const id = getOrCreateChatId()
    setChatId(id)

    // Ensure chat exists in backend (best-effort)
    postJson("/api/chat", { chat_id: id }).catch(() => {})

    getJson<Message[]>(`/api/messages?chat_id=${encodeURIComponent(id)}&limit=200`)
      .then((rows) => {
        const hydrated = rows.map((r: any) => parseIncomingMessage(r))
        setMessages(hydrated)
      })
      .catch((err) => {
        console.warn("Failed to hydrate messages:", err)
      })
  }, [])

  // Connect to WebSocket
  useEffect(() => {
    const socket = new WebSocket(backendWsBase() + "/ws")

    socket.onopen = () => {
      console.log("WebSocket connected")
      setIsConnected(true)
    }

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const parsed = parseIncomingMessage(data)

        // Ensure assistant messages have a stable id for feedback + persistence
        const newMessage: Message =
          parsed.role === "assistant" ? { ...parsed, id: parsed.id ?? `asst_${crypto.randomUUID()}` } : parsed

        setMessages((prev) => [...prev, newMessage])

        // Persist assistant message
        if (chatId && newMessage.role === "assistant" && newMessage.id) {
          postJson("/api/message", {
            id: newMessage.id,
            chat_id: chatId,
            role: "assistant",
            content: newMessage.content,
            parent_message_id: newMessage.parent_message_id,
          }).catch((err) => console.warn("Persist assistant message failed:", err))
        }
      } catch (error) {
        console.error("Error parsing message:", error)
      }
    }

    socket.onclose = () => {
      console.log("WebSocket disconnected")
      setIsConnected(false)
    }

    socket.onerror = (e) => {
      console.warn("WebSocket error:", e)
      setIsConnected(false)
    }

    socketRef.current = socket

    return () => {
      socket.close()
    }
  }, [chatId])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !isConnected || !chatId) return

    const userMsgId = `user_${crypto.randomUUID()}`

    // Add user message to the chat
    const userMessage: Message = {
      id: userMsgId,
      chat_id: chatId,
      role: "user",
      content: input,
    }
    setMessages((prev) => [...prev, userMessage])

    // Persist user message
    postJson("/api/message", {
      id: userMsgId,
      chat_id: chatId,
      role: "user",
      content: input,
    }).catch((err) => console.warn("Persist user message failed:", err))

    // Send message to WebSocket
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          chat_id: chatId,
          message_id: userMsgId,
          content: input,
        })
      )
    }

    setInput("")
  }


  const submitFreeform = async () => {
    if (!chatId || !freeformText.trim()) return
    setFreeformStatus("Saving...")
    try {
      await postJson("/api/feedback/freeform", {
        id: `ff_${crypto.randomUUID()}`,
        chat_id: chatId,
        text: freeformText,
      })
      setFreeformText("")
      setFreeformStatus("Saved")
      setTimeout(() => setFreeformStatus(null), 1500)
    } catch (e: any) {
      setFreeformStatus(`Error: ${e?.message ?? e}`)
    }
  }

  const CodeBlock = ({ inline, className, children, ...props }: any) => {
    const match = /language-(\w+)/.exec(className || "")
    return !inline && match ? (
      <SyntaxHighlighter style={dracula} language={match[1]} PreTag="div" {...props}>
        {String(children).replace(/\n$/, "")}
      </SyntaxHighlighter>
    ) : (
      <code className={className} {...props}>
        {children}
      </code>
    )
  }

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4">
      <header className="py-4 border-b">
        <h1 className="text-2xl font-bold text-center">Chat Interface</h1>
        <div className="text-center">
          <span className={`inline-block w-3 h-3 rounded-full mr-2 ${isConnected ? "bg-green-500" : "bg-red-500"}`}></span>
          {isConnected ? "Connected" : "Disconnected"}
        </div>

        <div className="mt-3 flex gap-2 items-center justify-center">
          <button
            type="button"
            className={`px-3 py-2 rounded-lg border ${view === "chat" ? "bg-gray-900 text-white" : "bg-white"}`}
            onClick={() => setView("chat")}
          >
            Chat
          </button>
          <button
            type="button"
            className={`px-3 py-2 rounded-lg border ${view === "changelog" ? "bg-gray-900 text-white" : "bg-white"}`}
            onClick={() => setView("changelog")}
          >
            Changelog
          </button>
          <input
            value={freeformText}
            onChange={(e) => setFreeformText(e.target.value)}
            placeholder="Free-form feedback (catch-all)…"
            className="w-full max-w-xl p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={submitFreeform}
            className="bg-gray-900 text-white px-3 py-2 rounded-lg disabled:bg-gray-400"
            disabled={!freeformText.trim() || !chatId}
            type="button"
          >
            Send
          </button>
        </div>
        {freeformStatus && <div className="text-center text-xs text-gray-600 mt-1">{freeformStatus}</div>}



        <div className="mt-3 flex items-center justify-center">
          <button
            type="button"
            className="px-3 py-2 rounded-lg border bg-white hover:bg-gray-50"
            onClick={() => {
              const url = new URL(window.location.href)
              url.searchParams.set("panel", "feature-request")
              // pass chat id explicitly when available
              if (chatId) url.searchParams.set("chat_id", chatId)
              const features = "popup,width=520,height=700"
              const w = window.open(url.toString(), "feature_request", features)
              if (!w) window.open(url.toString(), "_blank", "noopener,noreferrer")
            }}
            disabled={!chatId}
            title={!chatId ? "Chat not ready yet" : "Open feature request window"}
          >
            Request a feature ↗
          </button>
        </div>
      </header>

      {view === "changelog" ? (
        <div className="flex-1 overflow-y-auto">
          <Changelog />
        </div>
      ) : view === "backlog" ? (
        <div className="flex-1 overflow-y-auto">
          <Backlog />
        </div>
      ) : (
      <div className="flex-1 overflow-y-auto py-4 space-y-4">
        {messages.map((message, index) => (
          <div key={message.id ?? index} className={`flex flex-col ${message.role === "user" ? "items-end" : "items-start"}`}>
            <div className="font-semibold text-sm mb-1">{message.role === "user" ? "You" : message.role}</div>

            {message.role === "user" && message.content && (
              <div className="bg-gray-100 rounded-lg p-3 mb-2 max-w-[80%] text-sm">
                <div className="whitespace-pre-wrap">{message.content}</div>
              </div>
            )}

            {message.role !== "user" && (
              <div className="bg-white border rounded-lg p-3 max-w-[80%] prose prose-sm">
                {message.thinking && (
                  <details className="mb-2">
                    <summary className="cursor-pointer text-gray-500">Thinking</summary>
                    <div className="whitespace-pre-wrap text-sm mt-1">{message.thinking}</div>
                  </details>
                )}
                {message.markdown && <ReactMarkdown components={{ code: CodeBlock }}>{message.markdown}</ReactMarkdown>}

                {message.role === "assistant" && message.id && chatId && (
                  <AnswerFeedback chatId={chatId} messageId={message.id} />
                )}
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      )}

      <form onSubmit={handleSubmit} className="border-t pt-4">
        <div className="flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 p-2 border rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={!isConnected}
          />
          <button
            type="submit"
            className="bg-blue-500 text-white p-2 rounded-r-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-300"
            disabled={!isConnected || !input.trim()}
          >
            <Send size={20} />
          </button>
        </div>
      </form>
    </div>
  )
}

export default App
