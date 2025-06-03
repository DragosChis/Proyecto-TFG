import os
import mysql.connector
import openai
from configuracion.config import db_config, api_key
from database import get_keywords_full

# Configurar OpenAI
openai.api_key = api_key


def detectar_palabras_en_historial(historial, palabras_clave):
    """
    Recorre el historial de mensajes y busca coincidencias con la lista de palabras clave.
    - historial: lista de strings (mensajes del chat).
    - palabras_clave: lista de diccionarios con 'id' y 'palabra'.
    Devuelve una lista de diccionarios (palabras clave) que aparecen en el historial.
    """
    texto = ' '.join(historial).lower()
    coincidencias = []
    for palabra in palabras_clave:
        if palabra['palabra'].lower() in texto:
            coincidencias.append(palabra)
    return coincidencias


def obtener_info_relacionada(palabras_detectadas):
    """
    Consulta la base de datos para obtener información de productos, subcategorías
    y servicios digitales asociados a cada palabra clave detectada.
    - palabras_detectadas: lista de diccionarios con 'id' y 'palabra'.
    Devuelve tres diccionarios: productos, subcategorias y servicios,
    donde la clave es el nombre y el valor es la descripción.
    """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        productos = {}
        subcategorias = {}
        servicios = {}

        for palabra in palabras_detectadas:
            palabra_id = palabra['id']

            # Obtener productos relacionados
            cursor.execute("""
                SELECT p.nombre, p.descripcion
                FROM productos p
                JOIN palabras_clave_productos pkp ON p.id = pkp.producto_id
                WHERE pkp.palabra_id = %s
            """, (palabra_id,))
            for prod in cursor.fetchall():
                productos[prod['nombre']] = prod['descripcion']

            # Obtener subcategorías relacionadas
            cursor.execute("""
                SELECT s.nombre, s.descripcion
                FROM subcategorias s
                JOIN palabras_clave_subcategorias pcs ON s.id = pcs.subcategoria_id
                WHERE pcs.palabra_id = %s
            """, (palabra_id,))
            for sub in cursor.fetchall():
                subcategorias[sub['nombre']] = sub['descripcion']

            # Obtener servicios digitales relacionados
            cursor.execute("""
                SELECT s.nombre, s.descripcion
                FROM servicios_digitales s
                JOIN palabras_clave_servicios pcs ON s.id = pcs.servicio_id
                WHERE pcs.palabra_id = %s
            """, (palabra_id,))
            for srv in cursor.fetchall():
                servicios[srv['nombre']] = srv['descripcion']

        conn.close()
        return productos, subcategorias, servicios

    except Exception as e:
        print("Error en obtener_info_relacionada:", e)
        return {}, {}, {}


def construir_contexto_ia(productos, subcategorias, servicios, palabras_detectadas):
    """
    Construye bloques de texto que servirán como contexto para alimentar al modelo IA.
    - productos, subcategorias, servicios: diccionarios con nombre->descripción.
    - palabras_detectadas: lista de diccionarios con 'id' y 'palabra'.
    Agrega una recomendación adicional si se detectan términos relacionados con terraza o amplificador.
    Devuelve un string con el contexto completo, o un mensaje si no hay información.
    """
    bloques = []

    if productos:
        bloque_productos = "Productos relacionados:\n"
        for nombre, descripcion in productos.items():
            bloque_productos += f"- {nombre}: {descripcion.strip()}\n"
        bloques.append(bloque_productos)

    if subcategorias:
        bloque_subcats = "Categorías relacionadas:\n"
        for nombre, descripcion in subcategorias.items():
            bloque_subcats += f"- {nombre}: {descripcion.strip()}\n"
        bloques.append(bloque_subcats)

    if servicios:
        bloque_servicios = "Servicios digitales relacionados:\n"
        for nombre, descripcion in servicios.items():
            bloque_servicios += f"- {nombre}: {descripcion.strip()}\n"
        bloques.append(bloque_servicios)

    palabras = [p['palabra'].lower() for p in palabras_detectadas]
    if "terraza" in palabras or "amplificador" in palabras:
        bloques.append(
            "Recomendación:\n"
            "Si la terraza es de más de 20 metros, se recomienda instalar un amplificador de señal para asegurar el buen funcionamiento del sistema."
        )

    if not bloques:
        return "No se detectó información útil en la conversación actual."

    return "\n".join(bloques).strip()


def generar_respuesta_ia(prompt_user, chat_history):
    """
    Genera una respuesta utilizando el modelo de IA de OpenAI a partir de la consulta del usuario.
    - prompt_user: string con la consulta del cliente.
    - chat_history: lista de strings con el historial de conversación (preguntas/respuestas).
    Pasos:
      1. Recuperar todas las palabras clave de la base de datos.
      2. Detectar cuáles aparecen en el historial.
      3. Obtener info relacionada (productos, subcategorías, servicios).
      4. Construir contexto de IA a partir de esa información.
      5. Montar el prompt final con el contexto y la consulta del cliente.
      6. Llamar a OpenAI (modelo 'gpt-3.5-turbo') para generar la respuesta.
    Devuelve:
      - respuesta_texto: string con la respuesta generada (o None si hubo error).
      - error: mensaje de error en caso de fallo (o None si todo OK).
    """
    if not prompt_user:
        return None, "No se proporcionó una consulta válida."

    palabras_clave = get_keywords_full()
    palabras_detectadas = detectar_palabras_en_historial(chat_history, palabras_clave)

    productos, subcategorias, servicios = obtener_info_relacionada(palabras_detectadas)

    contexto = construir_contexto_ia(productos, subcategorias, servicios, palabras_detectadas)

    prompt = (
        "Eres el asistente virtual de Sodire. Utiliza solo la información que aparece a continuación para responder al cliente.\n\n"
        f"{contexto}\n\n"
        f"Cliente: {prompt_user}\n"
        "Responde de forma clara, profesional y breve. No inventes nada fuera de la información proporcionada."
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente útil de Sodire."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=80,
            n=1
        )
        respuesta_texto = response.choices[0].message.content.strip()
        if not respuesta_texto:
            return None, "Respuesta vacía del modelo"
        return respuesta_texto, None

    except Exception as e:
        print("Error en generar_respuesta_ia:", e)
        return None, "Error al generar respuesta con OpenAI"


def generar_prompt_ia(prompt_user, chat_history):
    """
    Genera únicamente el prompt que se enviaría a OpenAI, sin invocar al modelo.
    - prompt_user: string con la consulta del cliente.
    - chat_history: lista de strings con el historial.
    Devuelve el prompt completo (string) o None si no hay consulta válida.
    Útil para depuración o para enviar el prompt a otra parte.
    """
    if not prompt_user:
        return None

    palabras_clave = get_keywords_full()
    palabras_detectadas = detectar_palabras_en_historial(chat_history, palabras_clave)

    productos, subcategorias, servicios = obtener_info_relacionada(palabras_detectadas)

    contexto = construir_contexto_ia(productos, subcategorias, servicios, palabras_detectadas)

    prompt = (
        "Eres el asistente virtual de Sodire. Utiliza solo la información que aparece a continuación para responder al cliente.\n\n"
        f"{contexto}\n\n"
        f"Cliente: {prompt_user}\n"
        "Responde de forma clara, profesional y breve. No inventes nada fuera de la información proporcionada."
    )

    return prompt
