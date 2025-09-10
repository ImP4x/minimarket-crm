from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from models.ventas_model import listar_productos, registrar_venta, obtener_factura, listar_facturas
from models.cliente_model import listar_clientes, obtener_cliente_por_id
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from bson.objectid import ObjectId
import gridfs
from config import db

ventas_bp = Blueprint("ventas", __name__)

# Inicializar GridFS
fs = gridfs.GridFS(db)

# -------------------------
# Helper: Generar PDF
# -------------------------
def generar_pdf_factura(factura):
    """Genera un PDF en memoria con los datos de la factura y devuelve los bytes."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(200, 770, "MINIMARKET CRM - FACTURA")

    p.setFont("Helvetica", 12)
    p.drawString(50, 740, f"Factura ID: {str(factura.get('_id', ''))}")
    p.drawString(50, 720, f"Fecha: {factura['fecha'].strftime('%Y-%m-%d %H:%M:%S')}")

    # Línea de separación
    p.line(50, 710, 550, 710)

    # Datos del cliente
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 690, "Datos del Cliente")
    p.setFont("Helvetica", 12)
    p.drawString(50, 670, f"Cliente: {factura['cliente']}")

    # Detalle del producto
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 640, "Detalle de la Venta")
    p.setFont("Helvetica", 12)
    p.drawString(50, 620, f"Producto: {factura['producto']}")
    p.drawString(50, 600, f"Cantidad: {factura['cantidad']}")
    p.drawString(50, 580, f"Total: ${factura['total']}")

    # Vendedor
    vendedor = factura.get("vendedor", "N/A")
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, 550, "Atendido por:")
    p.setFont("Helvetica", 12)
    p.drawString(150, 550, vendedor)

    # Pie de página
    p.line(50, 100, 550, 100)
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(200, 85, "Gracias por su compra en MINIMARKET CRM")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

# 📌 Registro de ventas
@ventas_bp.route("/ventas", methods=["GET", "POST"])
def ventas():
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        cliente_id = request.form["cliente"]
        producto_id = request.form["producto"]
        cantidad = int(request.form["cantidad"])

        cliente = obtener_cliente_por_id(cliente_id)
        vendedor = session["usuario"]["nombre"]

        venta_id, error = registrar_venta(cliente, producto_id, cantidad, vendedor=vendedor)
        if error:
            flash(error)
            return redirect(url_for("ventas.ventas"))

        # Generar y guardar PDF en GridFS
        factura = obtener_factura(venta_id)
        if factura:
            pdf_bytes = generar_pdf_factura(factura)
            pdf_id = fs.put(pdf_bytes, filename=f"factura_{venta_id}.pdf")
            # actualizar factura con referencia al PDF
            from config import db
            db["historial_facturas"].update_one(
                {"venta_id": ObjectId(str(venta_id))},
                {"$set": {"pdf_id": pdf_id}}
            )

        flash("Venta registrada exitosamente.")
        return redirect(url_for("ventas.ver_factura", venta_id=venta_id))

    productos = listar_productos()
    clientes = listar_clientes()
    return render_template("ventas.html", productos=productos, clientes=clientes)

# 📌 Ver factura en HTML
@ventas_bp.route("/ventas/factura/<venta_id>")
def ver_factura(venta_id):
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    factura = obtener_factura(venta_id)
    if not factura:
        flash("Factura no encontrada")
        return redirect(url_for("ventas.ventas"))

    return render_template("factura.html", factura=factura)

# 📌 Descargar factura en PDF (desde BD - GridFS)
@ventas_bp.route("/ventas/factura/<venta_id>/pdf")
def descargar_factura_pdf(venta_id):
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    factura = obtener_factura(venta_id)
    if not factura or "pdf_id" not in factura:
        flash("PDF no disponible para esta factura")
        return redirect(url_for("ventas.ver_factura", venta_id=venta_id))

    pdf_file = fs.get(factura["pdf_id"])
    return send_file(
        BytesIO(pdf_file.read()),
        as_attachment=True,
        download_name=f"factura_{venta_id}.pdf",
        mimetype="application/pdf"
    )

# 📌 Listar todas las facturas
@ventas_bp.route("/ventas/facturas")
def listar_facturas_view():
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    facturas = listar_facturas()
    return render_template("facturas.html", facturas=facturas)

# 📌 Mostrar stock actual
@ventas_bp.route("/ventas/stock")
def ver_stock():
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    productos = listar_productos()
    return render_template("stock.html", productos=productos)