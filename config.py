import os
from arango import ArangoClient

# Configuración de ArangoDB usando variables de entorno
ARANGO_HOST = os.getenv('ARANGO_HOST', 'https://3d098d1d6628.arangodb.cloud:8529')
ARANGO_DB_NAME = os.getenv('ARANGO_DB_NAME', 'minimarket_db')
ARANGO_USERNAME = os.getenv('ARANGO_USERNAME', 'root')
ARANGO_PASSWORD = os.getenv('ARANGO_PASSWORD', 'Q2QlGWMP02FLtUXbSH9')

# Inicializar cliente de ArangoDB
client = ArangoClient(hosts=ARANGO_HOST)

# Conectar a la base de datos (o crearla si no existe)
sys_db = client.db('_system', username=ARANGO_USERNAME, password=ARANGO_PASSWORD)

# Verificar si la base de datos existe, si no, crearla
if not sys_db.has_database(ARANGO_DB_NAME):
    sys_db.create_database(ARANGO_DB_NAME)

# Conectar a la base de datos del proyecto
db = client.db(ARANGO_DB_NAME, username=ARANGO_USERNAME, password=ARANGO_PASSWORD)

# Configuración de email con SendGrid (sin cambios)
MAIL_SETTINGS = {
    'MAIL_SERVER': 'smtp.sendgrid.net',
    'MAIL_PORT': 587,
    'MAIL_USE_TLS': True,
    'MAIL_USE_SSL': False,
    'MAIL_USERNAME': 'apikey',
    'MAIL_PASSWORD': os.getenv('SENDGRID_API_KEY', ''),
    'MAIL_DEFAULT_SENDER': 'william876540@gmail.com'
}
