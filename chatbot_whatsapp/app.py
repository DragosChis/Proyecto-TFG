# Importamos las librerías necesarias
from flask import Flask, request, jsonify  # Framework web para crear el servidor y manejar peticiones
import os  # Para acceder a las variables de entorno
from dotenv import load_dotenv  # Para cargar las variables de entorno desde un archivo .env
from utils.busqueda import buscar_fragmentos_parecidos  # Función personalizada para buscar fragmentos de contexto
from openai import OpenAI  # Librería de OpenAI para interactuar con la API de ChatGPT
import requests  # Para realizar peticiones HTTP (enviar mensajes por WhatsApp)
import sqlite3  # Para usar SQLite como base de datos local
import datetime  # Para controlar la hora y fecha en los límites de mensajes

# Cargamos las variables de entorno desde el archivo .env
load_dotenv()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")  # Token de verificación para WhatsApp
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")  # Token de autenticación de WhatsApp
PHONE_NUMBER_ID = "611948532009771"  # ID del número de teléfono de WhatsApp configurado
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Inicializamos el cliente de OpenAI

# Inicializamos la base de datos SQLite y creamos tablas si no existen
conn = sqlite3.connect('historiales.db', check_same_thread=False)  # Conexión a la base de datos
with conn:
    # Tabla para guardar el historial de conversaciones
    conn.execute('''
    CREATE TABLE IF NOT EXISTS historial (
        numero TEXT,
        rol TEXT,
        mensaje TEXT
    )
    ''')
    # Tabla para controlar el límite de mensajes por usuario y hora
    conn.execute('''
    CREATE TABLE IF NOT EXISTS limites (
        numero TEXT,
        fecha TEXT,
        conteo INTEGER
    )
    ''')

# Inicializamos la app Flask
app = Flask(__name__)

# Ruta para comprobar si el servidor está activo
@app.route('/')
def home():
    return "✅ Servidor activo."

# Ruta principal para el webhook de WhatsApp (maneja GET para verificación y POST para recibir mensajes)
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Verificación de WhatsApp con los datos enviados en la URL
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200  # Retorna el challenge si el token es correcto
        else:
            return 'Forbidden', 403  # Si no coincide, rechaza la verificación

    elif request.method == 'POST':
        # Procesa los mensajes recibidos en el webhook
        data = request.get_json()  # Obtiene los datos en formato JSON

        try:
            # Verifica que el mensaje recibido es un mensaje de usuario
            if "messages" in data["entry"][0]["changes"][0]["value"]:
                numero = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]  # Número de teléfono del remitente
                pregunta = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]  # Texto del mensaje recibido
                
                print(f"✅ Mensaje recibido de {numero}: {pregunta}")

                # Verifica si el usuario ha superado el límite de mensajes por hora
                if supera_limite_mensajes(numero):
                    mensaje_limite = (
                        "Entiendo que no se ha resuelto su incidencia. Por favor, póngase en contacto contacto con uno de nuestros agentes via Email: soporte@sodire.es"
                    )
                    enviar_mensaje_whatsapp(numero, mensaje_limite)
                    return jsonify({"status": "limite alcanzado"}), 200

                # Si es la primera vez que escribe, se le envía un saludo
                if es_nuevo_usuario(numero):
                    saludo = "¡Hola! soy el tecnico virtual de Sodire, en qué te puedo ayudar?"
                    guardar_mensaje_sqlite(numero, "assistant", saludo)
                    enviar_mensaje_whatsapp(numero, saludo)

                # Guarda el mensaje del usuario en la base de datos
                guardar_mensaje_sqlite(numero, "user", pregunta)

                # Recupera el historial de la conversación con este usuario
                historial = obtener_historial_sqlite(numero)

                # Busca los fragmentos relevantes a la pregunta recibida
                fragmentos = buscar_fragmentos_parecidos(pregunta, top_k=3)
                contexto = "\n\n".join([f"[{f['documento']}] {f['contenido']}" for f in fragmentos])

                # Añade el contexto al historial como system para que la IA lo tenga en cuenta
                historial.append({
                    "role": "user",
                    "content": f"""
                "Actúas como un agente de soporte técnico especializado en soluciones digitales para hostelería, representando a Sodire. Tu función principal es ayudar a resolver dudas e incidencias relacionadas con los sistemas TPV de L' Addition o LastApp, herramientas de gestión y automatizaciones implementadas en negocios de restauración.
                Usa los fragmentos de contexto sólo como guía para asegurar la exactitud, pero no los copies literalmente. Integra la información de forma que sea útil, breve y concisa (máximo 3-4 frases), con un estilo profesional, directo y empático. Nunca uses un tono coloquial ni excesivamente técnico, y evita adornos o frases innecesarias. Prioriza la eficiencia y la utilidad.
                Si la pregunta no está relacionada con estos temas o no puedes ayudar, responde con un mensaje breve y conciso indicando que no puedes ayudar con eso, sin explicaciones innecesarias ni frases largas.
                Enfócate en resolver el asunto, ya que el interlocutor estará nervioso y con poco tiempo para leer texto que no aporte valor."

                Fragmentos:
                {contexto}

                Pregunta:
                {pregunta}
                """
                })

                # Llama a la API de OpenAI para generar una respuesta
                respuesta = client.chat.completions.create(
                    model="gpt-4o",
                    messages=historial,
                    temperature=0.4,  # Controla la creatividad de la respuesta
                    max_tokens=150  # Limita la longitud de la respuesta
                )

                texto_respuesta = respuesta.choices[0].message.content.strip()  # Extrae la respuesta
                guardar_mensaje_sqlite(numero, "assistant", texto_respuesta)  # Guarda la respuesta
                enviar_mensaje_whatsapp(numero, texto_respuesta)  # Envía la respuesta por WhatsApp
                print("💬 Respuesta generada por la IA:", texto_respuesta)

            else:
                print("ℹ️ No es un mensaje de usuario. Ignorando.")

        except Exception as e:
            print("❌ Error al procesar el mensaje:", e)

        return jsonify({"status": "ok"}), 200

# Comprueba si es la primera vez que el usuario escribe
def es_nuevo_usuario(numero):
    with conn:
        fila = conn.execute(
            'SELECT COUNT(*) FROM historial WHERE numero = ?', (numero,)
        ).fetchone()
    return fila[0] == 0

# Guarda un mensaje (usuario o asistente) en la base de datos
def guardar_mensaje_sqlite(numero, rol, mensaje):
    with conn:
        conn.execute(
            'INSERT INTO historial (numero, rol, mensaje) VALUES (?, ?, ?)',
            (numero, rol, mensaje)
        )

# Recupera el historial de mensajes de un usuario
def obtener_historial_sqlite(numero):
    with conn:
        filas = conn.execute(
            'SELECT rol, mensaje FROM historial WHERE numero = ?',
            (numero,)
        ).fetchall()
    if not filas:
        # Si no hay historial, añade un mensaje inicial de system
        return [{"role": "system", "content": "Eres un asistente técnico de la empresa Sodire."}]
    historial = [{"role": rol, "content": mensaje} for rol, mensaje in filas]
    return historial

# Verifica si el usuario ha superado el límite de 10 mensajes por hora
def supera_limite_mensajes(numero):
    ahora = datetime.datetime.now()
    hora_actual = ahora.strftime("%Y-%m-%d %H")  # Formato de fecha y hora actual

    with conn:
        fila = conn.execute(
            'SELECT conteo FROM limites WHERE numero = ? AND fecha = ?',
            (numero, hora_actual)
        ).fetchone()

        if fila:
            conteo = fila[0]
            if conteo >= 3:
                return True  # Ha superado el límite
            else:
                # Incrementa el conteo
                conn.execute(
                    'UPDATE limites SET conteo = conteo + 1 WHERE numero = ? AND fecha = ?',
                    (numero, hora_actual)
                )
        else:
            # Primer mensaje de la hora: crea registro
            conn.execute(
                'INSERT INTO limites (numero, fecha, conteo) VALUES (?, ?, ?)',
                (numero, hora_actual, 1)
            )
    return False

# Envía un mensaje de texto por la API de WhatsApp
def enviar_mensaje_whatsapp(destinatario, mensaje):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": "Bearer " + WHATSAPP_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": destinatario,
        "type": "text",
        "text": {
            "body": mensaje
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print("🔴 Código de estado:", response.status_code)
    print("🔴 Respuesta completa:", response.text)
    if response.ok:
        print("✅ Mensaje enviado correctamente.")
    else:
        print("❌ Error al enviar el mensaje.")

# Arranca la app Flask en el puerto 5000, accesible desde cualquier IP
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
