import os
from dotenv import load_dotenv

# Cargar las variables desde el .env
load_dotenv()

db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

email_config = {
    "host": os.getenv("EMAIL_HOST"),
    "port": int(os.getenv("EMAIL_PORT", 587)),  # convertir a int
    "user": os.getenv("EMAIL_USER"),
    "password": os.getenv("EMAIL_PASSWORD"),
    "to": os.getenv("EMAIL_TO")
}

# Ahora tomamos la clave de OpenAI en lugar de la antigua API_KEY de Gemini
api_key = os.getenv("OPENAI_API_KEY")
