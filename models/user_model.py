from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import db
import re


# Obtener o crear colecciones
def get_collection(name):
    """Helper para obtener o crear una colección"""
    if db.has_collection(name):
        return db.collection(name)
    else:
        return db.create_collection(name)


usuarios = get_collection("usuarios")
counters = get_collection("counters")


def obtener_siguiente_id(nombre_secuencia):
    """Obtiene el siguiente ID autoincrementable para una secuencia"""
    try:
        counter_doc = counters.get(nombre_secuencia)
        nuevo_valor = counter_doc["valor"] + 1
        counters.update({"_key": nombre_secuencia, "valor": nuevo_valor})
        return nuevo_valor
    except:
        counters.insert({"_key": nombre_secuencia, "valor": 1})
        return 1


def listar_usuarios():
    aql = """
    FOR usuario IN usuarios
        SORT usuario.fecha_registro DESC
        RETURN usuario
    """
    cursor = db.aql.execute(aql)
    return list(cursor)


def buscar_por_email(email):
    if not email:
        return None
    aql = """
    FOR usuario IN usuarios
        FILTER LOWER(usuario.email) == LOWER(@email)
        LIMIT 1
        RETURN usuario
    """
    cursor = db.aql.execute(aql, bind_vars={"email": email.strip()})
    resultado = list(cursor)
    return resultado[0] if resultado else None


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
    return usuarios.insert(doc)


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
        usuario = usuarios.get(str(user_id))
        if usuario:
            usuarios.update({**usuario, **cambios})
            return {"matched_count": 1, "modified_count": 1}
        return {"matched_count": 0, "modified_count": 0}
    except Exception as e:
        print("❌ actualizar_usuario error:", e)
        return {"matched_count": 0, "modified_count": 0}


def actualizar_password_by_email(email, nueva_password):
    if not email:
        return {"matched_count": 0, "modified_count": 0}
    
    hashed_pw = generate_password_hash(nueva_password.strip())
    
    try:
        aql = """
        FOR usuario IN usuarios
            FILTER LOWER(usuario.email) == LOWER(@email)
            UPDATE usuario WITH {password: @password} IN usuarios
            RETURN NEW
        """
        cursor = db.aql.execute(aql, bind_vars={
            "email": email.strip(),
            "password": hashed_pw
        })
        resultado = list(cursor)
        
        if resultado:
            return {"matched_count": 1, "modified_count": 1}
        return {"matched_count": 0, "modified_count": 0}
    except Exception as e:
        print("❌ actualizar_password_by_email error:", e)
        return {"matched_count": 0, "modified_count": 0}


def eliminar_usuario(user_id):
    try:
        usuarios.delete(str(user_id))
        return {"deleted_count": 1}
    except Exception as e:
        print("❌ eliminar_usuario error:", e)
        return {"deleted_count": 0}
