# Importamos la librería PyMuPDF (fitz) para leer PDFs
import fitz  # PyMuPDF para trabajar con documentos PDF
import os  # Para interactuar con el sistema de archivos (listar archivos, rutas, etc.)

# Función para extraer el texto de todos los archivos PDF en un directorio
def extraer_texto_pdfs(directorio_docs="./docs"):
    textos = {}  # Diccionario donde se almacenarán los textos extraídos: {nombre_archivo: texto}

    # Recorre todos los archivos del directorio especificado
    for archivo in os.listdir(directorio_docs):
        # Filtra solo los archivos con extensión .pdf
        if archivo.endswith(".pdf"):
            ruta = os.path.join(directorio_docs, archivo)  # Ruta completa del archivo
            print(f"Procesando: {archivo}")
            texto = ""  # Variable para almacenar el texto completo de este PDF

            # Abre el PDF con fitz (PyMuPDF)
            with fitz.open(ruta) as doc:
                # Recorre todas las páginas del PDF
                for pagina in doc:
                    texto += pagina.get_text()  # Extrae el texto de la página y lo añade al acumulador

            # Guarda el texto extraído en el diccionario con el nombre del archivo como clave
            textos[archivo] = texto.strip()  # strip() elimina espacios iniciales/finales

    return textos  # Devuelve el diccionario con los textos de los PDFs

# Bloque para probar la función directamente si este archivo se ejecuta como script
if __name__ == "__main__":
    resultados = extraer_texto_pdfs()  # Llama a la función para procesar PDFs
    for nombre, contenido in resultados.items():
        print(f"\n--- {nombre} ---")  # Imprime el nombre del archivo
        print(contenido[:500], "...")  # Muestra los primeros 500 caracteres del texto extraído
