from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from models.ventas_model import (
    listar_productos, obtener_factura, listar_facturas,
    obtener_ventas_por_periodo, obtener_ventas_detalladas_por_periodo, obtener_stock
)
from models.cliente_model import listar_clientes, obtener_cliente_por_id
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta
from config import db
import base64



ventas_bp = Blueprint("ventas", __name__)


# Obtener o crear colecciones
def get_collection(name):
    """Helper para obtener o crear una colección"""
    if db.has_collection(name):
        return db.collection(name)
    else:
        return db.create_collection(name)


# Referencias a colecciones
ventas_collection = get_collection("ventas")
facturas_collection = get_collection("historial_facturas")
productos_collection = get_collection("productos")
stock_collection = get_collection("stock")



# -------------------------
# Helper: Generar PDF Mejorado con MÚLTIPLES productos
# -------------------------
def generar_pdf_factura_mejorada(factura):
    """Genera un PDF profesional y moderno con los colores del proyecto"""
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.colors import HexColor
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=50,
        leftMargin=50,
        topMargin=40,
        bottomMargin=40
    )
    elements = []
    styles = getSampleStyleSheet()
    
    # Colores del proyecto
    color_primary = HexColor('#165d2a')  # Verde
    color_secondary = HexColor('#f8cf0f')  # Amarillo
    color_light = HexColor('#ebf3f3')  # Fondo claro
    color_dark = HexColor('#2c2c2c')  # Texto oscuro
    
    # ===== ENCABEZADO CON LOGO Y TÍTULO =====
    header_data = [
        [
            Paragraph("<b style='font-size:24; color:#165d2a;'>🏪 MINIMARKET CRM</b>", styles['Normal']),
            Paragraph("<b style='font-size:16; color:#165d2a; text-align:right;'>FACTURA DE VENTA</b>", styles['Normal'])
        ]
    ]
    header_table = Table(header_data, colWidths=[3.5*inch, 3.5*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    elements.append(header_table)
    
    # Línea separadora decorativa
    line_table = Table([['']], colWidths=[7*inch])
    line_table.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 3, color_secondary),
        ('LINEBELOW', (0, 0), (-1, 0), 1, color_primary),
    ]))
    elements.append(line_table)
    elements.append(Spacer(1, 20))
    
    # ===== INFORMACIÓN DE FACTURA Y CLIENTE EN DOS COLUMNAS =====
    # Usar _key en lugar de _id
    factura_id_str = str(factura.get('_key', ''))[:12]
    
    info_izquierda = f"""
    <b><font color='#165d2a' size='12'>INFORMACIÓN DE FACTURA</font></b><br/>
    <b>ID:</b> {factura_id_str}...<br/>
    <b>Fecha:</b> {factura['fecha'].strftime('%d/%m/%Y')}<br/>
    <b>Hora:</b> {factura['fecha'].strftime('%H:%M:%S')}<br/>
    <b>Atendido por:</b> {factura.get('vendedor', 'No disponible')}
    """
    
    info_derecha = f"""
    <b><font color='#165d2a' size='12'>DATOS DEL CLIENTE</font></b><br/>
    <b>Nombre:</b> {factura.get('cliente', 'No disponible')}<br/>
    <b>Email:</b> {factura.get('cliente_email', 'No especificado')}<br/>
    <br/>
    """
    
    info_data = [
        [
            Paragraph(info_izquierda, styles['Normal']),
            Paragraph(info_derecha, styles['Normal'])
        ]
    ]
    info_table = Table(info_data, colWidths=[3.5*inch, 3.5*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), color_light),
        ('BACKGROUND', (1, 0), (1, 0), color_light),
        ('BOX', (0, 0), (0, 0), 2, color_primary),
        ('BOX', (1, 0), (1, 0), 2, color_primary),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 25))
    
    # ===== TÍTULO DE DETALLE =====
    subtitle = Paragraph(
        "<b style='font-size:14; color:#165d2a;'>📦 DETALLE DE LA COMPRA</b>",
        styles['Normal']
    )
    elements.append(subtitle)
    elements.append(Spacer(1, 10))
    
    # ===== TABLA DE PRODUCTOS =====
    product_data = [
        [
            Paragraph("<b>PRODUCTO</b>", styles['Normal']),
            Paragraph("<b>CANT.</b>", styles['Normal']),
            Paragraph("<b>PRECIO UNIT.</b>", styles['Normal']),
            Paragraph("<b>SUBTOTAL</b>", styles['Normal'])
        ]
    ]
    
    # Agregar productos
    if factura.get('productos'):
        for item in factura['productos']:
            product_data.append([
                Paragraph(f"<b>{item.get('nombre', 'No disponible')}</b>", styles['Normal']),
                Paragraph(f"<para align='center'>{item.get('cantidad', '')}</para>", styles['Normal']),
                Paragraph(f"<para align='right'>${item.get('precio', 0):,.2f}</para>", styles['Normal']),
                Paragraph(f"<para align='right'><b>${item.get('subtotal', 0):,.2f}</b></para>", styles['Normal'])
            ])
    else:
        # Compatibilidad con facturas antiguas
        precio_unit = factura.get('total', 0) / factura.get('cantidad', 1)
        product_data.append([
            Paragraph(f"<b>{factura.get('producto', 'No disponible')}</b>", styles['Normal']),
            Paragraph(f"<para align='center'>{factura.get('cantidad', '')}</para>", styles['Normal']),
            Paragraph(f"<para align='right'>${precio_unit:,.2f}</para>", styles['Normal']),
            Paragraph(f"<para align='right'><b>${factura.get('total', 0):,.2f}</b></para>", styles['Normal'])
        ])
    
    prod_table = Table(product_data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    prod_table.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), color_primary),
        ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (-1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Cuerpo
        ('BACKGROUND', (0, 1), (-1, -1), color_light),
        ('TEXTCOLOR', (0, 1), (-1, -1), color_dark),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        
        # Bordes
        ('BOX', (0, 0), (-1, -1), 2, color_primary),
        ('LINEBELOW', (0, 0), (-1, 0), 2, color_secondary),
        ('GRID', (0, 1), (-1, -1), 0.5, rl_colors.grey),
        
        # Alineación
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(prod_table)
    elements.append(Spacer(1, 15))
    
    # ===== TOTAL DESTACADO =====
    total_data = [
        [
            Paragraph("<b style='font-size:14;'>TOTAL A PAGAR:</b>", styles['Normal']),
            Paragraph(f"<b style='font-size:16; color:#165d2a;'>${factura.get('total', 0):,.2f}</b>", styles['Normal'])
        ]
    ]
    total_table = Table(total_data, colWidths=[5*inch, 2*inch])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), color_secondary),
        ('BOX', (0, 0), (-1, -1), 2, color_primary),
        ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(total_table)
    elements.append(Spacer(1, 30))
    
    # ===== FOOTER =====
    footer_text = """
    <para align='center'>
    <b style='font-size:12; color:#165d2a;'>✨ ¡Gracias por su compra! ✨</b><br/>
    <font size='9' color='#666666'>
    Este documento es un comprobante de pago válido.<br/>
    Para cualquier consulta, contáctenos.<br/>
    <b>MINIMARKET CRM</b> - Sistema de Gestión Empresarial
    </font>
    </para>
    """
    footer = Paragraph(footer_text, styles['Normal'])
    footer_table = Table([[footer]], colWidths=[7*inch])
    footer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), color_light),
        ('BOX', (0, 0), (-1, -1), 1, color_primary),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    elements.append(footer_table)
    
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
    p.drawString(50, 740, f"Factura ID: {str(factura.get('_key', ''))}")
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
    p.drawString(50, 620, f"Producto: {factura.get('producto', 'Múltiples productos')}")
    p.drawString(50, 600, f"Cantidad: {factura.get('cantidad', 'Ver detalle')}")
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



# 📌 Registro de ventas (con carrito múltiple - UNA SOLA FACTURA)
@ventas_bp.route("/ventas", methods=["GET", "POST"])
def ventas():
    if "usuario" not in session:
        return redirect(url_for("auth.login"))
    
    if request.method == "POST":
        try:
            cliente_id = request.form["cliente"]
            carrito_json = request.form.get("carrito")
            
            if not carrito_json:
                flash("El carrito está vacío")
                return redirect(url_for("ventas.ventas"))
            
            import json
            carrito = json.loads(carrito_json)
            
            if not carrito or len(carrito) == 0:
                flash("El carrito está vacío")
                return redirect(url_for("ventas.ventas"))
            
            cliente = obtener_cliente_por_id(cliente_id)
            if not cliente:
                flash("Cliente no encontrado")
                return redirect(url_for("ventas.ventas"))
            
            vendedor = session["usuario"]["nombre"]
            
            # Procesar todos los productos y actualizar stock
            productos_factura = []
            total_factura = 0
            
            for item in carrito:
                producto_id = item["id"]
                cantidad = int(item["cantidad"])
                
                # Validar producto y stock
                try:
                    prod = productos_collection.get(str(producto_id))
                except Exception:
                    prod = None
                
                if not prod:
                    flash(f"Producto {item['nombre']} no encontrado")
                    continue
                
                stk = obtener_stock(producto_id)
                
                if not stk or stk.get("cantidad", 0) < cantidad:
                    flash(f"Stock insuficiente para {item['nombre']}")
                    continue
                
                precio = float(prod.get("precio", 0))
                subtotal = precio * cantidad
                total_factura += subtotal
                
                # Actualizar stock usando AQL
                aql = """
                FOR s IN stock
                    FILTER s.producto_id == @producto_id
                    UPDATE s WITH {cantidad: s.cantidad - @cantidad} IN stock
                """
                db.aql.execute(aql, bind_vars={
                    "producto_id": str(producto_id),
                    "cantidad": int(cantidad)
                })
                
                # Agregar producto a la lista de la factura
                productos_factura.append({
                    "id": str(producto_id),
                    "nombre": prod.get("nombre", ""),
                    "precio": precio,
                    "cantidad": cantidad,
                    "subtotal": subtotal
                })
            
            if len(productos_factura) == 0:
                flash("No se pudo procesar ningún producto")
                return redirect(url_for("ventas.ventas"))
            
            # Crear UNA SOLA venta con todos los productos
            venta_doc = {
                "cliente_id": str(cliente.get("_key")),
                "productos": productos_factura,
                "total": total_factura,
                "fecha": datetime.utcnow(),
                "vendedor": str(vendedor)
            }
            venta_res = ventas_collection.insert(venta_doc)
            venta_id = venta_res["_key"]
            
            # Crear UNA SOLA factura con todos los productos
            factura_doc = {
                "venta_id": venta_id,
                "cliente": cliente.get("nombre", ""),
                "cliente_email": cliente.get("email", ""),
                "productos": productos_factura,
                "total": total_factura,
                "fecha": datetime.utcnow(),
                "vendedor": str(vendedor)
            }
            factura_res = facturas_collection.insert(factura_doc)
            
            # Generar PDF con todos los productos y guardarlo como base64
            factura = obtener_factura(str(venta_id))
            if factura:
                pdf_bytes = generar_pdf_factura_mejorada(factura)
                pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                
                # Actualizar factura con PDF en base64
                factura_actualizada = facturas_collection.get(factura["_key"])
                facturas_collection.update({
                    **factura_actualizada,
                    "pdf_data": pdf_base64
                })
            
            flash(f"✅ Venta procesada exitosamente: {len(productos_factura)} producto(s) vendido(s)")
            return redirect(url_for("ventas.ver_factura", venta_id=venta_id))
                
        except Exception as e:
            print(f"❌ Error procesando venta: {e}")
            import traceback
            traceback.print_exc()
            flash("Ocurrió un error al procesar la venta")
            return redirect(url_for("ventas.ventas"))
    
    # GET: mostrar formulario
    productos_list = listar_productos()
    clientes = listar_clientes()
    return render_template("ventas.html", productos=productos_list, clientes=clientes)



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



# 📌 Descargar factura en PDF (desde base64)
@ventas_bp.route("/ventas/factura/<venta_id>/pdf")
def descargar_factura_pdf(venta_id):
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    factura = obtener_factura(venta_id)
    if not factura or "pdf_data" not in factura:
        flash("PDF no disponible para esta factura")
        return redirect(url_for("ventas.ver_factura", venta_id=venta_id))

    # Decodificar base64 a bytes
    pdf_bytes = base64.b64decode(factura["pdf_data"])
    
    return send_file(
        BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=f"factura_{venta_id}.pdf",
        mimetype="application/pdf"
    )



# 📌 Listar todas las facturas
@ventas_bp.route("/ventas/facturas")
def listar_facturas_view():
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    facturas_list = listar_facturas()
    return render_template("facturas.html", facturas=facturas_list)



# 📌 Mostrar stock actual
@ventas_bp.route("/ventas/stock")
def ver_stock():
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    productos_list = listar_productos()
    return render_template("stock.html", productos=productos_list)



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
