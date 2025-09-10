from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.producto_model import crear_producto, listar_productos, actualizar_producto, eliminar_producto

productos_bp = Blueprint("productos", __name__)

def _usuario_logueado_y_permiso():
    if "usuario" not in session:
        return False
    return session["usuario"].get("rol") in ("administrador", "vendedor")

@productos_bp.route("/productos", methods=["GET", "POST"])
def productos():
    if not _usuario_logueado_y_permiso():
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        nombre = request.form.get("nombre")
        precio = request.form.get("precio")
        categoria = request.form.get("categoria")
        cantidad = request.form.get("cantidad", 0)

        if not nombre or not precio:
            flash("Nombre y precio son obligatorios.")
            return redirect(url_for("productos.productos"))

        crear_producto(nombre, precio, categoria, cantidad)
        flash("Producto creado correctamente.")
        return redirect(url_for("productos.productos"))

    lista = listar_productos()
    return render_template("productos.html", productos=lista)

@productos_bp.route("/productos/editar/<producto_id>", methods=["POST"])
def editar_producto(producto_id):
    if not _usuario_logueado_y_permiso():
        return redirect(url_for("auth.login"))

    nombre = request.form.get("nombre")
    precio = request.form.get("precio")
    categoria = request.form.get("categoria")
    cantidad = request.form.get("cantidad")

    actualizar_producto(producto_id, nombre, precio, categoria, cantidad)
    flash("Producto actualizado correctamente.")
    return redirect(url_for("productos.productos"))

@productos_bp.route("/productos/eliminar/<producto_id>", methods=["POST"])
def eliminar_producto_route(producto_id):
    if not _usuario_logueado_y_permiso():
        return redirect(url_for("auth.login"))

    eliminar_producto(producto_id)
    flash("Producto eliminado correctamente.")
    return redirect(url_for("productos.productos"))