from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI()

# -----------------------------
# TU CÓDIGO ADAPTADO A API
# -----------------------------

def cifrar_cesar(texto, desplazamiento):
    resultado = ""
    for caracter in texto:
        if caracter.isalpha():
            base = ord('A') if caracter.isupper() else ord('a')
            resultado += chr((ord(caracter) - base + desplazamiento) % 26 + base)
        else:
            resultado += caracter
    return resultado

def descifrar_cesar(texto, desplazamiento):
    return cifrar_cesar(texto, -desplazamiento)

# Archivo de chat
CHAT_FILE = "chat_cifrado.txt"

class MensajeIn(BaseModel):
    usuario: str
    mensaje: str
    desplazamiento: int

class MensajeOut(BaseModel):
    usuario: str
    mensaje_descifrado: str

# ---------------------------------
# ENDPOINT: enviar mensaje cifrado
# ---------------------------------
@app.post("/enviar")
def enviar_msg(data: MensajeIn):
    mensaje_cifrado = cifrar_cesar(data.mensaje, data.desplazamiento)

    with open(CHAT_FILE, "a", encoding="utf-8") as archivo:
        archivo.write(f"{data.usuario}: {mensaje_cifrado}\n")

    return {"status": "ok", "mensaje_cifrado": mensaje_cifrado}

# ---------------------------------
# ENDPOINT: obtener chat descifrado
# ---------------------------------
@app.get("/historial")
def historial(desplazamiento: int):
    if not os.path.exists(CHAT_FILE):
        return []

    mensajes = []
    with open(CHAT_FILE, "r", encoding="utf-8") as archivo:
        for linea in archivo:
            usuario, mensaje_cifrado = linea.strip().split(": ", 1)
            mensaje_desc = descifrar_cesar(mensaje_cifrado, desplazamiento)

            mensajes.append(
                {"usuario": usuario, "mensaje_descifrado": mensaje_desc}
            )

    return mensajes
