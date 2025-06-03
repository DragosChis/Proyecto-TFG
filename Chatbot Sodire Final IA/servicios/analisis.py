import re
import json
import os
import google.generativeai as genai

# Configurar modelo Gemini (si lo necesitas más adelante)
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel('models/gemini-1.5-flash')


def extraer_parametros_del_historial(historial):
    sistema_op = None
    dispositivos_mesa = 0
    dispositivos_barra = 0
    dispositivos_barra_cantidad = 0
    total_dispositivos = 0
    total_impresoras = 0
    tipo_impresora = None
    impresoras_wifi = 0
    impresoras_cable = 0
    tiene_internet = None  # Este queda aunque ya no lo uses
    necesita_amplificador = False
    tipo_negocio = None
    router_especifico_contratado = False  # Nuevo parámetro

    print("🧠 HISTORIAL COMPLETO:\n", historial)

    pregunta_actual = ""
    respuestas = {}

    for linea in historial.splitlines():
        linea = linea.strip()
        if linea.lower().startswith("[pregunta]:"):
            pregunta_actual = linea.lower()
        elif linea.lower().startswith("[respuesta]:") and pregunta_actual:
            respuestas[pregunta_actual] = linea.lower()

    # Interpretar respuestas
    for pregunta, respuesta in respuestas.items():
        if "sistema operativo" in pregunta:
            if "android" in respuesta:
                sistema_op = "android"
            elif "ios" in respuesta:
                sistema_op = "ios"
            elif "windows" in respuesta:
                sistema_op = "windows"

        elif "comandas en mesa" in pregunta:
            try:
                dispositivos_mesa = int(re.search(r'\d+', respuesta).group())
            except:
                dispositivos_mesa = 0

        elif "cuántos dispositivos tiene" in pregunta:
            try:
                dispositivos_barra = int(re.search(r'\d+', respuesta).group())
            except:
                dispositivos_barra = 0

        elif "cuántos dispositivos va a necesitar" in pregunta:
            try:
                dispositivos_barra_cantidad = int(re.search(r'\d+', respuesta).group())
            except:
                dispositivos_barra_cantidad = 0

        elif "conexión de internet" in pregunta:
            if "si" in respuesta:
                tiene_internet = True
            elif "no" in respuesta:
                tiene_internet = False

        elif "tipo de impresora" in pregunta:
            if "wifi" in respuesta:
                tipo_impresora = "wifi"
            elif "cable" in respuesta:
                tipo_impresora = "cable"
            elif "ambas" in respuesta:
                tipo_impresora = "ambas"

        elif "cuántas impresoras necesita" in pregunta:
            try:
                total_impresoras = int(re.search(r'\d+', respuesta).group())
            except:
                total_impresoras = 0

        elif "cuantas impresoras necesita por wifi" in pregunta:
            try:
                impresoras_wifi = int(re.search(r'\d+', respuesta).group())
            except:
                impresoras_wifi = 0

        elif "tipo de negocio" in pregunta:
            if "restaurante" in respuesta:
                tipo_negocio = "Restaurante / Bar"
            elif "cafetería" in respuesta:
                tipo_negocio = "Cafetería"
            elif "heladería" in respuesta:
                tipo_negocio = "Heladería"
            elif "food truck" in respuesta:
                tipo_negocio = "Food truck"
            elif "comida para llevar" in respuesta or "delivery" in respuesta:
                tipo_negocio = "Solo para llevar / delivery"

        # ✅ Recomendación de amplificador
        elif "terraza" in pregunta and "si" in respuesta:
            terraza_confirmada = True
        elif "distancia" in pregunta and "+ de 20" in respuesta:
            distancia_larga = True

        # ✅ Nueva lógica para router específico
        elif "router específico" in pregunta:
            if "si" in respuesta:
                router_especifico_contratado = True
            elif "no" in respuesta:
                router_especifico_contratado = False

    # Calcular impresoras por tipo
    if tipo_impresora == "ambas":
        impresoras_cable = total_impresoras - impresoras_wifi
    elif tipo_impresora == "wifi":
        impresoras_wifi = total_impresoras
    elif tipo_impresora == "cable":
        impresoras_cable = total_impresoras

    # Calcular total dispositivos
    total_dispositivos = dispositivos_mesa + max(dispositivos_barra, dispositivos_barra_cantidad)

    # Activar recomendación si ambas condiciones se cumplieron
    necesita_amplificador = (
        any("terraza" in p and "si" in r for p, r in respuestas.items()) and
        any("distancia" in p and "+ de 20" in r for p, r in respuestas.items())
    )

    # Prints de depuración
    print("📱 Sistema operativo detectado:", sistema_op)
    print("📟 Dispositivos mesa:", dispositivos_mesa)
    print("🖥️ Dispositivos barra (tiene):", dispositivos_barra)
    print("🛒 Dispositivos barra (necesita):", dispositivos_barra_cantidad)
    print("🔢 Total dispositivos:", total_dispositivos)
    print("🖨️ Total impresoras:", total_impresoras)
    print("📶 Impresoras WiFi:", impresoras_wifi)
    print("🔌 Impresoras Cable:", impresoras_cable)
    print("🌐 ¿Tiene Internet?:", tiene_internet)
    print("📡 ¿Necesita amplificador?:", necesita_amplificador)
    print("📡 Router específico contratado:", router_especifico_contratado)

    return {
        "sistema_op": sistema_op,
        "dispositivos_mesa": dispositivos_mesa,
        "dispositivos_barra": dispositivos_barra,
        "dispositivos_barra_cantidad": dispositivos_barra_cantidad,
        "total_dispositivos": total_dispositivos,
        "tipo_impresora": tipo_impresora,
        "total_impresoras": total_impresoras,
        "impresoras_wifi": impresoras_wifi,
        "impresoras_cable": impresoras_cable,
        "tiene_internet": tiene_internet,
        "necesita_amplificador": necesita_amplificador,
        "tipo_negocio": tipo_negocio,
        "router_especifico_contratado": router_especifico_contratado
    }
