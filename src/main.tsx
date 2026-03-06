import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App.tsx"
import FeedbackWindow from "./FeedbackWindow.tsx"
import "./index.css"

function getParam(name: string): string | null {
  try {
    return new URLSearchParams(window.location.search).get(name)
  } catch {
    return null
  }
}

const panel = getParam("panel")

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    {panel === "feature-request" ? (
      // Backward-compatible panel. New unified feedback popout should be used going forward.
      <FeedbackWindow defaultType="feature_request" />
    ) : panel === "feedback" ? (
      <FeedbackWindow />
    ) : (
      <App />
    )}
  </React.StrictMode>,
)
