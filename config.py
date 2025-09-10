import os
from pymongo import MongoClient

# Configuración de MongoDB usando variables de entorno
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://p4x:p4xroot@cluster0.fjoy1qr.mongodb.net/minimarket_db')
client = MongoClient(MONGO_URI)
db = client[os.getenv('MONGO_DB_NAME', 'minimarket_db')]

# Configuración para envío de correo usando variables de entorno
MAIL_SETTINGS = {
    "MAIL_SERVER": os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
    "MAIL_PORT": int(os.getenv('MAIL_PORT', 587)),
    "MAIL_USE_TLS": os.getenv('MAIL_USE_TLS', 'True').lower() == 'true',
    "MAIL_USERNAME": os.getenv('MAIL_USERNAME', 'william876540@gmail.com'),
    "MAIL_PASSWORD": os.getenv('MAIL_PASSWORD', 'ftpmtklhdqcvlqll')
}
