from datetime import datetime
from config import db
import re


# Obtener o crear colecciones
def get_collection(name):
    """Helper para obtener o crear una colección"""
    if db.has_collection(name):
        return db.collection(name)
    else:
        return db.create_collection(name)


clientes = get_collection("clientes")
counters = get_collection("counters")


def obtener_siguiente_id(nombre_secuencia):
    """Obtiene el siguiente ID autoincrementable para una secuencia"""
    try:
        # Intentar obtener el contador existente
        counter_doc = counters.get(nombre_secuencia)
        nuevo_valor = counter_doc["valor"] + 1
        counters.update({"_key": nombre_secuencia, "valor": nuevo_valor})
        return nuevo_valor
    except:
        # Si no existe, crearlo
        counters.insert({"_key": nombre_secuencia, "valor": 1})
        return 1


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
    return clientes.insert(cliente)


def listar_clientes(filtro_q=None):
    if filtro_q:
        q = filtro_q.strip().lower()
        # Usar AQL para búsqueda con filtros
        aql = """
        FOR cliente IN clientes
            FILTER LOWER(cliente.nombre) LIKE @q OR
                   LOWER(cliente.email) LIKE @q OR
                   LOWER(cliente.ciudad) LIKE @q OR
                   LOWER(cliente.pais) LIKE @q
            SORT cliente.fecha_registro DESC
            RETURN cliente
        """
        cursor = db.aql.execute(aql, bind_vars={"q": f"%{q}%"})
        return list(cursor)
    else:
        # Sin filtro, obtener todos
        aql = """
        FOR cliente IN clientes
            SORT cliente.fecha_registro DESC
            RETURN cliente
        """
        cursor = db.aql.execute(aql)
        return list(cursor)


def buscar_cliente_por_id(client_id):
    try:
        return clientes.get(str(client_id))
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
        cliente = clientes.get(str(client_id))
        if cliente:
            clientes.update({**cliente, **cambios})
            return {"matched_count": 1, "modified_count": 1}
        return {"matched_count": 0, "modified_count": 0}
    except Exception as e:
        print("❌ actualizar_cliente error:", e)
        return {"matched_count": 0, "modified_count": 0}


def eliminar_cliente(client_id):
    try:
        clientes.delete(str(client_id))
        return {"deleted_count": 1}
    except Exception as e:
        print("❌ eliminar_cliente error:", e)
        return {"deleted_count": 0}


def reporte_por_pais():
    aql = """
    FOR cliente IN clientes
        COLLECT pais = cliente.pais WITH COUNT INTO total
        SORT total DESC
        RETURN {_id: pais, total: total}
    """
    cursor = db.aql.execute(aql)
    return list(cursor)