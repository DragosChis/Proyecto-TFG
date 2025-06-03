# Importamos las librerías necesarias
import os  # Para acceder a las variables de entorno
import requests  # Para realizar peticiones HTTP a la API de WhatsApp
from dotenv import load_dotenv  # Para cargar las variables de entorno desde el archivo .env

# Cargamos las variables de entorno (como el token de WhatsApp)
load_dotenv()
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")  # Token de autenticación de WhatsApp
PHONE_NUMBER_ID = "611948532009771"  # ID del número de teléfono de WhatsApp (debe coincidir con tu cuenta de WhatsApp Business)

# Función para enviar un mensaje de texto por WhatsApp
def enviar_mensaje_whatsapp(destinatario, mensaje):
    # Construimos la URL de la API de WhatsApp con el número de teléfono configurado
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    # Cabeceras HTTP para autenticar la petición
    headers = {
        "Authorization": "Bearer " + WHATSAPP_TOKEN,  # Autenticación con el token
        "Content-Type": "application/json"
    }

    # Cuerpo de la petición: a quién se envía y el contenido del mensaje
    payload = {
        "messaging_product": "whatsapp",
        "to": destinatario,  # Número de teléfono del destinatario en formato internacional (sin espacios)
        "type": "text",
        "text": {
            "body": mensaje  # Texto del mensaje
        }
    }

    # Realizamos la petición POST a la API
    response = requests.post(url, headers=headers, json=payload)

    # Mostramos el estado y la respuesta completa de la API (útil para depuración)
    print("🔴 Código de estado:", response.status_code)
    print("🔴 Respuesta completa:", response.text)

    # Verificamos si el mensaje se envió correctamente
    if response.ok:
        print("✅ Mensaje enviado correctamente.")
    else:
        print("❌ Error al enviar el mensaje.")

# Ejemplo de uso: envía un mensaje de prueba si el script se ejecuta directamente
if __name__ == "__main__":
    enviar_mensaje_whatsapp("34672152844", "Buenos días!")
