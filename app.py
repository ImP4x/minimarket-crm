import os
from flask import Flask
from flask_mail import Mail
from config import MAIL_SETTINGS
from routes.auth_routes import auth_bp
from routes.cliente_routes import cliente_bp
from routes.ventas_routes import ventas_bp
from routes.usuarios_routes import usuarios_bp
from routes.producto_routes import productos_bp

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

# Configuración de correo
app.config.update(MAIL_SETTINGS)
mail = Mail(app)

# Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(cliente_bp)
app.register_blueprint(ventas_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(productos_bp)

# Configuración para Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
