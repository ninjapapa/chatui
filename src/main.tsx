import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App.tsx"
import FeatureRequestWindow from "./FeatureRequestWindow.tsx"
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
  <React.StrictMode>{panel === "feature-request" ? <FeatureRequestWindow /> : <App />}</React.StrictMode>,
)
