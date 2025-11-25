from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import json
import os

app = FastAPI()

# =====================================
#   CORS
# =====================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================
#   HEALTHCHECK (para Render)
# =====================================
@app.get("/")
def home():
    return {"status": "ok", "message": "WebSocket server running!"}

# =====================================
#   SUPABASE
# =====================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# clients: { websocket: {"name": str, "shift": int, "room_id": str, "room_name": str, "user_id": str} }
clients = {}

# =====================================
#   CIFRADO CÉSAR
# =====================================
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
#   HELPERS SUPABASE
# =====================================
def get_or_create_user(name: str) -> str:
    """Busca un usuario por name, si no existe lo crea. Devuelve user_id (uuid)."""
    res = supabase.table("users").select("id").eq("name", name).execute()
    if res.data:
        return res.data[0]["id"]

    # crear
    ins = supabase.table("users").insert({
        "name": name,
        "avatar": None
    }).execute()
    return ins.data[0]["id"]

def get_or_create_room(room_name: str) -> str:
    """Busca una sala por name, si no existe la crea. Devuelve room_id (uuid)."""
    res = supabase.table("rooms").select("id").eq("name", room_name).execute()
    if res.data:
        return res.data[0]["id"]

    ins = supabase.table("rooms").insert({
        "name": room_name
    }).execute()
    return ins.data[0]["id"]

async def broadcast_to_room(room_id: str, message: dict):
    """Envía un JSON a todos los clientes conectados en una sala."""
    to_remove = []
    for ws, info in clients.items():
        if info["room_id"] == room_id:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                to_remove.append(ws)
    for ws in to_remove:
        clients.pop(ws, None)

async def send_users_list(room_id: str):
    """Manda la lista de usuarios conectados en esa sala."""
    users = [info["name"] for ws, info in clients.items() if info["room_id"] == room_id]
    await broadcast_to_room(room_id, {
        "type": "users",
        "users": users
    })

# =====================================
#   WEBSOCKET
# =====================================
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # Mientras no se haga join, no sabemos su info
    clients[websocket] = {
        "name": "Anon",
        "shift": 3,
        "room_id": None,
        "room_name": None,
        "user_id": None,
    }

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type")

            # -----------------------------
            # JOIN A LA SALA
            # -----------------------------
            if msg_type == "join":
                name = data.get("name", "Anon")
                shift = int(data.get("shift", 3))
                room_name = data.get("room", "general") or "general"

                # usuario real en Supabase
                user_id = get_or_create_user(name)
                # sala real en Supabase
                room_id = get_or_create_room(room_name)

                clients[websocket] = {
                    "name": name,
                    "shift": shift,
                    "room_id": room_id,
                    "room_name": room_name,
                    "user_id": user_id,
                }

                # mensaje del sistema
                await broadcast_to_room(room_id, {
                    "type": "system",
                    "text": f"{name} se unió a la sala {room_name}"
                })

                # lista de usuarios en la sala
                await send_users_list(room_id)

            # -----------------------------
            # MENSAJE NORMAL
            # -----------------------------
            elif msg_type == "message":
                info = clients.get(websocket)
                if not info or not info["room_id"] or not info["user_id"]:
                    continue

                plain_text = data.get("message", "")
                name = info["name"]
                shift = info["shift"]
                room_id = info["room_id"]

                encrypted = caesar_encrypt(plain_text, shift)

                # Guardar en Supabase
                supabase.table("messages").insert({
                    "room_id": room_id,
                    "user_id": info["user_id"],
                    "text": encrypted,
                    "shift": shift
                }).execute()

                # Enviar a todos en la sala
                await broadcast_to_room(room_id, {
                    "type": "message",
                    "from": name,
                    "text": encrypted
                })

    except WebSocketDisconnect:
        info = clients.pop(websocket, None)
        if info and info["room_id"]:
            room_id = info["room_id"]
            name = info["name"]

            # avisar que se fue
            await broadcast_to_room(room_id, {
                "type": "system",
                "text": f"{name} salió del chat"
            })
            await send_users_list(room_id)
