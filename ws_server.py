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
            data = await websocket.receive_text()
            data = json.loads(data)

            name = data["name"]
            message = data["message"]
            shift = int(data["shift"])

            encrypted = caesar_encrypt(message, shift)
            full_message = f"{name}: {encrypted}"

            # ----------------------------------------------------
            # GUARDAR MENSAJE EN SUPABASE (sin sala por ahora)
            # ----------------------------------------------------
            supabase.table("messages").insert({
                "user_id": "00000000-0000-0000-0000-000000000000",  # temporal si no hay login
                "room_id": "00000000-0000-0000-0000-000000000000",  # sala global
                "text": encrypted,
                "shift": shift
            }).execute()

            # Enviar a todos
            for client in clients:
                await client.send_text(full_message)

    except WebSocketDisconnect:
        clients.remove(websocket)
