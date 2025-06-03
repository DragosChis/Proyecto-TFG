import os
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Cargamos las variables de entorno desde el archivo .env
load_dotenv()
# Configuramos la clave de API para el cliente Gemini
genai.configure(api_key=os.getenv("API_KEY"))


def resumir_conversacion(historial):
    """
    Procesa un historial de chat (lista de líneas o string con saltos de línea)
    y genera un resumen estructurado, eliminando duplicados y etiquetas internas.
    Devuelve un string con la cabecera de resumen y bloques de diálogo relevantes.
    """
    # Si no hay historial, devolvemos mensaje estándar
    if not historial:
        return "Sin historial disponible."

    # 1) Dividir el historial en líneas
    #    - Si se recibe un string, hacemos split por '\n'.
    #    - Si ya es lista, lo usamos directamente.
    if isinstance(historial, str):
        raw_lines = historial.split('\n')
    else:
        raw_lines = historial

    # 2) Normalizar etiquetas:
    #    Reemplazamos prefijos internos ([Pregunta]:, [Respuesta]:, Chatbot:, Usuario:)
    #    por "Asistente Virtual:" o "Cliente:". Eliminamos líneas vacías.
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
            # Si la línea no comienza con ninguna etiqueta pero no está vacía, la conservamos
            if line:
                normalized.append(line)

    # 3) Construir bloques de diálogo:
    #    Agrupamos líneas que empiezan con "Asistente Virtual:" o "Cliente:" en bloques
    oradores = ("Asistente Virtual:", "Cliente:")
    bloques = []
    bloque_actual = ""
    for linea in normalized:
        if linea.startswith(oradores):
            # Si ya teníamos un bloque en construcción, lo cerramos y lo añadimos a la lista
            if bloque_actual:
                bloques.append(bloque_actual.strip())
            # Iniciamos un nuevo bloque con la línea actual
            bloque_actual = linea
        else:
            # Si la línea no empieza con etiqueta, se añade al bloque actual con salto
            bloque_actual += "\n" + linea
    # Al finalizar, añadimos el último bloque si existe
    if bloque_actual:
        bloques.append(bloque_actual.strip())

    # 4) Filtrar ruido:
    #    Eliminamos bloques que contengan "Opciones" o "Usuario seleccionó" (mensajes internos)
    bloques = [b for b in bloques if not ("Opciones" in b or "Usuario seleccionó" in b)]

    # 5) Eliminar duplicados:
    #    - Evitar bloques idénticos adyacentes.
    #    - Para bloques de asistente, evitar repetidos si ya aparecieron antes.
    vistos_preguntas = set()
    bloques_unicos = []
    prev_bloque = None
    for b in bloques:
        # Si es exactamente igual al bloque anterior, lo saltamos
        if b == prev_bloque:
            continue
        if b.startswith("Asistente Virtual:"):
            # Para bloques del asistente, sólo añadir si no se ha visto antes
            if b not in vistos_preguntas:
                vistos_preguntas.add(b)
                bloques_unicos.append(b)
        else:
            # Para líneas de cliente, siempre las añadimos (pueden repetirse)
            bloques_unicos.append(b)
        prev_bloque = b

    # 6) Montar texto final:
    #    - Agregamos cabecera con fecha y título.
    #    - Insertamos bloques con saltos de línea adecuados entre ellos.
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    cabecera = f"=== Resumen del flujo de atención ===\nFecha: {fecha}\n\n"
    # Si no quedan bloques únicos, devolvemos mensaje de ausencia de interacciones
    if not bloques_unicos:
        return cabecera + "Sin interacciones relevantes registradas."

    resultado = ""
    for i, bloque in enumerate(bloques_unicos):
        resultado += bloque
        # Decidir cuántos saltos de línea después de cada bloque
        if i + 1 < len(bloques_unicos):
            siguiente = bloques_unicos[i + 1]
            # Si un bloque de asistente va seguido de cliente, sólo un salto
            if bloque.startswith("Asistente Virtual:") and siguiente.startswith("Cliente:"):
                resultado += "\n"
            else:
                # Si es otro caso (cliente->asistente o asistente->asistente…), dos saltos
                resultado += "\n\n"

    # Devolver cabecera + diálogo formateado
    return cabecera + resultado


def resumir_conversacion_prosa(historial: str) -> str:
    """
    Genera un resumen en prosa de los puntos más importantes de la conversación
    usando Gemini (modelo 'gemini-1.5-flash-latest'). El resumen sigue un tono
    formal y estructurado, dirigido al cliente, con salutación y despedida.
    """
    # Si no hay historial, devolvemos mensaje estándar
    if not historial:
        return "Sin historial disponible."

    # Construir el prompt completo que se pasará a Gemini
    prompt = (
        "Eres un asesor profesional de atención al cliente de Sodire. Siempre que generes un resumen dirigido al cliente, usa exactamente esta estructura y tono:"
        "   Estimado cliente:"
        "   Gracias por contactar con nosotros para informarse sobre la digitalización de su negocio."
        "   Le mostramos un resumen detallado de la conversacion que ha tenido con nuestro asistente virtual:"
        "   En base a esta información uno de nuestros comerciales se pondrá en contacto con usted en breve para ofrecerle más detalles."
        "   Por favor, no dudes en contactar con nosotros si tienes alguna pregunta adicional."
        "   Atentamente,"
        "   El equipo Sodire."
        f"{historial}"
    )

    # Instanciar el modelo Gemini Flash (versión gratuita)
    model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
    # Generar el contenido con temperatura baja para mayor coherencia
    resp = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.2,
            max_output_tokens=512
        )
    )

    # Devolver sólo el texto generado, sin espacios extra
    return getattr(resp, "text", "").strip()
