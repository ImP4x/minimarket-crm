from datetime import datetime
from config import db


# Obtener o crear colecciones
def get_collection(name):
    """Helper para obtener o crear una colección"""
    if db.has_collection(name):
        return db.collection(name)
    else:
        return db.create_collection(name)


productos = get_collection("productos")
stock = get_collection("stock")


def crear_producto(nombre, precio, categoria="", cantidad_inicial=0):
    """Crea un producto con registro en stock."""
    doc = {
        "nombre": nombre.strip(),
        "precio": float(precio),
        "categoria": categoria.strip(),
        "fecha_registro": datetime.utcnow().isoformat()  # ✅ CAMBIO: guardar como string ISO
    }
    res = productos.insert(doc)
    producto_id = res["_key"]

    stock.insert({
        "producto_id": producto_id,
        "cantidad": int(cantidad_inicial),
        "ultima_actualizacion": datetime.utcnow().isoformat()  # ✅ CAMBIO: guardar como string ISO
    })
    
    # Retornar objeto similar a MongoDB para mantener compatibilidad
    class InsertResult:
        def __init__(self, key):
            self.inserted_id = key
    
    return InsertResult(producto_id)


def listar_productos():
    """Lista todos los productos con su stock actual."""
    aql = """
    FOR producto IN productos
        LET stock_info = FIRST(
            FOR s IN stock
                FILTER s.producto_id == producto._key
                RETURN s
        )
        SORT producto.fecha_registro DESC
        RETURN MERGE(producto, {
            stock_info: stock_info,
            stock: stock_info ? stock_info.cantidad : 0
        })
    """
    cursor = db.aql.execute(aql)
    return list(cursor)


def actualizar_producto(producto_id, nombre=None, precio=None, categoria=None, cantidad=None):
    """Actualiza datos del producto y stock si corresponde."""
    cambios = {}
    if nombre: 
        cambios["nombre"] = nombre.strip()
    if precio: 
        cambios["precio"] = float(precio)
    if categoria is not None: 
        cambios["categoria"] = categoria.strip()

    if cambios:
        try:
            producto = productos.get(str(producto_id))
            if producto:
                productos.update({**producto, **cambios})
        except Exception as e:
            print("❌ Error actualizando producto:", e)

    if cantidad is not None:
        try:
            # Buscar stock existente
            aql = """
            FOR s IN stock
                FILTER s.producto_id == @producto_id
                RETURN s
            """
            cursor = db.aql.execute(aql, bind_vars={"producto_id": str(producto_id)})
            stock_existente = list(cursor)
            
            if stock_existente:
                # Actualizar stock existente
                stock_doc = stock_existente[0]
                stock.update({
                    **stock_doc,
                    "cantidad": int(cantidad),
                    "ultima_actualizacion": datetime.utcnow().isoformat()  # ✅ CAMBIO: guardar como string ISO
                })
            else:
                # Crear nuevo registro de stock
                stock.insert({
                    "producto_id": str(producto_id),
                    "cantidad": int(cantidad),
                    "ultima_actualizacion": datetime.utcnow().isoformat()  # ✅ CAMBIO: guardar como string ISO
                })
        except Exception as e:
            print("❌ Error actualizando stock:", e)


def eliminar_producto(producto_id):
    """Elimina producto y su stock asociado."""
    try:
        productos.delete(str(producto_id))
    except Exception as e:
        print("❌ Error eliminando producto:", e)
    
    try:
        # Eliminar todos los registros de stock asociados
        aql = """
        FOR s IN stock
            FILTER s.producto_id == @producto_id
            REMOVE s IN stock
        """
        db.aql.execute(aql, bind_vars={"producto_id": str(producto_id)})
    except Exception as e:
        print("❌ Error eliminando stock:", e)