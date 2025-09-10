from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from models.ventas_model import (
    listar_productos, registrar_venta, obtener_factura, listar_facturas,
    obtener_ventas_por_periodo, obtener_ventas_detalladas_por_periodo
)
from models.cliente_model import listar_clientes, obtener_cliente_por_id
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import gridfs
from config import db

ventas_bp = Blueprint("ventas", __name__)

# Inicializar GridFS
fs = gridfs.GridFS(db)

# -------------------------
# Helper: Generar PDF Mejorado
# -------------------------
def generar_pdf_factura_mejorada(factura):
    """Genera un PDF mejorado en memoria con los datos de la factura."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=60, bottomMargin=18)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['Normal']
    
    # Título principal
    title = Paragraph("🏪 FACTURA - MINIMARKET CRM", title_style)
    elements.append(title)
    elements.append(Spacer(1, 20))
    
    # Información general de la factura
    info_data = [
        ["📄 ID Factura:", str(factura.get('_id', ''))],
        ["📅 Fecha:", factura['fecha'].strftime('%d/%m/%Y %H:%M:%S')],
        ["👤 Cliente:", factura.get('cliente', 'No disponible')],
        ["📧 Email Cliente:", factura.get('cliente_email', 'No disponible')],
        ["🧑‍💼 Atendido Por:", factura.get('vendedor', 'No disponible')]
    ]

    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 30))
    
    # Título para detalle de productos
    subtitle = Paragraph("📦 DETALLE DE LA VENTA", styles['Heading2'])
    elements.append(subtitle)
    elements.append(Spacer(1, 15))

    # Tabla de productos vendidos
    product_data = [["Producto", "Cantidad", "Total"]]
    product_data.append([
        factura.get('producto', 'No disponible'),
        str(factura.get('cantidad', '')),
        f"${factura.get('total', ''):,.2f}"
    ])

    prod_table = Table(product_data, colWidths=[4*inch, 1*inch, 2*inch])
    prod_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.dodgerblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
    ]))
    elements.append(prod_table)
    elements.append(Spacer(1, 40))

    # Footer de agradecimiento
    footer = Paragraph("✨ ¡Gracias por su compra en MINIMARKET CRM! ✨", styles['Heading3'])
    elements.append(footer)

    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# Mantener función original para compatibilidad
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

        # Generar y guardar PDF mejorado en GridFS
        factura = obtener_factura(venta_id)
        if factura:
            # Usar la nueva función mejorada
            pdf_bytes = generar_pdf_factura_mejorada(factura)
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

# 📊 NUEVO: Reporte de ventas con filtros de periodo
@ventas_bp.route("/reporte_ventas")
def reporte_ventas():
    if "usuario" not in session:
        return redirect(url_for("auth.login"))
    
    # Obtener filtro de periodo desde query string (?periodo=semanal)
    periodo = request.args.get('periodo', 'semanal')
    hoy = datetime.utcnow()
    
    # Calcular fechas según el periodo
    if periodo == 'semanal':
        fecha_inicio = hoy - timedelta(days=7)
        titulo_periodo = "Últimos 7 días"
    elif periodo == 'mensual':
        fecha_inicio = hoy - timedelta(days=30)
        titulo_periodo = "Últimos 30 días"
    elif periodo == 'anual':
        fecha_inicio = hoy - timedelta(days=365)
        titulo_periodo = "Último año"
    else:
        # Default a semanal
        fecha_inicio = hoy - timedelta(days=7)
        titulo_periodo = "Últimos 7 días"
        periodo = 'semanal'
    
    # Obtener estadísticas y ventas detalladas
    estadisticas = obtener_ventas_por_periodo(fecha_inicio, hoy)
    ventas_detalladas = obtener_ventas_detalladas_por_periodo(fecha_inicio, hoy)
    
    return render_template(
        'reporte_ventas.html',
        estadisticas=estadisticas,
        ventas_detalladas=ventas_detalladas,
        periodo_actual=periodo,
        titulo_periodo=titulo_periodo,
        fecha_inicio=fecha_inicio.strftime('%d/%m/%Y'),
        fecha_fin=hoy.strftime('%d/%m/%Y')
    )