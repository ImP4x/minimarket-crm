from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.user_model import listar_usuarios, crear_usuario, actualizar_usuario, eliminar_usuario

usuarios_bp = Blueprint("usuarios", __name__)

def _solo_admin():
    """Devuelve True si hay sesión y el usuario es administrador."""
    return "usuario" in session and session["usuario"].get("rol") == "administrador"

@usuarios_bp.route("/usuarios", methods=["GET", "POST"])
def usuarios():
    """Listado de usuarios (solo admin) y creación de nuevo usuario."""
    if not _solo_admin():
        flash("Acceso denegado.")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        # Creación de nuevo usuario
        nombre = request.form.get("nombre_usuario", "").strip()
        email = request.form.get("email_usuario", "").strip()
        password = request.form.get("password_usuario", "").strip()
        rol = request.form.get("rol_usuario", "none").strip()
        estado = request.form.get("estado_usuario", "inactivo").strip()

        if not nombre or not email or not password:
            flash("Nombre, email y contraseña son obligatorios para crear usuario.")
            return redirect(url_for("usuarios.usuarios"))

        # Comprobar si ya existe usuario con ese email
        from models.user_model import buscar_por_email
        existente = buscar_por_email(email)
        if existente:
            flash("El correo ya está registrado. Intenta con otro.")
            return redirect(url_for("usuarios.usuarios"))

        crear_usuario(nombre, email, password, rol=rol, estado=estado)
        flash("Usuario creado correctamente.")
        return redirect(url_for("usuarios.usuarios"))

    # GET: Listar usuarios
    lista = listar_usuarios()
    return render_template("usuarios.html", usuarios=lista)

@usuarios_bp.route("/usuarios/editar/<user_id>", methods=["POST"])
def editar_usuario(user_id):
    """Permite actualizar nombre, email, rol, estado y/o contraseña."""
    if not _solo_admin():
        flash("Acceso denegado.")
        return redirect(url_for("auth.login"))

    nombre = request.form.get("nombre", "").strip()
    email = request.form.get("email", "").strip()
    rol = request.form.get("rol", "").strip()
    estado = request.form.get("estado", "").strip()
    nueva_password = request.form.get("nueva_password", "").strip()

    if not nombre or not email:
        flash("Nombre y email son obligatorios.")
        return redirect(url_for("usuarios.usuarios"))

    resultado = actualizar_usuario(
        user_id,
        nombre=nombre,
        email=email,
        rol=rol,
        estado=estado,
        nueva_password=nueva_password if nueva_password else None
    )

    if resultado.get("modified_count", 0) > 0:
        flash("Usuario actualizado correctamente.")
    else:
        flash("No se realizaron cambios o el usuario no fue encontrado.")

    return redirect(url_for("usuarios.usuarios"))


@usuarios_bp.route("/usuarios/eliminar/<user_id>", methods=["POST"])
def eliminar_usuario_route(user_id):
    """Eliminar usuario por ID (solo admin). Evita que el admin se borre a sí mismo."""
    if not _solo_admin():
        flash("Acceso denegado.")
        return redirect(url_for("auth.login"))

    current_id = session["usuario"].get("id")
    if current_id == str(user_id):
        flash("No puede eliminar su propia cuenta.")
        return redirect(url_for("usuarios.usuarios"))

    resultado = eliminar_usuario(user_id)
    if resultado.get("deleted_count", 0) > 0:
        flash("Usuario eliminado correctamente.")
    else:
        flash("No se pudo eliminar el usuario.")
    return redirect(url_for("usuarios.usuarios"))
