from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from models.user_model import (
    verificar_usuario, crear_usuario, buscar_por_email,
    actualizar_password_by_email, listar_usuarios
)
from config import MAIL_SETTINGS
import secrets
import string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

auth_bp = Blueprint("auth", __name__)


# Generar contraseñas temporales seguras
def generar_password_temporal(length=12):
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(caracteres) for _ in range(length))


# Función para enviar emails con SendGrid Web API
def enviar_email_sendgrid(destinatario, asunto, cuerpo_texto, cuerpo_html=None):
    """Envía emails usando SendGrid Web API (no SMTP)"""
    try:
        message = Mail(
            from_email=MAIL_SETTINGS['MAIL_DEFAULT_SENDER'],
            to_emails=destinatario,
            subject=asunto,
            html_content=cuerpo_html if cuerpo_html else cuerpo_texto
        )
        
        sg = SendGridAPIClient(MAIL_SETTINGS['MAIL_PASSWORD'])
        response = sg.send(message)
        
        print(f"✅ Email enviado exitosamente a {destinatario} - Status: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando email: {e}")
        import traceback
        traceback.print_exc()
        return False


# LOGIN
@auth_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        usuario = verificar_usuario(email, password)
        if usuario:
            # ✅ Verificar estado del usuario
            if usuario.get("estado", "").lower() != "activo":
                flash("Tu cuenta está inactiva. Contacta al administrador.")
                return redirect(url_for("auth.login"))

            session["usuario"] = {
                "id": str(usuario["_id"]),
                "nombre": usuario["nombre"],
                "rol": usuario.get("rol", ""),
                "email": usuario["email"]
            }
            if usuario.get("rol") == "administrador":
                return redirect(url_for("auth.dashboard_admin"))
            else:
                return redirect(url_for("auth.dashboard_vendedor"))
        else:
            flash("Credenciales inválidas")
    return render_template("login.html")


# REGISTRO
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form["nombre_usuario"]
        email = request.form["email"]
        password = request.form["password"]

        # ✅ Verificar que no exista un usuario con ese correo
        existente = buscar_por_email(email)
        if existente:
            flash("El correo ya está registrado. Intenta con otro.")
            return redirect(url_for("auth.register"))

        # ✅ Crear usuario con rol vacío y estado inactivo
        crear_usuario(nombre, email, password, rol="none", estado="inactivo")
        flash("Usuario registrado correctamente. Espera a que un administrador active tu cuenta.")
        return redirect(url_for("auth.login"))
    return render_template("register.html")


# RECUPERACIÓN DE CONTRASEÑA
@auth_bp.route("/reset", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form["email"]
        usuario = buscar_por_email(email)
        if usuario:
            nueva_pass = generar_password_temporal()
            res = actualizar_password_by_email(usuario["email"], nueva_pass)
            print("Resultado reset_password ->", res)

            # Cuerpo del email en texto plano
            cuerpo_texto = f"""
Estimado/a {usuario['nombre']},

Hemos recibido una solicitud para restablecer su contraseña.
Se le ha asignado una contraseña temporal segura:

{nueva_pass}

Por favor, inicie sesión con esta contraseña temporal y posteriormente cámbiela desde la sección de configuración de su cuenta.

Atentamente,  
Equipo de soporte - Sistema Minimarket CRM
"""

            # Cuerpo del email en HTML
            cuerpo_html = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid #165d2a; border-radius: 10px;">
      <h2 style="color: #165d2a; text-align: center;">🏪 Minimarket CRM</h2>
      <h3 style="color: #165d2a;">Recuperación de Contraseña</h3>
      
      <p>Estimado/a <strong>{usuario['nombre']}</strong>,</p>
      
      <p>Hemos recibido una solicitud para restablecer su contraseña.</p>
      
      <div style="background: #f8cf0f; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p style="margin: 0;"><strong>Contraseña temporal:</strong></p>
        <p style="font-size: 18px; font-weight: bold; margin: 10px 0; color: #165d2a;">{nueva_pass}</p>
      </div>
      
      <p>Por favor, inicie sesión con esta contraseña temporal y posteriormente cámbiela desde la sección de configuración de su cuenta.</p>
      
      <hr style="border: 1px solid #165d2a; margin: 20px 0;">
      
      <p style="font-size: 12px; color: #666;">
        Atentamente,<br>
        <strong>Equipo de soporte - Sistema Minimarket CRM</strong>
      </p>
    </div>
  </body>
</html>
"""

            # Enviar email con SendGrid API
            if enviar_email_sendgrid(
                usuario["email"],
                "Recuperación de contraseña - Sistema Minimarket",
                cuerpo_texto,
                cuerpo_html
            ):
                flash("✅ Se envió una contraseña temporal segura a su correo electrónico.")
            else:
                flash("⚠️ Se generó la contraseña pero hubo un problema al enviar el email.")
            
            return redirect(url_for("auth.login"))
        else:
            flash("El correo ingresado no está registrado en el sistema.")
    return render_template("reset_password.html")


# 📌 Solicitud de cambio de contraseña
@auth_bp.route("/solicitud-password", methods=["GET", "POST"])
def solicitud_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        nueva_password = request.form.get("nueva_password", "").strip()

        if not email or not nueva_password:
            flash("Debes ingresar el correo y la nueva contraseña.")
            return redirect(url_for("auth.solicitud_password"))

        # Buscar administradores
        admins = [u for u in listar_usuarios() if u.get("rol") == "administrador"]

        if not admins:
            flash("No hay administradores registrados para procesar la solicitud.")
            return redirect(url_for("auth.solicitud_password"))

        # Obtener datos del solicitante
        if "usuario" in session:
            solicitante = session["usuario"]["nombre"]
            email_solicitante = session["usuario"]["email"]
        else:
            solicitante = "Usuario no identificado"
            email_solicitante = email

        # Enviar email a cada administrador
        enviados = 0
        for admin in admins:
            if "email" not in admin:
                continue
            
            # Cuerpo del email en texto plano
            cuerpo_texto = f"""
Estimados administradores,

El usuario {solicitante} con correo {email_solicitante}
ha solicitado un cambio de contraseña para la cuenta:

📧 Correo a modificar: {email}
🔑 Nueva contraseña deseada: {nueva_password}

Por favor, validen la solicitud y realicen el cambio en el panel de administración.

Atentamente,  
Equipo de soporte - Sistema Minimarket CRM
"""

            # Cuerpo del email en HTML
            cuerpo_html = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid #165d2a; border-radius: 10px;">
      <h2 style="color: #165d2a; text-align: center;">🏪 Minimarket CRM</h2>
      <h3 style="color: #165d2a;">Solicitud de Cambio de Contraseña</h3>
      
      <p>Estimados administradores,</p>
      
      <p>El usuario <strong>{solicitante}</strong> con correo <strong>{email_solicitante}</strong> ha solicitado un cambio de contraseña.</p>
      
      <div style="background: #ebf3f3; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #165d2a;">
        <p style="margin: 5px 0;"><strong>📧 Correo a modificar:</strong> {email}</p>
        <p style="margin: 5px 0;"><strong>🔑 Nueva contraseña deseada:</strong></p>
        <p style="font-size: 16px; font-weight: bold; margin: 10px 0; color: #165d2a;">{nueva_password}</p>
      </div>
      
      <p>Por favor, validen la solicitud y realicen el cambio en el panel de administración.</p>
      
      <hr style="border: 1px solid #165d2a; margin: 20px 0;">
      
      <p style="font-size: 12px; color: #666;">
        Atentamente,<br>
        <strong>Equipo de soporte - Sistema Minimarket CRM</strong>
      </p>
    </div>
  </body>
</html>
"""

            if enviar_email_sendgrid(
                admin["email"],
                "Solicitud de Cambio de Contraseña - Minimarket CRM",
                cuerpo_texto,
                cuerpo_html
            ):
                enviados += 1

        if enviados > 0:
            flash(f"✅ Solicitud enviada correctamente a {enviados} administrador(es).")
        else:
            flash("❌ Error al enviar la solicitud. Intenta nuevamente.")
        
        return redirect(url_for("auth.solicitud_password"))

    return render_template("solicitud_password.html")


# DASHBOARD ADMIN
@auth_bp.route("/dashboard/admin")
def dashboard_admin():
    if "usuario" in session and session["usuario"]["rol"] == "administrador":
        return render_template("dashboard_admin.html", usuario=session["usuario"])
    return redirect(url_for("auth.login"))


# DASHBOARD VENDEDOR
@auth_bp.route("/dashboard/vendedor")
def dashboard_vendedor():
    if "usuario" in session and session["usuario"]["rol"] == "vendedor":
        return render_template("dashboard_vendedor.html", usuario=session["usuario"])
    return redirect(url_for("auth.login"))


# LOGOUT
@auth_bp.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("auth.login"))
