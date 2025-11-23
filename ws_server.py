from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

# =====================================
#   CORS (permite acceso desde todos)
# =====================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================
#   ENDPOINT PARA RENDER / HEALTHCHECK
# =====================================
@app.get("/")
def home():
    return {"status": "ok", "message": "WebSocket server running!"}

# =====================================
#   FUNCIONES DEL CHAT
# =====================================
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

# =====================================
#   WEBSOCKET
# =====================================
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            name = data["name"]
            message = data["message"]
            shift = int(data["shift"])

            encrypted = caesar_encrypt(message, shift)
            full_msg = f"{name}: {encrypted}"

            # Enviar a todos los clientes conectados
            for client in clients:
                await client.send_text(full_msg)

    except WebSocketDisconnect:
        clients.remove(websocket)
