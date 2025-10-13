from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.contrato_model import (
    crear_contrato, listar_contratos, obtener_contrato_por_id,
    actualizar_contrato, eliminar_contrato
)
from models.empleado_model import listar_empleados

contrato_bp = Blueprint("contrato", __name__)

def _usuario_logueado_y_permiso():
    """Helper: devuelve True si hay sesión y rol válido"""
    if "usuario" not in session:
        return False
    rol = session["usuario"].get("rol")
    return rol in ("administrador", "vendedor")

# 📌 Listar contratos y crear nuevo
@contrato_bp.route("/contratos", methods=["GET", "POST"])
def contratos():
    if not _usuario_logueado_y_permiso():
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        # Crear nuevo contrato
        empleado_id = request.form.get("empleado_id", "").strip()
        tipo_contrato = request.form.get("tipo_contrato", "").strip()
        fecha_inicio = request.form.get("fecha_inicio", "").strip()
        fecha_fin = request.form.get("fecha_fin", "").strip()
        salario = request.form.get("salario", "").strip()
        cargo = request.form.get("cargo", "").strip()
        observaciones = request.form.get("observaciones", "").strip()

        if not empleado_id or not tipo_contrato or not fecha_inicio or not salario or not cargo:
            flash("Empleado, tipo de contrato, fecha inicio, salario y cargo son obligatorios.")
            return redirect(url_for("contrato.contratos"))

        try:
            crear_contrato(empleado_id, tipo_contrato, fecha_inicio, fecha_fin, 
                         salario, cargo, observaciones)
            flash("Contrato creado correctamente.")
        except Exception as e:
            print("❌ Error crear_contrato:", e)
            flash("Ocurrió un error al crear el contrato.")
        return redirect(url_for("contrato.contratos"))

    # GET: listado con posible búsqueda
    q = request.args.get("q", None)
    lista_contratos = listar_contratos(q)
    lista_empleados = listar_empleados()
    return render_template("contratos.html", contratos=lista_contratos, empleados=lista_empleados, q=q)

# 📌 Editar contrato
@contrato_bp.route("/contratos/editar/<contrato_id>", methods=["POST"])
def editar_contrato(contrato_id):
    if not _usuario_logueado_y_permiso():
        return redirect(url_for("auth.login"))

    tipo_contrato = request.form.get("tipo_contrato", None)
    fecha_inicio = request.form.get("fecha_inicio", None)
    fecha_fin = request.form.get("fecha_fin", None)
    salario = request.form.get("salario", None)
    cargo = request.form.get("cargo", None)
    observaciones = request.form.get("observaciones", None)

    try:
        resultado = actualizar_contrato(contrato_id, tipo_contrato, fecha_inicio,
                                       fecha_fin, salario, cargo, observaciones)
        if resultado.get("modified_count", 0) > 0:
            flash("Contrato actualizado correctamente.")
        else:
            flash("No se realizaron cambios o el contrato no fue encontrado.")
    except Exception as e:
        print("❌ Error actualizar_contrato:", e)
        flash("Ocurrió un error al actualizar el contrato.")

    return redirect(url_for("contrato.contratos"))

# 📌 Eliminar contrato
@contrato_bp.route("/contratos/eliminar/<contrato_id>", methods=["POST"])
def eliminar_contrato_route(contrato_id):
    if not _usuario_logueado_y_permiso():
        return redirect(url_for("auth.login"))

    try:
        resultado = eliminar_contrato(contrato_id)
        if resultado.get("deleted_count", 0) > 0:
            flash("Contrato eliminado correctamente.")
        else:
            flash("No se pudo eliminar el contrato.")
    except Exception as e:
        print("❌ Error eliminar_contrato:", e)
        flash("Ocurrió un error al eliminar el contrato.")

    return redirect(url_for("contrato.contratos"))
