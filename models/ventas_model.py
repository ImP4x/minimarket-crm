from datetime import datetime
from config import db


# Obtener o crear colecciones
def get_collection(name):
    """Helper para obtener o crear una colección"""
    if db.has_collection(name):
        return db.collection(name)
    else:
        return db.create_collection(name)


# Colecciones
productos = get_collection("productos")
stock = get_collection("stock")
ventas = get_collection("ventas")
facturas = get_collection("historial_facturas")


# -----------------------
# Productos / Stock
# -----------------------
def listar_productos():
    """
    Devuelve una lista de productos. Cada producto trae además el campo 'stock'
    con la cantidad disponible (0 si no existe registro de stock).
    """
    aql = """
    FOR producto IN productos
        LET stock_info = FIRST(
            FOR s IN stock
                FILTER s.producto_id == producto._key
                RETURN s
        )
        RETURN MERGE(producto, {stock: stock_info ? stock_info.cantidad : 0})
    """
    cursor = db.aql.execute(aql)
    return list(cursor)


def registrar_producto(nombre, precio, cantidad_inicial=0):
    """
    Crea un producto y su registro de stock inicial.
    Devuelve el id (string) del producto creado.
    """
    doc = {
        "nombre": str(nombre).strip(),
        "precio": float(precio)
    }
    res = productos.insert(doc)
    prod_id = res["_key"]
    stock.insert({"producto_id": prod_id, "cantidad": int(cantidad_inicial)})
    return str(prod_id)


def obtener_producto(producto_id):
    """Devuelve el documento del producto (o None). Acepta str."""
    try:
        return productos.get(str(producto_id))
    except Exception:
        return None


def obtener_stock(producto_id):
    """Devuelve el documento de stock para un producto (o None)."""
    try:
        aql = """
        FOR s IN stock
            FILTER s.producto_id == @producto_id
            LIMIT 1
            RETURN s
        """
        cursor = db.aql.execute(aql, bind_vars={"producto_id": str(producto_id)})
        resultado = list(cursor)
        return resultado[0] if resultado else None
    except Exception:
        return None


def actualizar_stock(producto_id, delta):
    """
    Incrementa o decrementa el stock (delta puede ser negativo).
    Devuelve dict con matched_count y modified_count.
    """
    try:
        aql = """
        FOR s IN stock
            FILTER s.producto_id == @producto_id
            UPDATE s WITH {cantidad: s.cantidad + @delta} IN stock
            RETURN NEW
        """
        cursor = db.aql.execute(aql, bind_vars={
            "producto_id": str(producto_id),
            "delta": int(delta)
        })
        resultado = list(cursor)
        
        if resultado:
            return {"matched_count": 1, "modified_count": 1}
        return {"matched_count": 0, "modified_count": 0}
    except Exception as e:
        print("❌ actualizar_stock error:", e)
        return {"matched_count": 0, "modified_count": 0}


# -----------------------
# Ventas / Facturación
# -----------------------
def registrar_venta(cliente, producto_id, cantidad, vendedor=None):
    """
    Registra una venta:
      - valida existencia de producto y stock
      - inserta documento en 'ventas'
      - decrementa el stock
      - crea un documento en 'historial_facturas'
    """
    # validaciones mínimas
    if not cliente or not isinstance(cantidad, int) or cantidad <= 0:
        return None, "Datos de venta inválidos."

    try:
        prod = productos.get(str(producto_id))
    except Exception:
        prod = None

    stk = obtener_stock(producto_id)

    if not prod:
        return None, "Producto inexistente."
    if not stk or stk.get("cantidad", 0) < cantidad:
        return None, "Stock insuficiente."

    total = float(prod.get("precio", 0)) * int(cantidad)

    # 1) insertar venta
    venta_doc = {
        "cliente_id": str(cliente.get("_key")),
        "producto_id": str(producto_id),
        "cantidad": int(cantidad),
        "total": total,
        "fecha": datetime.utcnow(),
        "vendedor": str(vendedor) if vendedor else None
    }
    venta_res = ventas.insert(venta_doc)
    venta_id = venta_res["_key"]

    # 2) actualizar stock (-cantidad)
    actualizar_stock(producto_id, -int(cantidad))

    # 3) crear factura en historial_facturas
    factura_doc = {
        "venta_id": venta_id,
        "cliente": cliente.get("nombre", "") if isinstance(cliente, dict) else "",
        "cliente_email": cliente.get("email", "") if isinstance(cliente, dict) else "",
        "producto": prod.get("nombre", ""),
        "cantidad": int(cantidad),
        "total": total,
        "fecha": datetime.utcnow(),
        "vendedor": str(vendedor) if vendedor else None
    }
    facturas.insert(factura_doc)

    return str(venta_id), None


def obtener_factura(venta_id):
    """
    Busca en 'historial_facturas' el documento que tenga venta_id = venta_id.
    Devuelve el documento o None.
    """
    try:
        aql = """
        FOR factura IN historial_facturas
            FILTER factura.venta_id == @venta_id
            LIMIT 1
            RETURN factura
        """
        cursor = db.aql.execute(aql, bind_vars={"venta_id": str(venta_id)})
        resultado = list(cursor)
        return resultado[0] if resultado else None
    except Exception:
        return None


def listar_facturas():
    """
    Devuelve todas las facturas ordenadas por fecha descendente.
    """
    aql = """
    FOR factura IN historial_facturas
        SORT factura.fecha DESC
        RETURN factura
    """
    cursor = db.aql.execute(aql)
    return list(cursor)


# -----------------------
# NUEVO: Reportes de Ventas
# -----------------------
def obtener_ventas_por_periodo(fecha_inicio, fecha_fin):
    """
    Obtiene estadísticas de ventas por periodo específico.
    Retorna un diccionario con total de ventas, cantidad de transacciones, etc.
    """
    try:
        aql = """
        FOR venta IN ventas
            FILTER venta.fecha >= @fecha_inicio AND venta.fecha <= @fecha_fin
            COLLECT AGGREGATE 
                total_ventas = SUM(venta.total),
                cantidad_transacciones = COUNT(1),
                promedio_venta = AVG(venta.total)
            RETURN {
                total_ventas: total_ventas,
                cantidad_transacciones: cantidad_transacciones,
                promedio_venta: promedio_venta
            }
        """
        cursor = db.aql.execute(aql, bind_vars={
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin
        })
        resultado = list(cursor)
        
        if resultado:
            stats = resultado[0]
            return {
                "total_ventas": round(stats.get("total_ventas", 0) or 0, 2),
                "cantidad_transacciones": stats.get("cantidad_transacciones", 0) or 0,
                "promedio_venta": round(stats.get("promedio_venta", 0) or 0, 2)
            }
        else:
            return {
                "total_ventas": 0.0,
                "cantidad_transacciones": 0,
                "promedio_venta": 0.0
            }
    except Exception as e:
        print(f"❌ Error obtener_ventas_por_periodo: {e}")
        return {
            "total_ventas": 0.0,
            "cantidad_transacciones": 0,
            "promedio_venta": 0.0
        }


def obtener_ventas_detalladas_por_periodo(fecha_inicio, fecha_fin):
    """
    Obtiene lista detallada de ventas por periodo con información de cliente y producto.
    """
    try:
        aql = """
        FOR venta IN ventas
            FILTER venta.fecha >= @fecha_inicio AND venta.fecha <= @fecha_fin
            LET cliente = FIRST(
                FOR c IN clientes
                    FILTER c._key == venta.cliente_id
                    RETURN c
            )
            LET producto = FIRST(
                FOR p IN productos
                    FILTER p._key == venta.producto_id
                    RETURN p
            )
            SORT venta.fecha DESC
            RETURN {
                _id: venta._key,
                fecha: venta.fecha,
                cliente_nombre: cliente ? cliente.nombre : "Cliente no encontrado",
                producto_nombre: producto ? producto.nombre : "Producto no encontrado",
                cantidad: venta.cantidad,
                total: venta.total,
                vendedor: venta.vendedor ? venta.vendedor : "N/A"
            }
        """
        cursor = db.aql.execute(aql, bind_vars={
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin
        })
        
        return list(cursor)
    except Exception as e:
        print(f"❌ Error obtener_ventas_detalladas_por_periodo: {e}")
        return []


# -----------------------
# Utilidades / Depuración
# -----------------------
def contar_stock_total():
    """Ejemplo: suma total de stock (helper)."""
    aql = """
    FOR s IN stock
        COLLECT AGGREGATE total = SUM(s.cantidad)
        RETURN total
    """
    cursor = db.aql.execute(aql)
    resultado = list(cursor)
    return resultado[0] if resultado else 0
