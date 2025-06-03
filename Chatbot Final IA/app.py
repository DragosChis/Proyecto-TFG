from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from rutas.api import api_blueprint

# Cargar variables de entorno definidas en archivo .env (e.g., claves de API, configuraciones)
load_dotenv()

# Crear la aplicación Flask
app = Flask(__name__)
# Habilitar CORS para permitir solicitudes desde otros dominios/orígenes
CORS(app)

# Registrar el Blueprint que contiene las rutas de la API
# - api_blueprint se define en rutas/api.py
# - Agrupa y organiza las rutas bajo un mismo prefijo si es necesario
app.register_blueprint(api_blueprint)

# Punto de entrada de la aplicación
if __name__ == '__main__':
    # Iniciar el servidor en modo debug en el puerto 5000
    app.run(debug=True, port=5000)
