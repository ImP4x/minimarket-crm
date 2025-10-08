import os
from pymongo import MongoClient

# Configuración de MongoDB usando variables de entorno
MONGO_URI = os.getenv('MONGO_URI', 'mongodb+srv://p4x:p4xroot@cluster0.fjoy1qr.mongodb.net/minimarket_db')
client = MongoClient(MONGO_URI)
db = client[os.getenv('MONGO_DB_NAME', 'minimarket_db')]

# Configuración de email con SendGrid
MAIL_SETTINGS = {
    'MAIL_SERVER': 'smtp.sendgrid.net',
    'MAIL_PORT': 587,
    'MAIL_USE_TLS': True,
    'MAIL_USE_SSL': False,
    'MAIL_USERNAME': 'apikey',  # Siempre es 'apikey'
    'MAIL_PASSWORD': os.getenv('SENDGRID_API_KEY', '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'),
    'MAIL_DEFAULT_SENDER': 'william876540@gmail.com'
}