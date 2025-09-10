from datetime import datetime
from bson.objectid import ObjectId
from config import db
import re

clientes = db["clientes"]
counters = db["counters"]

def obtener_siguiente_id(nombre_secuencia):
    secuencia = counters.find_one_and_update(
        {"_id": nombre_secuencia},
        {"$inc": {"valor": 1}},
        upsert=True,
        return_document=True
    )
    return secuencia["valor"]

def crear_cliente(nombre, email, telefono, direccion, ciudad, pais):
    email_norm = email.strip().lower() if email else ""
    nuevo_id = obtener_siguiente_id("clientes")  # id autoincrementable

    cliente = {
        "id_cliente": nuevo_id,  # nuevo campo id incremental
        "nombre": nombre.strip(),
        "email": email_norm,
        "telefono": telefono.strip() if telefono else "",
        "direccion": direccion.strip() if direccion else "",
        "ciudad": ciudad.strip() if ciudad else "",
        "pais": pais.strip() if pais else "",
        "fecha_registro": datetime.utcnow()
    }
    return clientes.insert_one(cliente)

def listar_clientes(filtro_q=None):
    query = {}
    if filtro_q:
        q = re.escape(filtro_q.strip())
        query = {"$or": [
            {"nombre": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
            {"ciudad": {"$regex": q, "$options": "i"}},
            {"pais": {"$regex": q, "$options": "i"}}
        ]}
    cursor = clientes.find(query).sort("fecha_registro", -1)
    return list(cursor)

def buscar_cliente_por_id(client_id):
    try:
        return clientes.find_one({"_id": ObjectId(str(client_id))})
    except Exception as e:
        print("❌ buscar_cliente_por_id error:", e)
        return None

def obtener_cliente_por_id(client_id):
    return buscar_cliente_por_id(client_id)

def actualizar_cliente(client_id, nombre=None, email=None, telefono=None,
                      direccion=None, ciudad=None, pais=None):
    cambios = {}
    if nombre is not None:
        cambios["nombre"] = nombre.strip()
    if email is not None:
        cambios["email"] = email.strip().lower()
    if telefono is not None:
        cambios["telefono"] = telefono.strip()
    if direccion is not None:
        cambios["direccion"] = direccion.strip()
    if ciudad is not None:
        cambios["ciudad"] = ciudad.strip()
    if pais is not None:
        cambios["pais"] = pais.strip()

    if not cambios:
        return {"matched_count": 0, "modified_count": 0}

    try:
        res = clientes.update_one({"_id": ObjectId(str(client_id))}, {"$set": cambios})
        return {"matched_count": res.matched_count, "modified_count": res.modified_count}
    except Exception as e:
        print("❌ actualizar_cliente error:", e)
        return {"matched_count": 0, "modified_count": 0}

def eliminar_cliente(client_id):
    try:
        res = clientes.delete_one({"_id": ObjectId(str(client_id))})
        return {"deleted_count": res.deleted_count}
    except Exception as e:
        print("❌ eliminar_cliente error:", e)
        return {"deleted_count": 0}

def reporte_por_pais():
    pipeline = [
        {"$group": {"_id": "$pais", "total": {"$sum": 1}}},
        {"$sort": {"total": -1}}
    ]
    return list(clientes.aggregate(pipeline))