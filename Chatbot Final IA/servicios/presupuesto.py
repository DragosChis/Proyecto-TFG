import os
import traceback
from datetime import datetime
from fpdf import FPDF
from database import get_productos_compatibles, get_hardware_info_filtrado
from servicios.analisis import extraer_parametros_del_historial

# IDs de productos
ID_ADDITION = 1
ID_LASTAPP = 2

# IDs de hardware por producto
HARDWARE_IDS = {
    "addition": {
        "epsoncable": 1,
        "epsonwifi": 2,
        "router": 5,
        "server": 6,
        "switch": 7
    },
    "lastapp": {
        "iggual": 3,
        "epsonwifi": 2,
        "router": 5
    }
}

class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Inter', '', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, f'Páginas: {self.page_no()}/{{nb}}', 0, 0, 'C')

def generar_presupuesto_pdf(info_texto,
                            items,
                            tipo_negocio=None,
                            fecha=None,
                            cliente_nombre="",
                            cliente_negocio="",
                            cliente_telefono="",
                            cliente_ciudad="",
                            cliente_provincia="",
                            cliente_cp="",
                            recomendacion_extra=""):

    if fecha is None:
        fecha = datetime.now().strftime("%d/%m/%Y")

    try:
        font_path = os.path.join("fonts", "inter.ttf")
        bold_path = os.path.join("fonts", "inter-Bold.ttf")
        logo_path = os.path.join("img", "logopdf.png")

        for p in (font_path, bold_path, logo_path):
            if not os.path.exists(p):
                print("Archivo no encontrado:", p)
                return None

        pdf = PDF('P', 'mm', 'A4')
        pdf.alias_nb_pages()
        pdf.set_auto_page_break(auto=False)
        pdf.add_page()
        pdf.set_top_margin(20)
        pdf.add_font('Inter', '', font_path, uni=True)
        pdf.add_font('Inter', 'B', bold_path, uni=True)

        # Datos empresa
        pdf.image(logo_path, x=9, y=15, w=72)
        start_x = 9
        start_y = 43
        pdf.set_font('Inter', 'B', 9)
        pdf.set_text_color(54, 87, 98)
        pdf.set_xy(start_x, start_y)
        pdf.cell(70, 5, "SOLUCIONES DIGITALES", ln=1)
        pdf.set_x(start_x)
        pdf.cell(70, 5, "RESTAURACIÓN S.L.", ln=1)

        pdf.set_font('Inter', '', 9)
        pdf.set_text_color(54, 87, 98)
        for line in [
            "CALLE DOCTOR SUMSI 44 4",
            "46005 VALENCIA, VALENCIA",
            "NIF (CIF): ESB06774228",
            "www.sodire.es"
        ]:
            pdf.set_x(start_x)
            pdf.cell(70, 5, line, ln=1)

        # Datos cliente
        pdf.ln(8)
        pdf.set_font('Inter', 'B', 10)
        pdf.set_text_color(54, 87, 98)
        pdf.set_x(start_x)
        pdf.cell(70, 6, cliente_nombre, ln=1)
        pdf.set_font('Inter', 'B', 9)
        pdf.set_x(start_x)
        pdf.cell(70, 5, cliente_negocio, ln=1)
        if cliente_telefono:
            pdf.set_font('Inter', '', 9)
            pdf.set_text_color(54, 87, 98)
            pdf.set_x(start_x)
            pdf.cell(70, 5, f"{cliente_telefono}", ln=1)
        pdf.set_font('Inter', '', 9)
        pdf.set_text_color(54, 87, 98)
        pdf.set_x(start_x)
        ciudad_line = f"{cliente_cp} {cliente_ciudad}, {cliente_provincia}"
        pdf.cell(70, 5, ciudad_line, ln=1)

        # Cabecera presupuesto
        extra_margin = 5
        pdf.set_text_color(5, 33, 45)
        pdf.set_font('Inter', 'B', 22)
        title = 'Presupuesto Provisional'
        x_title = pdf.w - pdf.r_margin - pdf.get_string_width(title) - extra_margin + 5
        pdf.set_xy(x_title, 22)
        pdf.cell(0, 10, title, ln=1)

        # Recuadro metadatos
        meta_w, meta_h = 60, 20
        meta_x = pdf.w - pdf.r_margin - extra_margin - meta_w + 5
        meta_y = 43
        pdf.set_fill_color(245, 247, 255)
        pdf.set_draw_color(200, 200, 200)
        pdf.rect(meta_x, meta_y, meta_w, meta_h, style='F')

        pdf.set_font('Inter', 'B', 9)
        line_h = 6
        pdf.set_xy(meta_x + 4, meta_y + 4)
        pdf.cell(25, line_h, 'Tipo negocio:')
        pdf.set_font('Inter', '', 9)
        pdf.cell(0, line_h, tipo_negocio or "No especificado", ln=1)
        pdf.set_font('Inter', 'B', 9)
        pdf.set_x(meta_x + 4)
        pdf.cell(25, line_h, 'Fecha:')
        pdf.set_font('Inter', '', 9)
        pdf.cell(0, line_h, fecha, ln=1)

        pdf.ln(55)
        agregar_tabla_con_totales(pdf, items)
        pdf.ln(10)

        pdf.set_font("Inter", '', 12)
        for linea in info_texto.replace('\r\n', '\n').split('\n'):
            if not linea.strip():
                pdf.ln(5)
            else:
                pdf.multi_cell(0, 8, linea.encode('latin-1', 'replace').decode('latin-1'))

        # Segunda página con notas
        # Segunda página con notas
        pdf.add_page()
        pdf.set_top_margin(20)
        pdf.set_font('Inter', 'B', 9)
        pdf.set_text_color(5, 33, 45)
        pdf.cell(0, 10, 'Notas', ln=1)

        # Mostrar recomendación como primera nota
        if recomendacion_extra:
            pdf.set_font("Inter", '', 9)
            pdf.set_text_color(5, 33, 45)
            pdf.multi_cell(0, 8, recomendacion_extra.encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(5)

        # Resto de notas
        pdf.set_text_color(5, 33, 45)
        pdf.set_font('Inter', '', 9)
        notas = [
            'El tiempo incluido en el presupuesto para la puesta en marcha será de 2h. En caso de que por motivos ajenos a SODIRE se exceda ese tiempo, se facturará por franjas de 1h a 40€/h.',
            'CONDICIONES DE LA INSTALACIÓN:',
            '- Se requiere disponer de cableado de ethernet (RJ45) que vaya desde el router hasta la ubicación de cada impresora. Cada extremo del cable debe de estar correctamente crimpado a una clavija macho. - Se requiere conexión eléctrica en la ubicación de las impresoras.',
            'CONDICIONES GENERALES:',
            '- SODIRE no puede garantizar el correcto funcionamiento de la red al utilizarse un dispositivo no probado anteriormente, por lo que el cliente asume que pueda haber algún problema en la conexión de los dispositivos por este hecho. - No se realiza ningún tipo de instalación eléctrica, de cableado o de fijación de los dispositivos.',
            'CONDICIONES DE USO:',
            '(La firma del presente presupuesto implica la aceptación de las políticas de uso del fabricante del software)',
            'NOMBRE: ',
            'FECHA: ',
            'FIRMA: .'
        ]
        for linea in notas:
            pdf.multi_cell(0, 8, linea.encode('latin-1', 'replace').decode('latin-1'))

        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        with open("presupuesto_estilizado.pdf", "wb") as f:
            f.write(pdf_bytes)
        return pdf_bytes

    except Exception:
        traceback.print_exc()
        return None

def calcular_costes_adicionales(n_dispositivos):
    costes = []

    if n_dispositivos == 1:
        costes.append({"nombre": "Preconfiguración", "cantidad": 1, "importe": 89.0})
    elif n_dispositivos == 2:
        costes.append({"nombre": "Preconfiguración", "cantidad": 1, "importe": 119.0})
    elif n_dispositivos == 3:
        costes.append({"nombre": "Preconfiguración", "cantidad": 1, "importe": 149.0})
    elif n_dispositivos > 3:
        costes.append({"nombre": "Preconfiguración", "cantidad": 1, "importe": 149.0 + (n_dispositivos - 3) * 30})

    if n_dispositivos == 1:
        costes.append({"nombre": "Gastos de envío", "cantidad": 1, "importe": 39.0})
    elif 2 <= n_dispositivos <= 3:
        costes.append({"nombre": "Gastos de envío", "cantidad": 1, "importe": 59.0})
    elif 4 <= n_dispositivos <= 5:
        costes.append({"nombre": "Gastos de envío", "cantidad": 1, "importe": 69.0})
    elif n_dispositivos >= 6:
        costes.append({"nombre": "Gastos de envío", "cantidad": 1, "importe": 79.0})

    if n_dispositivos == 1:
        costes.append({"nombre": "Puesta en marcha y formación", "cantidad": 1, "importe": 149.0})
    elif 2 <= n_dispositivos <= 3:
        costes.append({"nombre": "Puesta en marcha y formación", "cantidad": 1, "importe": 189.0})
    elif 4 <= n_dispositivos <= 5:
        costes.append({"nombre": "Puesta en marcha y formación", "cantidad": 1, "importe": 239.0})
    elif n_dispositivos >= 6:
        costes.append({"nombre": "Puesta en marcha y formación", "cantidad": 1, "importe": 309.0})

    return costes

def agregar_tabla_con_totales(pdf, items):
    start_x = 9
    col_widths = [121, 34, 36]
    row_height = 8

    # Encabezados de la tabla
    pdf.set_font("Inter", "B", 10)
    pdf.set_draw_color(193, 205, 231)
    pdf.set_text_color(5, 33, 45)
    headers = ["Producto o servicio", "Cantidad", "Importe"]
    for i, header in enumerate(headers):
        pdf.set_x(start_x + sum(col_widths[:i]))
        align = 'R' if i in [1, 2] else 'L'
        pdf.cell(col_widths[i], row_height, header, border='B', align=align, fill=False)
    pdf.ln(row_height)

    # Contenido de la tabla
    pdf.set_font("Inter", '', 9)
    subtotal = 0

    for idx, item in enumerate(items):
        nombre = item.get("nombre", "")
        cantidad = item.get("cantidad", 1)
        importe = item.get("importe", 0.00)
        tipo = item.get("tipo", "unitario")

        total = importe if tipo == "fijo" else cantidad * importe
        subtotal += total

        pdf.set_x(start_x)
        pdf.set_text_color(54, 87, 98)
        pdf.set_draw_color(228, 236, 250)
        border_style = 'B' if idx < len(items) - 1 else 0

        pdf.cell(col_widths[0], row_height, nombre, border=border_style)

        es_producto_principal = nombre.lower() in ["l'addition", "lastapp"]
        sufijo = ("dispositivo" if cantidad == 1 and es_producto_principal else
                  "dispositivos" if es_producto_principal else
                  "unidad" if cantidad == 1 else "unidades")
        pdf.cell(col_widths[1], row_height,
                 f"{cantidad} {sufijo}", border=border_style, align='R')
        pdf.cell(col_widths[2], row_height,
                 f"{total:.2f} EUR", border=border_style, align='R')
        pdf.ln(row_height)

    # Totales con estilo
    iva = subtotal * 0.21
    total_final = subtotal + iva
    pdf.ln(4)

    def draw_total_row(label, value, fill=False, bold=False):
        total_width = sum(col_widths)
        row_padding = 6
        pdf.set_x(start_x)
        pdf.set_fill_color(245, 247, 255) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(255, 255, 255)
        pdf.set_font("Inter", 'B' if bold else '', 10)
        pdf.set_text_color(5, 33, 45)
        pdf.cell(total_width, row_height,
                 f"{label}{' ' * row_padding}{value:.2f} EUR",
                 border=0, align='R', fill=True)
        pdf.ln(row_height)

    draw_total_row("Subtotal", subtotal, fill=False, bold=True)
    draw_total_row("IVA 21%", iva, fill=True, bold=False)
    draw_total_row("Importe total", total_final, fill=False, bold=True)


def generar_presupuesto_final(historial, nombre, negocio):
    params = extraer_parametros_del_historial(historial)

    sistema_op          = params['sistema_op']
    total_dispositivos  = params['total_dispositivos']
    total_impresoras    = params['total_impresoras']
    impresoras_wifi     = params['impresoras_wifi']
    impresoras_cable    = params['impresoras_cable']
    tiene_internet      = params['tiene_internet']
    necesita_amplificador = params.get("necesita_amplificador", False)
    router_especifico_contratado = params.get('router_especifico_contratado', False)

    producto_id  = ID_ADDITION if sistema_op == 'ios' else ID_LASTAPP
    producto_key = 'addition' if producto_id == ID_ADDITION else 'lastapp'

    productos_filtrados = get_productos_compatibles([producto_id], sistema_op)
    if not productos_filtrados:
        return "No se encontraron productos compatibles con tu sistema operativo.", []

    items = []
    for p in productos_filtrados:
        if producto_key == 'lastapp' and total_dispositivos > 4:
            importe = 175.0
        else:
            importe = 0.0
            if p.get('planes'):
                plan = next((pl for pl in p['planes']
                             if pl.get('dispositivos') == total_dispositivos), None)
                if plan is None:
                    candidatos = [pl for pl in p['planes']
                                  if pl.get('dispositivos') is not None
                                     and pl['dispositivos'] <= total_dispositivos]
                    if candidatos:
                        plan = max(candidatos, key=lambda pl: pl['dispositivos'])
                if plan:
                    importe = float(plan['precio'])
        items.append({
            "nombre": p['nombre'],
            "cantidad": total_dispositivos,
            "importe": importe,
            "tipo": "fijo"
        })

    hardware_ids = []
    if impresoras_wifi > 0:
        hardware_ids.append(HARDWARE_IDS[producto_key]['epsonwifi'])
    if impresoras_cable > 0:
        if producto_key == 'addition':
            hardware_ids.append(HARDWARE_IDS['addition']['epsoncable'])
        else:
            hardware_ids.append(HARDWARE_IDS['lastapp']['iggual'])
    if router_especifico_contratado:
        hardware_ids.append(HARDWARE_IDS[producto_key]['router'])
    if producto_key == 'addition' and total_dispositivos > 1:
        hardware_ids.append(HARDWARE_IDS['addition']['server'])
    if total_impresoras > 3:
        hardware_ids.append(HARDWARE_IDS['addition']['switch'])

    hardware_recomendado = get_hardware_info_filtrado(
        hardware_ids, sistema_op, total_dispositivos
    )
    for hw in hardware_recomendado:
        precio_h = float(hw.get('precio', 0.0))
        if 'wifi' in hw['nombre'].lower():
            qty = impresoras_wifi
        elif 'ethernet' in hw['nombre'].lower():
            qty = impresoras_cable
        else:
            qty = 1
        items.append({
            "nombre": hw['nombre'],
            "cantidad": qty,
            "importe": precio_h
        })

    if impresoras_wifi > 0 and not any('wifi' in hw['nombre'].lower() for hw in hardware_recomendado):
        wifi_info = get_hardware_info_filtrado(
            [HARDWARE_IDS['addition']['epsonwifi']], 'ios', total_dispositivos
        )
        if wifi_info:
            hw = wifi_info[0]
            precio_h = float(hw.get('precio', 0.0))
            items.append({
                "nombre": hw['nombre'],
                "cantidad": impresoras_wifi,
                "importe": precio_h
            })

    # ✅ NUEVO BLOQUE: contar dispositivos físicos para calcular costes adicionales
    dispositivos_fisicos = 0
    dispositivos_fisicos += impresoras_wifi + impresoras_cable
    if HARDWARE_IDS[producto_key]["router"] in hardware_ids:
        dispositivos_fisicos += 1
    if producto_key == "addition" and HARDWARE_IDS["addition"]["server"] in hardware_ids:
        dispositivos_fisicos += 1
    if HARDWARE_IDS["addition"]["switch"] in hardware_ids:
        dispositivos_fisicos += 1

    # ➕ Añadir costes adicionales
    costes_adicionales = calcular_costes_adicionales(dispositivos_fisicos)
    items.extend(costes_adicionales)

    return "", items

