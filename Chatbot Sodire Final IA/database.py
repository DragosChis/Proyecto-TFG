import mysql.connector
import os
from dotenv import load_dotenv
from configuracion.config import db_config, api_key, email_config

load_dotenv()

db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}


def search_database(query):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT p.id, p.nombre, p.descripcion
            FROM productos p
            JOIN palabras_clave_productos pkp ON p.id = pkp.producto_id
            JOIN palabras_clave pk ON pk.id = pkp.palabra_clave_id
            WHERE LOWER(%s) LIKE CONCAT('%%', LOWER(pk.palabra), '%%')
        """
        cursor.execute(sql, (query.lower(),))
        results = cursor.fetchall()
        conn.close()
        return results
    except mysql.connector.Error as e:
        print(f"Error de MySQL: {e}")
        return []
    except Exception as e:
        print(f"Error inesperado: {e}")
        return []


def get_keywords():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT palabra FROM palabras_clave"
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()
        return [row['palabra'] for row in results]
    except mysql.connector.Error as e:
        print(f"Error de MySQL: {e}")
        return []
    except Exception as e:
        print(f"Error inesperado: {e}")
        return []

def get_keywords_full():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, palabra FROM palabras_clave")
        resultados = cursor.fetchall()
        conn.close()
        return resultados  # ← devuelve [{'id': 2, 'palabra': 'tpv'}, ...]
    except:
        return []

def detectar_palabras_en_historial(historial, palabras_clave):
    """
    Detecta qué palabras clave están presentes en el historial de conversación.

    historial: lista de strings (mensajes del cliente)
    palabras_clave: lista de dicts con 'id' y 'palabra'

    Devuelve: lista de dicts con las palabras clave encontradas
    """
    texto = ' '.join(historial).lower()
    coincidencias = []

    for palabra in palabras_clave:
        palabra_texto = palabra['palabra'].lower()
        if palabra_texto in texto:
            coincidencias.append(palabra)

    return coincidencias



def get_budget_info_optimizado(productos_ids, num_dispositivos):
    """
    Devuelve solo el plan que coincide con el número de dispositivos indicado.
    """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        budget_info = ""

        for prod_id in productos_ids:
            cursor.execute("SELECT nombre, descripcion FROM productos WHERE id = %s", (prod_id,))
            producto = cursor.fetchone()
            if producto:
                budget_info += f"Producto: {producto['nombre']}\n"
                budget_info += f"Descripción: {producto['descripcion']}\n"

                cursor.execute(
                    "SELECT precio, dispositivos FROM planes_producto WHERE producto_id = %s AND dispositivos = %s",
                    (prod_id, num_dispositivos)
                )
                plan = cursor.fetchone()
                if plan:
                    budget_info += f"Plan seleccionado:\n  - {plan['dispositivos']} dispositivos: {plan['precio']} €\n"

                # Añadimos hardware compatible como referencia
                cursor.execute("""
                    SELECT h.nombre, h.descripcion
                    FROM hardware h
                    JOIN hardware_productos hp ON h.id = hp.hardware_id
                    WHERE hp.producto_id = %s
                """, (prod_id,))
                hardware_items = cursor.fetchall()
                if hardware_items:
                    budget_info += "Hardware compatible:\n"
                    for hw in hardware_items:
                        budget_info += f"  - {hw['nombre']}: {hw['descripcion']}\n"

                budget_info += "\n"

        conn.close()
        return budget_info.strip()
    except Exception as e:
        print("Error en get_budget_info_optimizado:", e)
        return ""


def get_hardware_info_filtrado(ids, sistema_op, num_dispositivos):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        hardware_info = []

        for hw_id in ids:
            cursor.execute("SELECT nombre, descripcion, precio FROM hardware WHERE id = %s", (hw_id,))
            hw = cursor.fetchone()
            if not hw:
                continue

            nombre_hw = hw['nombre'].lower()
            incluir = False

            if sistema_op == 'ios' and 'epson' in nombre_hw:
                incluir = True
            elif sistema_op in ['android', 'windows'] and 'iggual' in nombre_hw:
                incluir = True
            elif 'servidor' in nombre_hw and num_dispositivos and num_dispositivos > 1:
                incluir = True
            elif 'switch' in nombre_hw and num_dispositivos and num_dispositivos > 3:
                incluir = True
            elif 'router' in nombre_hw:
                incluir = True
            elif 'cajón' in nombre_hw:
                incluir = True

            if incluir:
                hardware_info.append(hw)

        conn.close()
        return hardware_info
    except Exception as e:
        print("Error en get_hardware_info_filtrado:", e)
        return []

def get_productos_compatibles(productos_ids, sistema_op):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="chatbot_prueba_enriquecida"
        )
        cursor = conn.cursor(dictionary=True)

        if not productos_ids:
            return []

        formato_ids = ','.join(['%s'] * len(productos_ids))

        query = f"""
            SELECT p.*, GROUP_CONCAT(DISTINCT pp.id ORDER BY pp.dispositivos ASC) AS planes_ids
            FROM productos p
            JOIN producto_sistema_op ps ON p.id = ps.producto_id
            JOIN sistema_op s ON ps.sistema_id = s.id
            LEFT JOIN planes_producto pp ON pp.producto_id = p.id
            WHERE p.id IN ({formato_ids}) AND s.nombre = %s
            GROUP BY p.id
        """

        cursor.execute(query, productos_ids + [sistema_op])
        productos = cursor.fetchall()

        # Obtener planes de cada producto por separado
        for producto in productos:
            cursor.execute(
                "SELECT * FROM planes_producto WHERE producto_id = %s ORDER BY dispositivos ASC",
                (producto['id'],)
            )
            producto['planes'] = cursor.fetchall()

        return productos

    except Exception as e:
        print("Error en get_productos_compatibles:", e)
        return []

def get_servicios_digitales_info(ids):

    if not ids:
        return "", ""

    try:
        conn   = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        ph  = ",".join(["%s"] * len(ids))
        sql = (
            f"SELECT id,nombre,precio_minimo_mensual,precio_desde_texto,"
            f"herramientas FROM servicios_digitales "
            f"WHERE id IN ({ph}) ORDER BY FIELD(id,{ph})"
        )
        cursor.execute(sql, ids + ids)
        rows = cursor.fetchall()
        conn.close()

        precios_lines, herr_lines = [], []

        for r in rows:
            # ---------- BLOQUE PRECIOS ----------
            if r["id"] == 5:                      # ← excepción para RRSS/web
                
                linea_precio = (
                    f"• {r['nombre']}: {r['precio_desde_texto']}."
                    if r["precio_desde_texto"]
                    else f"• {r['nombre']}"
                )
            else:
                precio_num   = int(r["precio_minimo_mensual"])
                precio_label = f"{precio_num}€"

                if r["precio_desde_texto"]:
                    linea_precio = (
                        f"• {r['nombre']}: Este servicio tiene un precio "
                        f"desde {precio_label} + {r['precio_desde_texto']}."
                    )
                else:
                    linea_precio = (
                        f"• {r['nombre']}: Este servicio tiene un precio "
                        f"de {precio_label}."
                    )

            precios_lines.append(linea_precio)

            # ---------- BLOQUE HERRAMIENTAS ----------
            
            if r["herramientas"]:
                herr_lines.append(
                    f"en {r['nombre']} trabajamos con {r['herramientas']}."
                )

        bloque_precios      = "\n".join(precios_lines)
        bloque_herramientas = " ".join(herr_lines)

        return bloque_precios, bloque_herramientas

    except Exception as e:
        print("Error al obtener servicios digitales:", e)
        return "", ""




    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
