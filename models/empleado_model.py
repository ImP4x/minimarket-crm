from datetime import datetime
from config import db

# Obtener o crear colecciones
def get_collection(name):
    """Helper para obtener o crear una colección"""
    if db.has_collection(name):
        return db.collection(name)
    else:
        return db.create_collection(name)

empleados = get_collection("empleados")
counters = get_collection("counters")

def obtener_siguiente_id(nombre_secuencia="empleado"):
    """Obtiene el siguiente ID secuencial para empleados"""
    try:
        aql = """
        UPSERT { _key: @nombre }
        INSERT { _key: @nombre, valor: 1 }
        UPDATE { valor: OLD.valor + 1 }
        IN counters
        RETURN NEW.valor
        """
        cursor = db.aql.execute(aql, bind_vars={"nombre": nombre_secuencia})
        resultado = list(cursor)
        return resultado[0] if resultado else 1
    except Exception as e:
        print(f"❌ Error obtener_siguiente_id: {e}")
        return 1

def crear_empleado(nro_documento, nombre, apellido, edad, genero, cargo, 
                   correo, nro_contacto, estado="activo", observaciones=""):
    """Crea un nuevo empleado con ID autoincremental"""
    id_empleado = obtener_siguiente_id("empleado")
    
    doc = {
        "id_empleado": id_empleado,
        "nro_documento": str(nro_documento).strip(),
        "nombre": str(nombre).strip(),
        "apellido": str(apellido).strip(),
        "edad": int(edad),
        "genero": str(genero).strip(),
        "cargo": str(cargo).strip(),
        "correo": str(correo).strip(),
        "nro_contacto": str(nro_contacto).strip(),
        "estado": str(estado).strip(),
        "observaciones": str(observaciones).strip(),
        "fecha_registro": datetime.utcnow().isoformat()
    }
    
    try:
        res = empleados.insert(doc)
        return res["_key"]
    except Exception as e:
        print(f"❌ Error crear_empleado: {e}")
        return None

def listar_empleados(busqueda=None):
    """Lista todos los empleados, con búsqueda opcional por nombre/apellido/documento"""
    if busqueda:
        aql = """
        FOR empleado IN empleados
            FILTER LOWER(empleado.nombre) LIKE LOWER(@busqueda)
                OR LOWER(empleado.apellido) LIKE LOWER(@busqueda)
                OR LOWER(empleado.nro_documento) LIKE LOWER(@busqueda)
            SORT empleado.fecha_registro DESC
            RETURN empleado
        """
        cursor = db.aql.execute(aql, bind_vars={"busqueda": f"%{busqueda}%"})
    else:
        aql = """
        FOR empleado IN empleados
            SORT empleado.fecha_registro DESC
            RETURN empleado
        """
        cursor = db.aql.execute(aql)
    
    return list(cursor)

def obtener_empleado_por_id(empleado_id):
    """Obtiene un empleado por su _key"""
    try:
        return empleados.get(str(empleado_id))
    except Exception:
        return None

def obtener_empleado_por_documento(nro_documento):
    """Obtiene un empleado por su número de documento"""
    try:
        aql = """
        FOR empleado IN empleados
            FILTER empleado.nro_documento == @nro_documento
            LIMIT 1
            RETURN empleado
        """
        cursor = db.aql.execute(aql, bind_vars={"nro_documento": str(nro_documento)})
        resultado = list(cursor)
        return resultado[0] if resultado else None
    except Exception:
        return None

def actualizar_empleado(empleado_id, nro_documento=None, nombre=None, apellido=None,
                       edad=None, genero=None, cargo=None, correo=None, 
                       nro_contacto=None, estado=None, observaciones=None):
    """Actualiza los datos de un empleado"""
    try:
        empleado = empleados.get(str(empleado_id))
        if not empleado:
            return {"matched_count": 0, "modified_count": 0}
        
        cambios = {}
        if nro_documento is not None: cambios["nro_documento"] = str(nro_documento).strip()
        if nombre is not None: cambios["nombre"] = str(nombre).strip()
        if apellido is not None: cambios["apellido"] = str(apellido).strip()
        if edad is not None: cambios["edad"] = int(edad)
        if genero is not None: cambios["genero"] = str(genero).strip()
        if cargo is not None: cambios["cargo"] = str(cargo).strip()
        if correo is not None: cambios["correo"] = str(correo).strip()
        if nro_contacto is not None: cambios["nro_contacto"] = str(nro_contacto).strip()
        if estado is not None: cambios["estado"] = str(estado).strip()
        if observaciones is not None: cambios["observaciones"] = str(observaciones).strip()
        
        if cambios:
            empleados.update({**empleado, **cambios})
            return {"matched_count": 1, "modified_count": 1}
        return {"matched_count": 1, "modified_count": 0}
    except Exception as e:
        print(f"❌ Error actualizar_empleado: {e}")
        return {"matched_count": 0, "modified_count": 0}

def eliminar_empleado(empleado_id):
    """Elimina un empleado por su _key"""
    try:
        empleados.delete(str(empleado_id))
        return {"deleted_count": 1}
    except Exception as e:
        print(f"❌ Error eliminar_empleado: {e}")
        return {"deleted_count": 0}
