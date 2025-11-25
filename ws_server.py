from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import json
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clients = []

# -------------------------------
#  SUPABASE CLIENT
# -------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------
#  Cifrado César
# -------------------------------
def caesar_encrypt(text, shift):
    result = ""
    for char in text:
        if char.isalpha():
            base = 'A' if char.isupper() else 'a'
            result += chr((ord(char) - ord(base) + shift) % 26 + ord(base))
        else:
            result += char
    return result


# -------------------------------
#  WebSocket principal
# -------------------------------
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)

    try:
        while True:

            # -----------------------------
            # Recibir JSON desde el cliente
            # -----------------------------
            data = await websocket.receive_text()
            data = json.loads(data)

            # Datos recibidos
            user_id = data.get("user_id")
            room_id = data.get("room_id")
            name = data.get("name")
            message = data.get("message")
            shift = int(data.get("shift", 3))

            # Cifrar
            encrypted = caesar_encrypt(message, shift)

            # Guardar en SUPABASE
            supabase.table("messages").insert({
                "user_id": user_id,
                "room_id": room_id,
                "text": encrypted,
                "shift": shift
            }).execute()

            # Mensaje formateado
            full_message = f"{name}: {encrypted}"

            # Enviar a todos los conectados
            for client in clients:
                await client.send_text(full_message)

    except WebSocketDisconnect:
        clients.remove(websocket)
