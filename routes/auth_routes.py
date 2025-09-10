from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from flask_mail import Mail, Message
from models.user_model import (
    verificar_usuario, crear_usuario, buscar_por_email,
    actualizar_password_by_email, listar_usuarios
)
from config import MAIL_SETTINGS
import secrets, string

auth_bp = Blueprint("auth", __name__)
mail = Mail()

# Generar contraseñas temporales seguras
def generar_password_temporal(length=12):
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(caracteres) for _ in range(length))

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
                "nombre": usuario["nombre"],   # 👈 unificado
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
        nombre = request.form["nombre_usuario"]  # 👈 viene del form
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

            msg = Message(
                subject="Recuperación de contraseña - Sistema Minimarket",
                sender=MAIL_SETTINGS["MAIL_USERNAME"],
                recipients=[usuario["email"]]
            )
            msg.body = f"""
Estimado/a {usuario['nombre']},

Hemos recibido una solicitud para restablecer su contraseña.
Se le ha asignado una contraseña temporal segura:

{nueva_pass}

Por favor, inicie sesión con esta contraseña temporal y posteriormente cámbiela desde la sección de configuración de su cuenta.

Atentamente,  
Equipo de soporte - Sistema Ecomarket
"""
            mail.send(msg)

            flash("Se envió una contraseña temporal segura a su correo electrónico.")
            return redirect(url_for("auth.login"))
        else:
            flash("El correo ingresado no está registrado en el sistema.")
    return render_template("reset_password.html")
# 📌 Solicitud de cambio de contraseña (solo vendedores)
@auth_bp.route("/solicitud-password", methods=["GET", "POST"])
def solicitud_password():
    if "usuario" not in session or session["usuario"]["rol"] != "vendedor":
        flash("Solo los vendedores pueden acceder a esta opción.")
        return redirect(url_for("auth.login"))

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

        # Datos del vendedor que solicita
        vendedor = session["usuario"]

        # Crear el mensaje
        destinatarios = [a["email"] for a in admins if "email" in a]

        msg = Message(
            subject="Solicitud de Cambio de Contraseña - Minimarket CRM",
            sender=MAIL_SETTINGS["MAIL_USERNAME"],
            recipients=destinatarios
        )
        msg.body = f"""
Estimados administradores,

El usuario **{vendedor['nombre']}** con correo **{vendedor['email']}**
ha solicitado un cambio de contraseña para la cuenta:

📧 Correo a modificar: {email}
🔑 Nueva contraseña deseada: {nueva_password}

Por favor, validen la solicitud y realicen el cambio en el panel de administración.

Atentamente,  
Equipo de soporte - Sistema Ecomarket
"""
        mail.send(msg)

        flash("Solicitud enviada correctamente a los administradores.")
        return redirect(url_for("auth.dashboard_vendedor"))

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
