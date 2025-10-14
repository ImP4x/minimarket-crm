from datetime import datetime
from config import db
import unicodedata


# Obtener o crear colecciones
def get_collection(name):
    """Helper para obtener o crear una colección"""
    if db.has_collection(name):
        return db.collection(name)
    else:
        return db.create_collection(name)


contratos = get_collection("contratos")
empleados = get_collection("empleados")
counters = get_collection("counters")


def remover_acentos(texto):
    """Remueve tildes y acentos de un texto para búsqueda insensible"""
    if not texto:
        return ""
    texto_normalizado = unicodedata.normalize('NFD', str(texto))
    texto_sin_acentos = ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
    return texto_sin_acentos


def obtener_siguiente_id(nombre_secuencia="contrato"):
    """Obtiene el siguiente ID secuencial para contratos"""
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


def crear_contrato(empleado_id, tipo_contrato, fecha_inicio, fecha_fin, 
                   salario, cargo, observaciones=""):
    """Crea un nuevo contrato"""
    id_contrato = obtener_siguiente_id("contrato")
    
    doc = {
        "id_contrato": id_contrato,
        "empleado_id": str(empleado_id).strip(),
        "tipo_contrato": str(tipo_contrato).strip(),
        "fecha_inicio": str(fecha_inicio).strip(),
        "fecha_fin": str(fecha_fin).strip() if fecha_fin else None,
        "salario": float(salario),
        "cargo": str(cargo).strip(),
        "observaciones": str(observaciones).strip(),
        "fecha_registro": datetime.utcnow().isoformat()
    }
    
    try:
        res = contratos.insert(doc)
        return res["_key"]
    except Exception as e:
        print(f"❌ Error crear_contrato: {e}")
        return None


def listar_contratos(busqueda=None):
    """Lista todos los contratos con información del empleado"""
    if busqueda:
        # Remover acentos de la búsqueda
        busqueda_sin_acentos = remover_acentos(busqueda).lower()
        
        # Obtener todos los contratos con empleados
        aql = """
        FOR contrato IN contratos
            LET empleado = FIRST(
                FOR e IN empleados
                    FILTER e._key == contrato.empleado_id
                    RETURN e
            )
            SORT contrato.fecha_registro DESC
            RETURN MERGE(contrato, {
                empleado_nombre: empleado ? CONCAT(empleado.nombre, " ", empleado.apellido) : "Empleado no encontrado",
                empleado_documento: empleado ? empleado.nro_documento : "N/A",
                empleado_nombre_completo: empleado ? empleado.nombre : "",
                empleado_apellido_completo: empleado ? empleado.apellido : ""
            })
        """
        cursor = db.aql.execute(aql)
        todos_contratos = list(cursor)
        
        # Filtrar en Python con búsqueda insensible a acentos
        resultados = []
        for contrato in todos_contratos:
            # Remover acentos de los campos a buscar
            nombre = remover_acentos(contrato.get('empleado_nombre_completo', '')).lower()
            apellido = remover_acentos(contrato.get('empleado_apellido_completo', '')).lower()
            documento = remover_acentos(contrato.get('empleado_documento', '')).lower()
            tipo_contrato = remover_acentos(contrato.get('tipo_contrato', '')).lower()
            cargo = remover_acentos(contrato.get('cargo', '')).lower()
            
            # Buscar en todos los campos
            if (busqueda_sin_acentos in nombre or 
                busqueda_sin_acentos in apellido or 
                busqueda_sin_acentos in documento or
                busqueda_sin_acentos in tipo_contrato or
                busqueda_sin_acentos in cargo):
                resultados.append(contrato)
        
        return resultados
    else:
        aql = """
        FOR contrato IN contratos
            LET empleado = FIRST(
                FOR e IN empleados
                    FILTER e._key == contrato.empleado_id
                    RETURN e
            )
            SORT contrato.fecha_registro DESC
            RETURN MERGE(contrato, {
                empleado_nombre: empleado ? CONCAT(empleado.nombre, " ", empleado.apellido) : "Empleado no encontrado",
                empleado_documento: empleado ? empleado.nro_documento : "N/A"
            })
        """
        cursor = db.aql.execute(aql)
        return list(cursor)


def obtener_contrato_por_id(contrato_id):
    """Obtiene un contrato por su _key"""
    try:
        return contratos.get(str(contrato_id))
    except Exception:
        return None


def actualizar_contrato(contrato_id, tipo_contrato=None, fecha_inicio=None,
                       fecha_fin=None, salario=None, cargo=None, observaciones=None):
    """Actualiza los datos de un contrato"""
    try:
        contrato = contratos.get(str(contrato_id))
        if not contrato:
            return {"matched_count": 0, "modified_count": 0}
        
        cambios = {}
        if tipo_contrato is not None: cambios["tipo_contrato"] = str(tipo_contrato).strip()
        if fecha_inicio is not None: cambios["fecha_inicio"] = str(fecha_inicio).strip()
        if fecha_fin is not None: cambios["fecha_fin"] = str(fecha_fin).strip() if fecha_fin else None
        if salario is not None: cambios["salario"] = float(salario)
        if cargo is not None: cambios["cargo"] = str(cargo).strip()
        if observaciones is not None: cambios["observaciones"] = str(observaciones).strip()
        
        if cambios:
            contratos.update({**contrato, **cambios})
            return {"matched_count": 1, "modified_count": 1}
        return {"matched_count": 1, "modified_count": 0}
    except Exception as e:
        print(f"❌ Error actualizar_contrato: {e}")
        return {"matched_count": 0, "modified_count": 0}


def eliminar_contrato(contrato_id):
    """Elimina un contrato por su _key"""
    try:
        contratos.delete(str(contrato_id))
        return {"deleted_count": 1}
    except Exception as e:
        print(f"❌ Error eliminar_contrato: {e}")
        return {"deleted_count": 0}
