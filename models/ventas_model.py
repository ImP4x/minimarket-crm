from bson.objectid import ObjectId
from datetime import datetime
from config import db

# Colecciones
productos = db["productos"]
stock = db["stock"]
ventas = db["ventas"]
facturas = db["historial_facturas"]

# -----------------------
# Productos / Stock
# -----------------------
def listar_productos():
    """
    Devuelve una lista de productos. Cada producto trae además el campo 'stock'
    con la cantidad disponible (0 si no existe registro de stock).
    """
    docs = list(productos.find())
    for p in docs:
        try:
            s = stock.find_one({"producto_id": p["_id"]})
            p["stock"] = s["cantidad"] if s and "cantidad" in s else 0
        except Exception:
            p["stock"] = 0
    return docs


def registrar_producto(nombre, precio, cantidad_inicial=0):
    """
    Crea un producto y su registro de stock inicial.
    Devuelve el id (string) del producto creado.
    """
    doc = {
        "nombre": str(nombre).strip(),
        "precio": float(precio)
    }
    res = productos.insert_one(doc)
    prod_id = res.inserted_id
    stock.insert_one({"producto_id": prod_id, "cantidad": int(cantidad_inicial)})
    return str(prod_id)


def obtener_producto(producto_id):
    """Devuelve el documento del producto (o None). Acepta str/ObjectId."""
    try:
        return productos.find_one({"_id": ObjectId(str(producto_id))})
    except Exception:
        return None


def obtener_stock(producto_id):
    """Devuelve el documento de stock para un producto (o None)."""
    try:
        return stock.find_one({"producto_id": ObjectId(str(producto_id))})
    except Exception:
        return None


def actualizar_stock(producto_id, delta):
    """
    Incrementa o decrementa el stock (delta puede ser negativo).
    Devuelve dict con matched_count y modified_count.
    """
    try:
        res = stock.update_one(
            {"producto_id": ObjectId(str(producto_id))},
            {"$inc": {"cantidad": int(delta)}}
        )
        return {"matched_count": res.matched_count, "modified_count": res.modified_count}
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
        prod = productos.find_one({"_id": ObjectId(str(producto_id))})
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
        "cliente_id": ObjectId(str(cliente["_id"])),
        "producto_id": ObjectId(str(producto_id)),
        "cantidad": int(cantidad),
        "total": total,
        "fecha": datetime.utcnow(),
        "vendedor": str(vendedor) if vendedor else None
    }
    venta_res = ventas.insert_one(venta_doc)
    venta_id = venta_res.inserted_id

    # 2) actualizar stock (-cantidad)
    stock.update_one(
        {"producto_id": ObjectId(str(producto_id))},
        {"$inc": {"cantidad": -int(cantidad)}}
    )

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
    facturas.insert_one(factura_doc)

    return str(venta_id), None


def obtener_factura(venta_id):
    """
    Busca en 'historial_facturas' el documento que tenga venta_id = ObjectId(venta_id).
    Devuelve el documento o None.
    """
    try:
        doc = facturas.find_one({"venta_id": ObjectId(str(venta_id))})
        return doc
    except Exception:
        return None


def listar_facturas():
    """
    Devuelve todas las facturas ordenadas por fecha descendente.
    """
    return list(facturas.find().sort("fecha", -1))


# -----------------------
# Utilidades / Depuración
# -----------------------
def contar_stock_total():
    """Ejemplo: suma total de stock (helper)."""
    cursor = stock.aggregate([{"$group": {"_id": None, "total": {"$sum": "$cantidad"}}}])
    res = list(cursor)
    return res[0]["total"] if res else 0