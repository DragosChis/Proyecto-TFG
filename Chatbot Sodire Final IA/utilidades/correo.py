import os
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime  # ✅ añadido para formatear la fecha

def enviar_correos(nombre, apellidos, negocio, ciudad, provincia, cp, email, telefono, asunto, resumen, pdf_bytes):
    try:
        subject = "Departamento Ventas Sodire"

        # Generar nombre de archivo con nombre, apellidos y fecha
        fecha = datetime.now().strftime("%Y-%m-%d")
        nombre_archivo_txt = f"resumen_{nombre}_{apellidos}_{fecha}.txt".replace(" ", "_")
        nombre_archivo_pdf = f"presupuesto_{nombre}_{apellidos}_{fecha}.pdf".replace(" ", "_")  # ← NUEVO
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ========= CUERPO DEL MENSAJE PARA AGENTE COMERCIAL =========
        cuerpo = (
            "Se ha generado un nuevo presupuesto desde el asistente virtual. Aquí tienes los detalles del cliente:\n\n"
            f"Nombre y apellido cliente: {nombre} {apellidos}\n"
            f"Email: {email}\n"
            f"Teléfono: {telefono or 'No proporcionado'}\n"
            f"Nombre del local: {negocio}\n"
            f"Fecha y hora de la solicitud: {fecha_hora}\n\n"
            "Por favor, contactar lo más brevemente posible.\n"
            "Gracias."
        )

        # Crear correo para comercial
        msg = MIMEMultipart()
        msg['From'] = os.getenv('EMAIL_USER')
        msg['To'] = os.getenv('EMAIL_TO')
        msg['Subject'] = subject
        msg.attach(MIMEText(cuerpo, _subtype='plain', _charset='utf-8'))

        # Adjuntar resumen TXT
        adj_txt = MIMEApplication(resumen.encode('utf-8'), _subtype='plain')
        adj_txt.add_header('Content-Disposition', 'attachment', filename=nombre_archivo_txt)
        msg.attach(adj_txt)

        # Adjuntar PDF
        if pdf_bytes:
            adj_pdf = MIMEApplication(pdf_bytes, _subtype='pdf')
            adj_pdf.add_header('Content-Disposition', 'attachment', filename=nombre_archivo_pdf)
            msg.attach(adj_pdf)

        server = smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT')))
        server.starttls()
        server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
        server.send_message(msg)
        server.quit()

        # ========= MENSAJE DE COPIA AL CLIENTE =========
        if email and pdf_bytes:
            mensaje_cliente = (
                f"Hola {nombre},\n\n"
                "Gracias por ponerte en contacto con nosotros.\n"
                "Hemos recibido tu mensaje y uno de nuestros agentes comerciales se pondrá en contacto contigo\n"
                "lo antes posible.\n\n"
                "Si necesitas añadir algo más, puedes responder a este correo directamente.\n\n"
                "Nuestro horario de atención al cliente es el siguiente:\n"
                "Lunes a viernes de 10:00 a 14:00 y 15:00 a 18:00.\n"
                "Sábados de 11:00 a 14:00 y 15:00 a 17:00\n\n"
                "Gracias por tu confianza,\n"
                "El equipo de soporte de Sodire"
            )

            copy = MIMEMultipart()
            copy['From'] = os.getenv('EMAIL_USER')
            copy['To'] = email
            copy['Subject'] = 'Confirmación de tu solicitud - Sodire'
            copy.attach(MIMEText(mensaje_cliente, _subtype='plain', _charset='utf-8'))

            # Adjuntos
            adj_txt_cliente = MIMEApplication(resumen.encode('utf-8'), _subtype='plain')
            adj_txt_cliente.add_header('Content-Disposition', 'attachment', filename=nombre_archivo_txt)
            copy.attach(adj_txt_cliente)

            adj_pdf_cliente = MIMEApplication(pdf_bytes, _subtype='pdf')
            adj_pdf_cliente.add_header('Content-Disposition', 'attachment', filename=nombre_archivo_pdf)
            copy.attach(adj_pdf_cliente)

            server = smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT')))
            server.starttls()
            server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
            server.send_message(copy)
            server.quit()

        return True

    except Exception as e:
        print("Error al enviar correos:", e)
        traceback.print_exc()
        return False


def enviar_correo_soporte(nombre, apellidos, email, telefono, local, mensaje, resumen, tipo_consulta=""):
    try:
        subject = "Solicitud de Soporte Técnico"
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha = datetime.now().strftime("%Y-%m-%d")
        nombre_archivo_txt = f"resumen_{nombre}_{apellidos}_{fecha}.txt".replace(" ", "_")

        # ========= CUERPO DEL MENSAJE PARA AGENTE COMERCIAL =========
        cuerpo = (
            f"Hola equipo,\n"
            f"Se ha generado un nuevo ticket de soporte desde el chatbot. Aquí tienes los detalles:\n\n"
            f"Cliente: {nombre} {apellidos}\n"
            f"Email: {email}\n"
            f"Teléfono: {telefono or 'No proporcionado'}\n"
            f"Nombre del local: {local}\n"
            f"Fecha y hora de la solicitud: {fecha_hora}\n"
            f"Tipo de consulta: {tipo_consulta.strip() if tipo_consulta.strip() else 'No especificado'}\n"
            f"Resumen de la incidencia: {mensaje}\n\n"
            f"Por favor, asignadlo y responded según prioridad.\n"
            f"Gracias."
        )
        cuerpo += "\nConsulte el archivo adjunto para ver el historial detallado."

        msg = MIMEMultipart()
        msg['From'] = os.getenv('EMAIL_USER')
        msg['To'] = os.getenv('EMAIL_TO')
        msg['Subject'] = subject
        msg.attach(MIMEText(cuerpo, _subtype='plain', _charset='utf-8'))

        adj_txt = MIMEApplication(resumen.encode('utf-8'), _subtype='plain')
        adj_txt.add_header('Content-Disposition', 'attachment', filename=nombre_archivo_txt)
        msg.attach(adj_txt)

        server = smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT')))
        server.starttls()
        server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
        server.send_message(msg)
        server.quit()

        if email:
            mensaje_cliente = (
                f"Hola {nombre},\n\n"
                "Gracias por ponerte en contacto con nosotros.\n"
                "Hemos recibido tu mensaje y uno de nuestros técnicos se pondrá en contacto contigo lo antes posible.\n\n"
                "Resumen de la incidencia:\n"
                f"{mensaje}\n\n"
                "Si necesitas añadir algo más o actualizar tu caso, puedes responder a este correo directamente.\n\n"
                "Nuestro horario de soporte es:\n"
                "Lunes a viernes de 10:00 a 14:00 y 15:00 a 18:00.\n"
                "Sábados de 11:00 a 14:00 y 15:00 a 17:00.\n\n"
                "Gracias por tu confianza,\n"
                "El equipo de soporte de Sodire"
            )
            mensaje_cliente += "\nAdjuntamos también un resumen de la conversación."

            copy = MIMEMultipart()
            copy['From'] = os.getenv('EMAIL_USER')
            copy['To'] = email
            copy['Subject'] = 'Copia de tu solicitud de soporte'
            copy.attach(MIMEText(mensaje_cliente, _subtype='plain', _charset='utf-8'))

            adj_txt_cliente = MIMEApplication(resumen.encode('utf-8'), _subtype='plain')
            adj_txt_cliente.add_header('Content-Disposition', 'attachment', filename=nombre_archivo_txt)
            copy.attach(adj_txt_cliente)

            server = smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT')))
            server.starttls()
            server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
            server.send_message(copy)
            server.quit()

        return True

    except Exception as e:
        print("Error al enviar correo de soporte:", e)
        traceback.print_exc()
        return False


def enviar_correo_digitalizar(
    nombre, apellidos, negocio,
    provincia,
    email, telefono,
    resumen_comercial,  # resumen para el comercial
    resumen_cliente    # resumen en prosa que recibe el cliente
):
    try:
        subject = "Departamento Ventas Sodire"

        # Fecha y nombres de archivo
        fecha = datetime.now().strftime("%Y-%m-%d")
        nombre_archivo_txt_comercial = f"resumen_{nombre}_{apellidos}_{fecha}.txt".replace(" ", "_")
        nombre_archivo_txt_cliente   = f"resumen_cliente_{nombre}_{apellidos}_{fecha}.txt".replace(" ", "_")
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ==== Correo al comercial ====
        cuerpo = (
            "Se ha generado una nueva solicitud de digitalización desde el asistente virtual. Aquí tienes los detalles del cliente:\n\n"
            f"Nombre y apellido cliente: {nombre} {apellidos}\n"
            f"Email: {email}\n"
            f"Teléfono: {telefono or 'No proporcionado'}\n"
            f"Nombre del negocio: {negocio}\n"
            f"Provincia: {provincia}\n"
            f"Fecha y hora de la solicitud: {fecha_hora}\n\n"
            "Por favor, contactar lo más brevemente posible.\n"
            "Gracias."
        )

        msg = MIMEMultipart()
        msg['From']    = os.getenv('EMAIL_USER')
        msg['To']      = os.getenv('EMAIL_TO')
        msg['Subject'] = subject
        msg.attach(MIMEText(cuerpo, _subtype='plain', _charset='utf-8'))

        # 1) Adjuntar el resumen detallado (literal) para el comercial
        adj_txt_comercial = MIMEApplication(resumen_comercial.encode('utf-8'), _subtype='plain')
        adj_txt_comercial.add_header('Content-Disposition',
                                     'attachment',
                                     filename=nombre_archivo_txt_comercial)
        msg.attach(adj_txt_comercial)

        # 2) Adjuntar también el resumen en prosa (el que recibió el cliente),
        #    para que el comercial tenga una copia exacta de lo que vio el cliente.
        adj_txt_cliente = MIMEApplication(resumen_cliente.encode('utf-8'), _subtype='plain')
        adj_txt_cliente.add_header('Content-Disposition',
                                   'attachment',
                                   filename=nombre_archivo_txt_cliente)
        msg.attach(adj_txt_cliente)

        # Enviar al comercial
        server = smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT')))
        server.starttls()
        server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
        server.send_message(msg)
        server.quit()

        # ==== Copia al cliente ====
        if email:
            mensaje_cliente = (
                f"Hola {nombre},\n\n"
                "Gracias por tu interés en nuestro servicio de digitalización.\n"
                "Adjunto encontrarás un resumen personalizado de lo hablado.\n\n"
                "Si necesitas más información, no dudes en responder a este correo.\n\n"
                "Saludos cordiales,\n"
                "El equipo de Sodire"
            )

            copy = MIMEMultipart()
            copy['From']    = os.getenv('EMAIL_USER')
            copy['To']      = email
            copy['Subject'] = 'Confirmación de tu solicitud - Sodire'
            copy.attach(MIMEText(mensaje_cliente, _subtype='plain', _charset='utf-8'))

            # Adjuntar el resumen en prosa para el cliente
            adj_cliente_para_cliente = MIMEApplication(resumen_cliente.encode('utf-8'), _subtype='plain')
            adj_cliente_para_cliente.add_header('Content-Disposition',
                                                'attachment',
                                                filename=nombre_archivo_txt_cliente)
            copy.attach(adj_cliente_para_cliente)

            server = smtplib.SMTP(os.getenv('EMAIL_HOST'), int(os.getenv('EMAIL_PORT')))
            server.starttls()
            server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
            server.send_message(copy)
            server.quit()

        return True

    except Exception as e:
        print("Error en enviar_correo_digitalizar:", e)
        traceback.print_exc()
        return False
