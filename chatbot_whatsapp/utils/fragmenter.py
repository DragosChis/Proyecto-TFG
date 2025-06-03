import json  # Para guardar los fragmentos en un archivo JSON
import os  # Para gestionar rutas y crear carpetas

# Función para fragmentar un texto por párrafos y, si son largos, dividirlos aún más
def fragmentar_por_parrafos(texto, max_longitud=500, solapamiento=50):
    parrafos = texto.split("\n\n")  # Divide el texto en párrafos, usando saltos de línea dobles
    fragmentos = []  # Lista para almacenar los fragmentos finales

    for parrafo in parrafos:
        parrafo = parrafo.strip()  # Elimina espacios innecesarios al principio y al final
        if not parrafo:
            continue  # Si el párrafo está vacío, lo salta

        # Si el párrafo es corto, se añade tal cual a la lista de fragmentos
        if len(parrafo) <= max_longitud:
            fragmentos.append(parrafo)
        else:
            # Si el párrafo es largo, se fragmenta en trozos más pequeños
            inicio = 0
            while inicio < len(parrafo):
                fin = min(inicio + max_longitud, len(parrafo))  # Define el final del fragmento
                sub_frag = parrafo[inicio:fin].strip()  # Extrae el sub-fragmento
                if sub_frag:
                    fragmentos.append(sub_frag)  # Lo añade a la lista
                inicio += max_longitud - solapamiento  # Avanza, dejando solapamiento entre fragmentos

    return fragmentos  # Devuelve la lista de fragmentos generados

# Procesa un diccionario de documentos y fragmenta cada uno
def procesar_documentos(diccionario_textos):
    fragmentos_totales = []  # Lista para todos los fragmentos

    # Recorre todos los documentos y sus textos
    for nombre_doc, contenido in diccionario_textos.items():
        fragmentos = fragmentar_por_parrafos(contenido)  # Fragmenta el contenido
        for i, frag in enumerate(fragmentos):
            # Guarda cada fragmento como un diccionario con identificador único
            fragmentos_totales.append({
                "documento": nombre_doc,
                "fragmento_id": f"{nombre_doc}_frag_{i}",  # ID único para cada fragmento
                "contenido": frag
            })

    return fragmentos_totales  # Devuelve la lista final de fragmentos

# Guarda la lista de fragmentos en un archivo JSON
def guardar_fragmentos(fragmentos, ruta_salida="./data/fragments.json"):
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)  # Crea la carpeta si no existe
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(fragmentos, f, ensure_ascii=False, indent=2)  # Guarda con formato legible

# Bloque de pruebas rápidas si este archivo se ejecuta como script
if __name__ == "__main__":
    from pdf_reader import extraer_texto_pdfs  # Importa la función para extraer texto de PDFs

    textos = extraer_texto_pdfs()  # Extrae los textos de los PDFs
    fragmentos = procesar_documentos(textos)  # Procesa y fragmenta los textos
    guardar_fragmentos(fragmentos)  # Guarda los fragmentos generados
    print(f"Fragmentos generados: {len(fragmentos)}")  # Muestra cuántos fragmentos se han generado
