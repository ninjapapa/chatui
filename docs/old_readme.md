# Chat Interface for LLM appilations

## Features

- Syntax highlighting for code blocks
- Markdown formatting
- Chat history

## Usage

```bash
npm run build
```

Then on application project, use ```FastAPI``` to serve the static files:

```python
app = FastAPI()
app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")


@app.get("/")
async def read_index():
    return FileResponse("dist/index.html")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection opened")

    moomoo_api = MooMooAPI()
    index = moomoo_api.get_index()
    chat_engine = index.as_chat_engine(
        chat_mode="context",
        system_prompt=(
            "You are a codeing helper who can use API doc provided from the context to create python code"
            " Please responde as Markdown with code blocks quoted with ```python"
        )
    )
    while True:
        user_query = await websocket.receive_text()
        print(user_query)
        response = await chat_engine.achat(user_query)
        print(response.response)
        agent_message = {
            "role": "assistant",
            "content": response.response
        }
        await websocket.send_text(json.dumps(agent_message))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app_ui:app", host="localhost", port=8080, reload=True)
```