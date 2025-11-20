import requests

API_URL = "http://127.0.0.1:8000"

usuario = input("Ingresa tu nombre: ")
desplazamiento = int(input("Desplazamiento del cifrado César: "))

print("\n=== CHAT conectado a la API ===")
print("Escribe 'salir' para terminar.\n")

while True:
    # --- Mostrar historial ---
    r_hist = requests.get(f"{API_URL}/historial", params={"desplazamiento": desplazamiento})
    historial = r_hist.json()

    print("\n--- HISTORIAL ---")
    for msg in historial:
        print(f"{msg['usuario']}: {msg['mensaje_descifrado']}")
    print("------------------\n")

    # --- Enviar mensaje ---
    mensaje = input(f"{usuario}: ")

    if mensaje.lower() == "salir":
        print("Chat terminado.")
        break

    data = {
        "usuario": usuario,
        "mensaje": mensaje,
        "desplazamiento": desplazamiento
    }

    r_send = requests.post(f"{API_URL}/enviar", json=data)

    if r_send.status_code == 200:
        print("Mensaje enviado (cifrado y guardado en la API).")
    else:
        print("Error enviando mensaje:", r_send.text)
