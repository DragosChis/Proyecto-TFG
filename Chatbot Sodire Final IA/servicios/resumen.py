import os
from datetime import datetime
from dotenv import load_dotenv
import openai

# Cargamos las variables de entorno desde el archivo .env
load_dotenv()

# Configuramos la clave de API para OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")


def resumir_conversacion(historial):
    """
    Procesa un historial de chat (lista de líneas o string con saltos de línea)
    y genera un resumen estructurado, eliminando duplicados y etiquetas internas.
    Devuelve un string con la cabecera de resumen y bloques de diálogo relevantes.
    """
    if not historial:
        return "Sin historial disponible."

    # 1) Dividir el historial en líneas
    if isinstance(historial, str):
        raw_lines = historial.split('\n')
    else:
        raw_lines = historial

    # 2) Normalizar etiquetas:
    normalized = []
    for l in raw_lines:
        line = l.strip()
        if line.startswith("[Pregunta]:"):
            normalized.append(line.replace("[Pregunta]:", "Asistente Virtual:"))
        elif line.startswith("[Respuesta]:"):
            normalized.append(line.replace("[Respuesta]:", "Cliente:"))
        elif line.startswith("Chatbot:"):
            normalized.append(line.replace("Chatbot:", "Asistente Virtual:"))
        elif line.startswith("Usuario:"):
            normalized.append(line.replace("Usuario:", "Cliente:"))
        else:
            if line:
                normalized.append(line)

    # 3) Construir bloques de diálogo:
    oradores = ("Asistente Virtual:", "Cliente:")
    bloques = []
    bloque_actual = ""
    for linea in normalized:
        if linea.startswith(oradores):
            if bloque_actual:
                bloques.append(bloque_actual.strip())
            bloque_actual = linea
        else:
            bloque_actual += "\n" + linea
    if bloque_actual:
        bloques.append(bloque_actual.strip())

    # 4) Filtrar ruido:
    bloques = [b for b in bloques if not ("Opciones" in b or "Usuario seleccionó" in b)]

    # 5) Eliminar duplicados:
    vistos_preguntas = set()
    bloques_unicos = []
    prev_bloque = None
    for b in bloques:
        if b == prev_bloque:
            continue
        if b.startswith("Asistente Virtual:"):
            if b not in vistos_preguntas:
                vistos_preguntas.add(b)
                bloques_unicos.append(b)
        else:
            bloques_unicos.append(b)
        prev_bloque = b

    # 6) Montar texto final:
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    cabecera = f"=== Resumen del flujo de atención ===\nFecha: {fecha}\n\n"
    if not bloques_unicos:
        return cabecera + "Sin interacciones relevantes registradas."

    resultado = ""
    for i, bloque in enumerate(bloques_unicos):
        resultado += bloque
        if i + 1 < len(bloques_unicos):
            siguiente = bloques_unicos[i + 1]
            # Si Asistente->Cliente, solo un salto; en otros casos, dos saltos
            if bloque.startswith("Asistente Virtual:") and siguiente.startswith("Cliente:"):
                resultado += "\n"
            else:
                resultado += "\n\n"

    return cabecera + resultado


def resumir_conversacion_prosa(historial: str) -> str:
    """
    Genera un resumen en prosa de los puntos más importantes de la conversación
    usando OpenAI. El resumen sigue un tono formal y estructurado, dirigido al cliente,
    con salutación y despedida.
    """
    if not historial:
        return "Sin historial disponible."

    # 1) Construimos un prompt explícito para "resumir" en prosa
    prompt = (
        "Eres un asesor profesional de atención al cliente de Sodire.\n"
        "A continuación tienes el historial completo de la conversación entre el cliente y el asistente:\n\n"
        f"{historial}\n\n"
        "**Tu tarea**: resume en prosa los puntos claves de esta conversación, "
        "siguiendo exactamente esta estructura y tono (sin copiar literalmente):\n\n"
        "Estimado cliente:\n"
        "Gracias por contactar con nosotros para informarse sobre la digitalización de su negocio.\n"
        "• [Aquí va el resumen conciso en prosa de lo tratado]\n"
        "• [Añade únicamente lo más importante: necesidades, servicios solicitados, información relevante]\n"
        "En base a esta información, uno de nuestros comerciales se pondrá en contacto con usted en breve para ofrecerle más detalles.\n"
        "Por favor, no dudes en contactar con nosotros si tienes alguna pregunta adicional.\n"
        "Atentamente,\n"
        "El equipo Sodire."
    )

    try:
        # 2) Llamada a la API de OpenAI con la interfaz 1.x
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente útil de Sodire."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=512
        )
        # 3) Devolvemos únicamente el texto generado (ya resumido)
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Error en resumir_conversacion_prosa:", e)
        return ""
