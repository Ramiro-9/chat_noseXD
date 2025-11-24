from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

# =========================
#   CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
#   HEALTHCHECK PARA RENDER
# =========================
@app.get("/")
def home():
    return {"status": "ok", "message": "WebSocket server running!"}

# =========================
#   CHAT CON SALAS
# =========================

# clients: { websocket: {"name": str, "shift": int, "room": str} }
clients = {}

def caesar_encrypt(text, shift):
    result = ""
    for char in text:
        if char.isalpha():
            base = 'A' if char.isupper() else 'a'
            result += chr((ord(char) - ord(base) + shift) % 26 + ord(base))
        else:
            result += char
    return result

async def broadcast_to_room(room: str, message: dict):
    """Envía un JSON a todos los clientes de una sala concreta."""
    dead_clients = []
    for ws, info in clients.items():
        if info["room"] == room:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead_clients.append(ws)
    # limpiar conexiones muertas
    for ws in dead_clients:
        clients.pop(ws, None)

async def send_users_list(room: str):
    """Envía la lista de usuarios conectados en la sala."""
    users = [info["name"] for info in clients.values() if info["room"] == room]
    await broadcast_to_room(room, {"type": "users", "users": users})

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # registro temporal hasta que haga "join"
    clients[websocket] = {"name": "Anon", "shift": 3, "room": "general"}

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type", "message")

            if msg_type == "join":
                # actualizar datos del usuario
                name = data.get("name", "Anon")
                shift = int(data.get("shift", 3))
                room = data.get("room", "general") or "general"

                clients[websocket] = {
                    "name": name,
                    "shift": shift,
                    "room": room
                }

                # mensaje del sistema
                await broadcast_to_room(
                    room,
                    {
                        "type": "system",
                        "text": f"{name} se unió a la sala {room}"
                    }
                )
                # enviar lista de usuarios
                await send_users_list(room)

            elif msg_type == "message":
                info = clients.get(websocket)
                if not info:
                    continue

                room = info["room"]
                name = info["name"]
                shift = info["shift"]

                plain_text = data.get("message", "")
                encrypted = caesar_encrypt(plain_text, shift)

                await broadcast_to_room(
                    room,
                    {
                        "type": "message",
                        "from": name,
                        "text": encrypted
                    }
                )

    except WebSocketDisconnect:
        info = clients.pop(websocket, None)
        if info:
            room = info["room"]
            name = info["name"]
            # avisar que se fue
            await broadcast_to_room(
                room,
                {
                    "type": "system",
                    "text": f"{name} salió del chat"
                }
            )
            await send_users_list(room)
