from datetime import datetime
from bson.objectid import ObjectId
from config import db

productos = db["productos"]
stock = db["stock"]

def crear_producto(nombre, precio, categoria="", cantidad_inicial=0):
    """Crea un producto con registro en stock."""
    doc = {
        "nombre": nombre.strip(),
        "precio": float(precio),
        "categoria": categoria.strip(),
        "fecha_registro": datetime.utcnow()
    }
    res = productos.insert_one(doc)
    producto_id = res.inserted_id

    stock.insert_one({
        "producto_id": producto_id,
        "cantidad": int(cantidad_inicial),
        "ultima_actualizacion": datetime.utcnow()
    })
    return res

def listar_productos():
    """Lista todos los productos con su stock actual."""
    pipeline = [
        {"$lookup": {
            "from": "stock",
            "localField": "_id",
            "foreignField": "producto_id",
            "as": "stock_info"
        }},
        {"$unwind": {"path": "$stock_info", "preserveNullAndEmptyArrays": True}},
        {"$sort": {"fecha_registro": -1}}
    ]
    return list(productos.aggregate(pipeline))

def actualizar_producto(producto_id, nombre=None, precio=None, categoria=None, cantidad=None):
    """Actualiza datos del producto y stock si corresponde."""
    cambios = {}
    if nombre: cambios["nombre"] = nombre.strip()
    if precio: cambios["precio"] = float(precio)
    if categoria is not None: cambios["categoria"] = categoria.strip()

    if cambios:
        productos.update_one({"_id": ObjectId(str(producto_id))}, {"$set": cambios})

    if cantidad is not None:
        stock.update_one(
            {"producto_id": ObjectId(str(producto_id))},
            {"$set": {"cantidad": int(cantidad), "ultima_actualizacion": datetime.utcnow()}},
            upsert=True
        )

def eliminar_producto(producto_id):
    """Elimina producto y su stock asociado."""
    productos.delete_one({"_id": ObjectId(str(producto_id))})
    stock.delete_one({"producto_id": ObjectId(str(producto_id))})