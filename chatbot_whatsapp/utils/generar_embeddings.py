import json  # Para trabajar con archivos JSON (lectura y escritura)
import os  # Para interactuar con el sistema de archivos
import pickle  # Para guardar datos serializados (en binario)
import sys  # Para manipular la ruta de búsqueda de módulos
from tqdm import tqdm  # Para mostrar una barra de progreso en la consola

# AÑADIDO: permite importar módulos desde la raíz del proyecto
# Esto añade el directorio raíz del proyecto a sys.path, facilitando las importaciones
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa la función que genera el embedding de un texto usando OpenAI
from utils.embedding_openai import obtener_embedding

# Función para cargar los fragmentos de texto desde un archivo JSON
def cargar_fragmentos(ruta="data/fragments.json"):
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)  # Devuelve una lista de fragmentos

# Función para guardar los embeddings generados en un archivo binario (.pkl)
def guardar_embeddings(datos, ruta="data/index_openai.pkl"):
    with open(ruta, "wb") as f:
        pickle.dump(datos, f)  # Serializa la lista y la guarda en el archivo

# Función principal para generar el índice de embeddings
def generar_index():
    fragmentos = cargar_fragmentos()  # Carga los fragmentos desde el JSON
    index = []  # Lista para almacenar los fragmentos con sus embeddings

    print("Generando embeddings de los fragmentos...")
    # tqdm: muestra una barra de progreso en la consola
    for item in tqdm(fragmentos):
        texto = item["contenido"]  # Contenido del fragmento
        embedding = obtener_embedding(texto)  # Genera el embedding con OpenAI
        if embedding:
            item["embedding"] = embedding  # Añade el embedding al fragmento
            index.append(item)  # Añade el fragmento con embedding a la lista final

    # Guarda todos los fragmentos con embeddings en un archivo .pkl
    guardar_embeddings(index)
    print(f"Embeddings generados: {len(index)}")  # Muestra el número total de embeddings generados

# Bloque para ejecutar el script directamente
if __name__ == "__main__":
    generar_index()
