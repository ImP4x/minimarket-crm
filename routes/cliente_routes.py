from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.cliente_model import (
    crear_cliente, listar_clientes, buscar_cliente_por_id,
    actualizar_cliente, eliminar_cliente, reporte_por_pais
)

cliente_bp = Blueprint("cliente", __name__)

def _usuario_logueado_y_permiso():
    """
    Helper: devuelve True si hay sesión y rol válido para acceder a clientes.
    Admin y vendedor tienen acceso al módulo 1 según la consigna.
    """
    if "usuario" not in session:
        return False
    rol = session["usuario"].get("rol")
    return rol in ("administrador", "vendedor")

# 📌 Listar clientes y crear nuevo (Componente A - CRUD)
@cliente_bp.route("/clientes", methods=["GET", "POST"])
def clientes():
    if not _usuario_logueado_y_permiso():
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        # Crear nuevo cliente (form en la misma página)
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        telefono = request.form.get("telefono", "").strip()
        direccion = request.form.get("direccion", "").strip()
        ciudad = request.form.get("ciudad", "").strip()
        pais = request.form.get("pais", "").strip()

        if not nombre:
            flash("El nombre del cliente es obligatorio.")
            return redirect(url_for("cliente.clientes"))

        try:
            crear_cliente(nombre, email, telefono, direccion, ciudad, pais)
            flash("Cliente creado correctamente.")
        except Exception as e:
            print("❌ Error crear_cliente:", e)
            flash("Ocurrió un error al crear el cliente.")
        return redirect(url_for("cliente.clientes"))

    # GET: listado (con posible búsqueda por querystring ?q=)
    q = request.args.get("q", None)
    lista = listar_clientes(q)
    return render_template("clientes.html", clientes=lista, q=q)

# 📌 Editar cliente (se envía desde la misma página)
@cliente_bp.route("/clientes/editar/<client_id>", methods=["POST"])
def editar_cliente(client_id):
    if not _usuario_logueado_y_permiso():
        return redirect(url_for("auth.login"))

    nombre = request.form.get("nombre", None)
    email = request.form.get("email", None)
    telefono = request.form.get("telefono", None)
    direccion = request.form.get("direccion", None)
    ciudad = request.form.get("ciudad", None)
    pais = request.form.get("pais", None)

    try:
        resultado = actualizar_cliente(client_id, nombre, email, telefono, direccion, ciudad, pais)
        if resultado.get("modified_count", 0) > 0:
            flash("Cliente actualizado correctamente.")
        else:
            flash("No se realizaron cambios o el cliente no fue encontrado.")
    except Exception as e:
        print("❌ Error actualizar_cliente:", e)
        flash("Ocurrió un error al actualizar el cliente.")

    return redirect(url_for("cliente.clientes"))

# 📌 Eliminar cliente
@cliente_bp.route("/clientes/eliminar/<client_id>", methods=["POST"])
def eliminar_cliente_route(client_id):
    if not _usuario_logueado_y_permiso():
        return redirect(url_for("auth.login"))

    try:
        resultado = eliminar_cliente(client_id)
        if resultado.get("deleted_count", 0) > 0:
            flash("Cliente eliminado correctamente.")
        else:
            flash("No se pudo eliminar el cliente.")
    except Exception as e:
        print("❌ Error eliminar_cliente:", e)
        flash("Ocurrió un error al eliminar el cliente.")

    return redirect(url_for("cliente.clientes"))

# 📌 Componente B: reporte clasificación por país
@cliente_bp.route("/clientes/reporte/pais")
def reporte_clientes_por_pais():
    if not _usuario_logueado_y_permiso():
        return redirect(url_for("auth.login"))

    datos = reporte_por_pais()  # [{'_id': 'Colombia', 'total': 10}, ...]
    return render_template("clientes_reporte_pais.html", datos=datos)