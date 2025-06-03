import os  # Para acceder a las variables de entorno
from openai import OpenAI  # Cliente de OpenAI para acceder a la API
from dotenv import load_dotenv  # Para cargar las variables de entorno desde un archivo .env

# Cargamos las variables de entorno (.env) para no exponer claves en el código
load_dotenv()
# Creamos el cliente de OpenAI con la clave de API cargada
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Función para obtener el embedding (vector numérico) de un texto dado
def obtener_embedding(texto):
    response = client.embeddings.create(  # Llamada a la API de OpenAI para crear el embedding
        input=texto,  # El texto del que queremos generar el embedding
        model="text-embedding-3-small"  # Modelo de OpenAI específico para embeddings
    )
    # Devuelve el embedding (vector) de la primera respuesta
    return response.data[0].embedding
