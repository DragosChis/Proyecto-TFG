from flask import Blueprint, request, jsonify, make_response
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import re 

# ── Cargar variables de entorno desde .env y configurar Gemini ───────────────────
# Esto permite utilizar la API_KEY almacenada en el archivo .env para las llamadas a Gemini.
load_dotenv()
genai.configure(api_key=os.getenv("API_KEY"))

# ── Importar servicios de resumen, presupuesto, análisis y envío de correos ───────
# Estos módulos encapsulan la lógica de negocio para generar resúmenes, presupuestos
# y gestionar el análisis del historial y el envío de correos.
from servicios.resumen import resumir_conversacion, resumir_conversacion_prosa
from servicios.presupuesto import generar_presupuesto_pdf, generar_presupuesto_final
from servicios.analisis import extraer_parametros_del_historial
from utilidades.correo import enviar_correos, enviar_correo_soporte
from utilidades.correo import enviar_correo_digitalizar
from database import get_keywords
from servicios.respuesta_ia import generar_respuesta_ia, generar_prompt_ia
from database import get_servicios_digitales_info

# Crear el Blueprint para agrupar las rutas de la API
api_blueprint = Blueprint('api', __name__)

# ── Mapeo de IDs textuales de data_digitalizar.json a IDs numéricos de la base ────
# Este diccionario permite traducir los identificadores legibles (strings) a los que
# utiliza la tabla de servicios en la base de datos.
SERVICE_ID_MAP = {
    "digitalizacion_reservas_online":  1,
    "digitalizacion_delivery":          2,
    "digitalizacion_stock_proveedores": 4,
    "digitalizacion_rrss_web":          5,
    "digitalizacion_automatizacion_tareas_administrativas": 7,
    "digitalizacion_agentes_ia":        6
    # …añade aquí el resto según tu tabla…
}

# ======================= ENDPOINT: /resumen-digital =========================
@api_blueprint.route('/resumen-digital', methods=['POST'])
def resumen_digital():
    """
    Genera un resumen de los servicios digitales seleccionados por el usuario.
    Recibe en el payload un historial y una lista de IDs textuales de servicios,
    los convierte a IDs numéricos, obtiene la información de precios y herramientas,
    y construye un texto final con la introducción, precios y, si existe, descripción
    de herramientas.
    """
    data        = request.get_json() or {}
    raw_ids     = data.get("servicios", [])
    historial   = data.get("historial", "")

    # ↳ Mapear identificadores textuales a IDs numéricos validos
    ids_num = [SERVICE_ID_MAP[x] for x in raw_ids if x in SERVICE_ID_MAP]

    # ↳ Obtener los bloques de texto con precios y herramientas de los servicios
    bloque_precios, bloque_herr = get_servicios_digitales_info(ids_num)

    # ----------------- Construcción del texto final -----------------
    # · Introducción fija explicativa
    intro = (
        "En base a tus selecciones, te muestro el resumen de los "
        "servicios digitales marcados:"
    )

    # · El cuerpo contiene la información de precios, ya formateada
    cuerpo = bloque_precios

    # · Solo incluir sección de herramientas si bloque_herr no está vacío
    if bloque_herr:
        # Convertir la primera letra del bloque a minúscula
        bloque_herr = bloque_herr[0].lower() + bloque_herr[1:]
        # Asegurar que después de la primera coma + espacio, el siguiente carácter sea minúscula
        bloque_herr = re.sub(
            r",\s+([A-ZÁÉÍÓÚÜÑ])",
            lambda m: ", " + m.group(1).lower(),
            bloque_herr,
            count=1  # solo la primera coincidencia
        )

        herramientas = (
            "\n\nEn cuanto a las herramientas con las que trabajamos, debes saber que, "
            f"{bloque_herr}"
        )
    else:
        herramientas = ""

    # · Componer el resumen final, concatenando intro, cuerpo y herramientas
    resumen = f"{intro}\n\n{cuerpo}{herramientas}"

    return jsonify({"summary": resumen})


# ======================= ENDPOINT: /preview-pdf =========================
@api_blueprint.route('/preview-pdf', methods=['POST'])
def preview_pdf():
    """
    Genera un PDF de vista previa del presupuesto basado en el historial y datos del cliente.
    1. Extrae parámetros del historial (tipo de negocio).
    2. Llama a generar_presupuesto_final para obtener texto descriptivo e items.
    3. Llama a generar_presupuesto_pdf para construir el PDF en bytes.
    4. Devuelve el PDF en la respuesta HTTP con los encabezados adecuados.
    """
    data = request.get_json()

    # Parámetros recibidos en el JSON
    historial          = data.get('historial', '')
    nombre             = data.get('nombre', 'Cliente')
    cliente_negocio    = data.get('negocio', '')
    telefono           = data.get('telefono', '')
    cliente_ciudad     = data.get('ciudad', '')
    cliente_provincia  = data.get('provincia', '')
    cliente_cp         = data.get('cp', '')

    # Extraer tipo de negocio a partir del historial
    params = extraer_parametros_del_historial(historial)
    tipo_negocio = params.get("tipo_negocio", "No especificado")

    # Generar texto descriptivo (pres_text) e items a partir del historial y nombre
    pres_text, items = generar_presupuesto_final(historial, nombre, cliente_negocio)

    # Construir el PDF utilizando los datos obtenidos
    pdf_bytes = generar_presupuesto_pdf(
        pres_text,
        items,
        tipo_negocio=tipo_negocio,
        fecha=None,
        cliente_nombre=nombre,
        cliente_negocio=cliente_negocio,
        cliente_telefono=telefono,
        cliente_ciudad=cliente_ciudad,
        cliente_provincia=cliente_provincia,
        cliente_cp=cliente_cp
    )

    # Si no se pudo generar el PDF, devolver error 500
    if not pdf_bytes:
        return jsonify({'error': 'No se pudo generar el PDF'}), 500

    # Construir la respuesta con el PDF
    response = make_response(pdf_bytes)
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'inline; filename="preview.pdf"')
    return response


# ======================= ENDPOINT: /generate =========================
@api_blueprint.route('/generate', methods=['POST'])
def generate_response():
    """
    Recibe un prompt y el historial de chat, y genera una respuesta usando Gemini.
    1. Valida que prompt_user no esté vacío.
    2. Llama a generar_respuesta_ia que encapsula toda la lógica de contexto y Gemini.
    3. Devuelve la respuesta en formato JSON o el error correspondiente.
    """
    try:
        data = request.get_json()
        prompt_user = data.get('prompt', '').strip()
        chat_history = data.get('chat_history', [])

        if not prompt_user:
            return jsonify({'error': 'No se proporcionó una consulta válida.'}), 400

        # Obtener la respuesta y posible error de la función modular
        respuesta, error = generar_respuesta_ia(prompt_user, chat_history)

        if error:
            return jsonify({'error': error}), 500

        return jsonify({'response': respuesta})
    except Exception as e:
        print("Error en generate_response:", e)
        return jsonify({'error': 'Error procesando solicitud.'}), 500


# ======================= ENDPOINT: /debug-prompt =========================
@api_blueprint.route('/debug-prompt', methods=['POST'])
def debug_prompt():
    """
    Endpoint para devolver el prompt final que se enviaría a Gemini, sin generar la respuesta.
    Útil para depuración y revisión de cómo se construye el prompt con contexto.
    """
    try:
        data = request.get_json()
        prompt_user = data.get('prompt', '').strip()
        chat_history = data.get('chat_history', [])

        prompt_final = generar_prompt_ia(prompt_user, chat_history)
        if not prompt_final:
            return jsonify({'error': 'No se pudo generar el prompt'}), 400

        return jsonify({'prompt_final': prompt_final})
    except Exception as e:
        print("Error en debug_prompt:", e)
        return jsonify({'error': 'Error generando prompt de prueba'}), 500


# ======================= ENDPOINT: /keywords =========================
@api_blueprint.route('/keywords', methods=['GET'])
def get_keywords_route():
    """
    Devuelve la lista completa de palabras clave almacenadas en la base de datos.
    Utilizado en el frontend para autocompletar o sugerencias en el campo de entrada.
    """
    try:
        palabras = get_keywords()
        return jsonify({'keywords': palabras})
    except Exception as e:
        print("Error fetching keywords:", e)
        return jsonify({'keywords': []}), 500


# ======================= ENDPOINT: /enviar-formulario =========================
@api_blueprint.route('/enviar-formulario', methods=['POST'])
def enviar_formulario():
    """
    Recibe los datos del formulario comercial, genera un resumen y presupuesto,
    construye el PDF y envía todo por correo.
    1. Extraer datos básicos del cliente y historial.
    2. Validar que exista historial.
    3. Generar resumen de conversación.
    4. Generar presupuesto final y PDF.
    5. Enviar correos con resumen y PDF adjunto.
    """
    try:
        data = request.get_json()
        nombre     = data.get('nombre', '')
        apellidos  = data.get('apellidos', '')
        negocio    = data.get('negocio', '')
        ciudad     = data.get('ciudad', '')
        provincia  = data.get('provincia', '')
        cp         = data.get('cp', '')
        email      = data.get('email', '')
        telefono   = data.get('telefono', '')
        asunto     = data.get('asunto', '')
        historial  = data.get('historial', '')

        if not historial:
            return jsonify({'error': 'No se proporcionó historial'}), 400

        # Generar resumen de texto plano de la conversación
        resumen = resumir_conversacion(historial)

        # Extraer parámetros para el presupuesto (por ejemplo, tipo de negocio)
        params = extraer_parametros_del_historial(historial)
        tipo_negocio = params.get("tipo_negocio", "No especificado")

        # Generar el presupuesto (texto + lista de items)
        pres_text, items = generar_presupuesto_final(
            historial,
            f"{nombre} {apellidos}",
            negocio
        )
        # Construir el PDF del presupuesto completo
        pdf_bytes = generar_presupuesto_pdf(
            pres_text,
            items,
            tipo_negocio=tipo_negocio,
            fecha=None,
            cliente_nombre=f"{nombre} {apellidos}",
            cliente_negocio=negocio,
            cliente_telefono=telefono,
            cliente_ciudad=ciudad,
            cliente_provincia=provincia,
            cliente_cp=cp,
            recomendacion_extra=(
                "Dado que has indicado que el punto más lejano de tu terraza "
                "está a una distancia mayor a 20 metros respecto al router, "
                "te recomendamos instalar un amplificador de señal..."
                if extraer_parametros_del_historial(historial).get("necesita_amplificador")
                else ""
            )
        )

        # Enviar correos con la información: al cliente y al equipo interno
        exito = enviar_correos(
            nombre, apellidos, negocio, ciudad, provincia, cp,
            email, telefono, asunto,
            resumen, pdf_bytes
        )

        if not exito:
            return jsonify({'error': 'No se pudo enviar el correo'}), 500

        return jsonify({'message': 'Formulario enviado correctamente'})
    except Exception as e:
        print("Error en enviar_formulario:", e)
        return jsonify({'error': 'Error procesando formulario'}), 500


# ================ ENDPOINT: /enviar-formulario-soporte =====================
@api_blueprint.route('/enviar-formulario-soporte', methods=['POST'])
def enviar_formulario_soporte():
    """
    Recibe los datos del formulario de soporte técnico, genera un resumen de la conversación
    y envía un correo al equipo de soporte con la información completa.
    """
    try:
        data = request.get_json()
        nombre        = data.get('nombre', '')
        apellidos     = data.get('apellidos', '')
        email         = data.get('email', '')
        telefono      = data.get('telefono', '')
        local         = data.get('local', '')
        tipo_consulta = data.get('tipo_consulta', '')
        mensaje       = data.get('mensaje', '')
        historial     = data.get('historial', '')

        if not historial:
            return jsonify({'error': 'No se proporcionó historial'}), 400

        # Generar resumen de la conversación para adjuntar en el correo
        resumen = resumir_conversacion(historial)

        # Enviar correo de soporte con los datos proporcionados y el resumen
        exito = enviar_correo_soporte(
            nombre, apellidos, email, telefono, local, mensaje, resumen, tipo_consulta
        )

        if not exito:
            return jsonify({'error': 'No se pudo enviar el correo de soporte'}), 500

        return jsonify({'message': 'Formulario de soporte enviado correctamente'})
    except Exception as e:
        print("Error en enviar_formulario_soporte:", e)
        return jsonify({'error': 'Error procesando formulario de soporte'}), 500


# ============ ENDPOINT: /enviar-formulario-digitalizar =====================
@api_blueprint.route('/enviar-formulario-digitalizar', methods=['POST'])
def enviar_formulario_digitalizar():
    """
    Recibe los datos del formulario de digitalización, genera:
    1. Un mini-resumen de servicios seleccionados (precios y herramientas).
    2. Un resumen en prosa para el cliente usando Gemini.
    3. Un resumen estructurado para el equipo comercial.
    Limpia partes fijas de bienvenida/despedida del resumen en prosa y construye
    el texto final para el cliente. Finalmente, envía un correo con ambos resúmenes.
    """
    try:
        data       = request.get_json()
        nombre     = data.get('nombre', '')
        apellidos  = data.get('apellidos', '')
        negocio    = data.get('negocio', '')
        provincia  = data.get('provincia', '')
        email      = data.get('email', '')
        telefono   = data.get('telefono', '')
        historial  = data.get('historial', '')

        if not historial:
            return jsonify({'error': 'No se proporcionó historial'}), 400

        # ——— Recuperar servicios seleccionados y generar mini-resumen ———
        raw_ids = data.get('servicios', [])
        ids_num = [SERVICE_ID_MAP[x] for x in raw_ids if x in SERVICE_ID_MAP]
        bloque_precios, bloque_herr = get_servicios_digitales_info(ids_num)
        resumen_servicios = (
            "En base a tus selecciones, te muestro el resumen de los servicios digitales marcados:\n\n"
            + bloque_precios
        )
        if bloque_herr:
            resumen_servicios += "\n\nHerramientas: " + bloque_herr

        # ✅ Generar resumen en prosa usando Gemini (gratuito Flash)
        resumen_cliente_prosa = resumir_conversacion_prosa(historial)

        # ——— Eliminar texto fijo de bienvenida y despedida intermedia ———
        # Se buscan patrones de saludo y despedida para quedarnos solo con contenido relevante.
        for frase in [
            r"Gracias por contactar con nosotros para informarse sobre la digitalización de su negocio\.",
            r"Le mostramos un resumen detallado de la conversación que ha tenido con nuestro asistente virtual:",
            r"En base a esta información uno de nuestros comerciales se pondrá en contacto con usted en breve para ofrecerle más detalles\.",
            r"Por favor, no dudes en contactar con nosotros si tienes alguna pregunta adicional\."
        ]:
            resumen_cliente_prosa = re.sub(frase + r"\n*", "", resumen_cliente_prosa)

        # ——— Extraer cierre (“Atentamente…”) de la prosa ———
        cierre = ""
        prosa_sin_cierre = resumen_cliente_prosa
        if "Atentamente" in resumen_cliente_prosa:
            idx = resumen_cliente_prosa.index("Atentamente")
            prosa_sin_cierre = resumen_cliente_prosa[:idx].strip()
            cierre = resumen_cliente_prosa[idx:].strip()

        # ——— Montar el texto final para el cliente ———
        texto_para_cliente = (
            f"{prosa_sin_cierre}\n\n"
            f"{resumen_servicios}\n\n"
            f"{cierre}"
        )

        # ✅ Generar resumen estructurado para el comercial
        resumen_comercial = resumir_conversacion(historial)

        # ——— Fallback: si no hay interacciones relevantes, usamos historial completo ———
        if "Sin interacciones relevantes" in resumen_comercial:
            resumen_comercial = (
                "=== Historial completo de la conversación ===\n\n"
                + historial
            )

        # Enviar correo de digitalización con ambos resúmenes
        exito = enviar_correo_digitalizar(
            nombre, apellidos, negocio,
            provincia,
            email, telefono,
            resumen_comercial,
            texto_para_cliente
        )
        if not exito:
            return jsonify({'error': 'No se pudo enviar el correo'}), 500

        return jsonify({'message': 'Formulario digitalizar enviado correctamente'})
    except Exception as e:
        print("Error en enviar_formulario_digitalizar:", e)
        return jsonify({'error': 'Error procesando formulario digitalizar'}), 500

