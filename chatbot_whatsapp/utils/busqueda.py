import os  # Para manejar rutas y archivos
import sys  # Para modificar rutas de búsqueda de módulos
import pickle  # Para cargar el índice de embeddings (archivos binarios)
import numpy as np  # Para cálculos matemáticos (coseno, norma, etc.)

# AÑADIDO: permite importar módulos desde la raíz del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importamos la función que genera el embedding de una pregunta usando OpenAI
from utils.embedding_openai import obtener_embedding

# Función para cargar el índice de embeddings guardado en un archivo .pkl
def cargar_index(ruta="data/index_openai.pkl"):
    with open(ruta, "rb") as f:
        return pickle.load(f)  # Devuelve la lista de fragmentos con sus embeddings

# Función para calcular la similaridad coseno entre dos vectores (entre -1 y 1)
def similaridad_coseno(v1, v2):
    v1, v2 = np.array(v1), np.array(v2)  # Convierte las listas a arrays de NumPy
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))  # Fórmula del coseno

# Función principal para buscar los fragmentos más parecidos a la pregunta
def buscar_fragmentos_parecidos(pregunta, top_k=3):
    index = cargar_index()  # Carga el índice de embeddings
    embedding_pregunta = obtener_embedding(pregunta)  # Genera el embedding de la pregunta

    resultados = []  # Lista para almacenar los fragmentos con su similaridad

    # Recorre todos los fragmentos indexados
    for item in index:
        sim = similaridad_coseno(embedding_pregunta, item["embedding"])  # Calcula la similaridad
        resultados.append({
            "documento": item["documento"],
            "fragmento_id": item["fragmento_id"],
            "contenido": item["contenido"],
            "similaridad": sim
        })

    # Ordena los resultados de mayor a menor similaridad
    resultados.sort(key=lambda x: x["similaridad"], reverse=True)

    return resultados[:top_k]  # Devuelve los top_k fragmentos más parecidos

# Bloque para pruebas rápidas si este archivo se ejecuta como script
if __name__ == "__main__":
    pregunta = "¿Cómo configuro el modo ahorro de energía en el router?"
    top_fragmentos = buscar_fragmentos_parecidos(pregunta)
    for frag in top_fragmentos:
        print(f"\nDocumento: {frag['documento']}")  # Nombre del documento
        print(f"Similaridad: {frag['similaridad']:.4f}")  # Valor de similaridad
        print(f"Contenido: {frag['contenido'][:200]}...")  # Muestra un fragmento del texto
