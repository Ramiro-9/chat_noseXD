@app.get("/")
def home():
    return {"status": "ok", "message": "WebSocket server running!"}

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

# Permitir acceso desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = []

def caesar_encrypt(text, shift):
    result = ""
    for char in text:
        if char.isalpha():
            base = 'A' if char.isupper() else 'a'
            result += chr((ord(char) - ord(base) + shift) % 26 + ord(base))
        else:
            result += char
    return result

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)

            name = data["name"]
            message = data["message"]
            shift = int(data["shift"])

            encrypted = caesar_encrypt(message, shift)

            full_msg = f"{name}: {encrypted}"

            for client in clients:
                await client.send_text(full_msg)

    except WebSocketDisconnect:
        clients.remove(websocket)


