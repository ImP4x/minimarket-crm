from datetime import datetime
from pymongo import ReturnDocument
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from config import db
import re

usuarios = db["usuarios"]
counters = db["counters"]

def obtener_siguiente_id(nombre_secuencia):
    secuencia = counters.find_one_and_update(
        {"_id": nombre_secuencia},
        {"$inc": {"valor": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return secuencia["valor"]

def listar_usuarios():
    cursor = usuarios.find().sort("fecha_registro", -1)
    return list(cursor)

def buscar_por_email(email):
    if not email:
        return None
    return usuarios.find_one({"email": email.strip().lower()})

def verificar_usuario(email, password):
    user = buscar_por_email(email)
    if not user:
        return None
    stored_hash = user.get("password")
    if not stored_hash:
        return None
    try:
        if check_password_hash(stored_hash, password.strip()):
            return user
    except Exception:
        return None
    return None

def crear_usuario(nombre, email, password, rol="none", estado="inactivo"):
    nuevo_id = obtener_siguiente_id("usuarios")  # id autoincrementable
    doc = {
        "id_usuario": nuevo_id,  # nuevo campo id incremental
        "nombre": nombre.strip(),
        "email": email.strip().lower(),
        "password": generate_password_hash(password.strip()),
        "rol": rol,
        "estado": estado,
        "fecha_registro": datetime.utcnow()
    }
    return usuarios.insert_one(doc)

def actualizar_usuario(user_id, nombre=None, email=None, rol=None,
                      estado=None, nueva_password=None):
    cambios = {}
    if nombre is not None:
        cambios["nombre"] = nombre.strip()
    if email is not None:
        cambios["email"] = email.strip().lower()
    if rol is not None:
        cambios["rol"] = rol
    if estado is not None:
        cambios["estado"] = estado
    if nueva_password is not None and nueva_password.strip():
        hashed = generate_password_hash(nueva_password.strip())
        cambios["password"] = hashed

    if not cambios:
        return {"matched_count": 0, "modified_count": 0}

    try:
        res = usuarios.update_one(
            {"_id": ObjectId(str(user_id))},
            {"$set": cambios}
        )
        return {"matched_count": res.matched_count, "modified_count": res.modified_count}
    except Exception as e:
        print("❌ actualizar_usuario error:", e)
        return {"matched_count": 0, "modified_count": 0}

def actualizar_password_by_email(email, nueva_password):
    if not email:
        return {"matched_count": 0, "modified_count": 0}
    hashed_pw = generate_password_hash(nueva_password.strip())
    result = usuarios.update_one(
        {"email": {"$regex": f"^{re.escape(email.strip())}$", "$options": "i"}},
        {"$set": {"password": hashed_pw}}
    )
    return {"matched_count": result.matched_count, "modified_count": result.modified_count}

def eliminar_usuario(user_id):
    try:
        res = usuarios.delete_one({"_id": ObjectId(str(user_id))})
        return {"deleted_count": res.deleted_count}
    except Exception as e:
        print("❌ eliminar_usuario error:", e)
        return {"deleted_count": 0}