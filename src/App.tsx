"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Send } from "lucide-react"
import ReactMarkdown from "react-markdown"
import "./App.css"

interface Message {
  role: string
  content: string
  thinking?: string
  markdown?: string
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isConnected, setIsConnected] = useState(false)
  const socketRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Connect to WebSocket
  useEffect(() => {
    // Replace with your actual WebSocket URL
    const socket = new WebSocket("ws://localhost:8080/ws")

    socket.onopen = () => {
      console.log("WebSocket connected")
      setIsConnected(true)
    }

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        // Parse the content to extract thinking and markdown parts
        const thinkMatch = data.content.match(/<think>(.*?)<\/think>/s)
        const thinking = thinkMatch ? thinkMatch[1].trim() : ""

        // Extract markdown content (everything after the </Thinking> tag)
        let markdown = data.content
        if (thinkMatch) {
          markdown = data.content.replace(/<think>.*?<\/think>/s, "").trim()
        }

        const newMessage: Message = {
          role: data.role,
          content: data.content,
          thinking,
          markdown,
        }

        setMessages((prev) => [...prev, newMessage])
      } catch (error) {
        console.error("Error parsing message:", error)
      }
    }

    socket.onclose = () => {
      console.log("WebSocket disconnected")
      setIsConnected(false)
    }

    socketRef.current = socket

    return () => {
      socket.close()
    }
  }, [])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !isConnected) return

    // Add user message to the chat
    const userMessage: Message = {
      role: "user",
      content: input,
    }
    setMessages((prev) => [...prev, userMessage])

    // Send message to WebSocket
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(input))
    }

    setInput("")
  }

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4">
      <header className="py-4 border-b">
        <h1 className="text-2xl font-bold text-center">Chat Interface</h1>
        <div className="text-center">
          <span
            className={`inline-block w-3 h-3 rounded-full mr-2 ${isConnected ? "bg-green-500" : "bg-red-500"}`}
          ></span>
          {isConnected ? "Connected" : "Disconnected"}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto py-4 space-y-4">
        {messages.map((message, index) => (
          <div key={index} className={`flex flex-col ${message.role === "user" ? "items-end" : "items-start"}`}>
            <div className="font-semibold text-sm mb-1">{message.role === "user" ? "You" : message.role}</div>

            {message.role === "user" && message.content && (
              <div className="bg-gray-100 rounded-lg p-3 mb-2 max-w-[80%] text-sm">
                <div className="whitespace-pre-wrap">{message.content}</div>
              </div>
            )}

            {message.thinking && (
              <div className="bg-gray-100 rounded-lg p-3 mb-2 max-w-[80%] text-sm">
                <div className="font-medium text-gray-500 mb-1">Thinking:</div>
                <div className="whitespace-pre-wrap">{message.thinking}</div>
              </div>
            )}

            {message.markdown && (
              <div className="bg-white border rounded-lg p-3 max-w-[80%] prose prose-sm">
                <ReactMarkdown>{message.markdown}</ReactMarkdown>
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

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

