from datetime import datetime
from config import db
import unicodedata
import base64
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors

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

def generar_pdf_contrato(contrato_data, empleado_data):
    """Genera el PDF del contrato según el tipo (Colombia)"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # 🎨 LOGO DE ECOMARKET
    try:
        logo_path = os.path.join('static', 'img', 'logo.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=1.5*inch, height=1.5*inch)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 0.2*inch))
    except Exception as e:
        print(f"⚠️ No se pudo cargar el logo: {e}")
    
    # Estilos personalizados
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#165d2a'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=10
    )
    
    tipo_contrato = contrato_data.get('tipo_contrato', '')
    
    # TÍTULO
    if tipo_contrato == 'Indefinido':
        titulo = "CONTRATO DE TRABAJO A TÉRMINO INDEFINIDO"
    elif tipo_contrato == 'Fijo':
        titulo = "CONTRATO DE TRABAJO A TÉRMINO FIJO"
    elif tipo_contrato == 'Obra o Labor':
        titulo = "CONTRATO DE TRABAJO POR OBRA O LABOR"
    elif tipo_contrato == 'Prestación de Servicios':
        titulo = "CONTRATO DE PRESTACIÓN DE SERVICIOS"
    elif tipo_contrato == 'Aprendizaje':
        titulo = "CONTRATO DE APRENDIZAJE"
    else:
        titulo = "CONTRATO DE TRABAJO"
    
    story.append(Paragraph(titulo, titulo_style))
    story.append(Spacer(1, 0.3*inch))
    
    # PARTES DEL CONTRATO
    partes_texto = f"""
    <b>Entre los suscritos a saber:</b> <b>ECOMARKET</b> (en adelante EL EMPLEADOR), 
    identificado con NIT 900.123.456-7, y <b>{empleado_data.get('nombre', '')} {empleado_data.get('apellido', '')}</b> 
    (en adelante EL TRABAJADOR), identificado con documento número <b>{empleado_data.get('nro_documento', '')}</b>, 
    se ha convenido celebrar el presente contrato de trabajo, el cual se regirá por las siguientes cláusulas:
    """
    story.append(Paragraph(partes_texto, body_style))
    story.append(Spacer(1, 0.2*inch))
    
    # CLÁUSULAS SEGÚN TIPO DE CONTRATO
    if tipo_contrato == 'Indefinido':
        clausulas = f"""
        <b>PRIMERA - OBJETO:</b> EL EMPLEADOR contrata los servicios de EL TRABAJADOR para desempeñar 
        el cargo de <b>{contrato_data.get('cargo', '')}</b>, comprometiéndose a realizar todas las 
        funciones inherentes al mismo.<br/><br/>
        
        <b>SEGUNDA - DURACIÓN:</b> El presente contrato es a <b>TÉRMINO INDEFINIDO</b>, iniciando 
        el día <b>{contrato_data.get('fecha_inicio', '')}</b>, y su terminación estará sujeta a las 
        causales legales establecidas en el Código Sustantivo del Trabajo.<br/><br/>
        
        <b>TERCERA - REMUNERACIÓN:</b> EL EMPLEADOR pagará a EL TRABAJADOR la suma de 
        <b>${contrato_data.get('salario', 0):,.0f} pesos colombianos</b> mensuales, pagaderos en dos 
        quincenas.<br/><br/>
        
        <b>CUARTA - JORNADA LABORAL:</b> La jornada ordinaria de trabajo será de 48 horas semanales, 
        distribuidas de lunes a sábado, con un día de descanso remunerado.<br/><br/>
        
        <b>QUINTA - PRESTACIONES SOCIALES:</b> EL TRABAJADOR tendrá derecho a todas las prestaciones 
        sociales de ley: cesantías, intereses sobre cesantías, prima de servicios, vacaciones, dotación, 
        y afiliación a seguridad social integral.<br/><br/>
        
        <b>SEXTA - OBLIGACIONES DEL TRABAJADOR:</b> Cumplir con las funciones asignadas, asistir 
        puntualmente, observar el reglamento interno de trabajo, y mantener reserva sobre la información 
        confidencial de la empresa.
        """
    
    elif tipo_contrato == 'Fijo':
        clausulas = f"""
        <b>PRIMERA - OBJETO:</b> EL EMPLEADOR contrata los servicios de EL TRABAJADOR para desempeñar 
        el cargo de <b>{contrato_data.get('cargo', '')}</b>.<br/><br/>
        
        <b>SEGUNDA - DURACIÓN:</b> El presente contrato es a <b>TÉRMINO FIJO</b>, con una duración de 
        desde el <b>{contrato_data.get('fecha_inicio', '')}</b> hasta el <b>{contrato_data.get('fecha_fin', '')}</b>. 
        Este contrato podrá prorrogarse por acuerdo entre las partes antes de su vencimiento.<br/><br/>
        
        <b>TERCERA - REMUNERACIÓN:</b> EL EMPLEADOR pagará a EL TRABAJADOR la suma de 
        <b>${contrato_data.get('salario', 0):,.0f} pesos colombianos</b> mensuales.<br/><br/>
        
        <b>CUARTA - JORNADA LABORAL:</b> La jornada ordinaria de trabajo será de 48 horas semanales.<br/><br/>
        
        <b>QUINTA - PRESTACIONES SOCIALES:</b> EL TRABAJADOR tendrá derecho a todas las prestaciones 
        sociales establecidas por ley.<br/><br/>
        
        <b>SEXTA - TERMINACIÓN:</b> Al vencimiento del plazo pactado, si no hay prórroga, el contrato 
        terminará automáticamente sin que se requiera aviso previo.
        """
    
    elif tipo_contrato == 'Obra o Labor':
        clausulas = f"""
        <b>PRIMERA - OBJETO:</b> EL EMPLEADOR contrata los servicios de EL TRABAJADOR para desempeñar 
        el cargo de <b>{contrato_data.get('cargo', '')}</b>, cuya labor consiste en: 
        <b>{contrato_data.get('observaciones', 'Obra específica según requerimientos')}</b>.<br/><br/>
        
        <b>SEGUNDA - DURACIÓN:</b> El presente contrato es por <b>OBRA O LABOR DETERMINADA</b>, 
        iniciando el <b>{contrato_data.get('fecha_inicio', '')}</b> y finalizando cuando se complete 
        la obra o labor contratada.<br/><br/>
        
        <b>TERCERA - REMUNERACIÓN:</b> Se pagará la suma de <b>${contrato_data.get('salario', 0):,.0f} 
        pesos colombianos</b> mensuales mientras dure la ejecución de la obra.<br/><br/>
        
        <b>CUARTA - PRESTACIONES SOCIALES:</b> EL TRABAJADOR tendrá derecho a todas las prestaciones 
        sociales de ley durante la vigencia del contrato.<br/><br/>
        
        <b>QUINTA - TERMINACIÓN:</b> El contrato terminará automáticamente al cumplirse el objeto 
        para el cual fue contratado.
        """
    
    elif tipo_contrato == 'Prestación de Servicios':
        clausulas = f"""
        <b>PRIMERA - OBJETO:</b> EL CONTRATANTE encarga al CONTRATISTA la prestación de servicios 
        profesionales como <b>{contrato_data.get('cargo', '')}</b>.<br/><br/>
        
        <b>SEGUNDA - DURACIÓN:</b> El presente contrato tendrá una duración desde el 
        <b>{contrato_data.get('fecha_inicio', '')}</b> hasta el <b>{contrato_data.get('fecha_fin', 'término de la labor')}</b>.<br/><br/>
        
        <b>TERCERA - VALOR:</b> El valor total del contrato es de <b>${contrato_data.get('salario', 0):,.0f} 
        pesos colombianos</b>, pagaderos según las entregas acordadas.<br/><br/>
        
        <b>CUARTA - INDEPENDENCIA:</b> El CONTRATISTA actuará de manera autónoma e independiente, 
        sin subordinación laboral. No existe relación laboral entre las partes.<br/><br/>
        
        <b>QUINTA - OBLIGACIONES:</b> El CONTRATISTA se obliga a cumplir el objeto contractual con 
        la mayor diligencia y calidad, respondiendo por los resultados.<br/><br/>
        
        <b>SEXTA - SEGURIDAD SOCIAL:</b> El CONTRATISTA se obliga a estar afiliado y al día en el 
        pago del sistema de seguridad social integral.
        """
    
    elif tipo_contrato == 'Aprendizaje':
        clausulas = f"""
        <b>PRIMERA - OBJETO:</b> LA EMPRESA patrocina al APRENDIZ para que realice su etapa práctica 
        como <b>{contrato_data.get('cargo', '')}</b>, relacionada con su formación académica.<br/><br/>
        
        <b>SEGUNDA - DURACIÓN:</b> El contrato tendrá vigencia desde el <b>{contrato_data.get('fecha_inicio', '')}</b> 
        hasta el <b>{contrato_data.get('fecha_fin', 'finalización del programa de formación')}</b>.<br/><br/>
        
        <b>TERCERA - APOYO DE SOSTENIMIENTO:</b> LA EMPRESA reconocerá un apoyo de sostenimiento 
        mensual de <b>${contrato_data.get('salario', 0):,.0f} pesos colombianos</b>, el cual NO constituye 
        salario.<br/><br/>
        
        <b>CUARTA - OBLIGACIONES DEL APRENDIZ:</b> Cumplir con el plan de formación, asistir puntualmente, 
        desarrollar las actividades asignadas y mantener buen rendimiento académico.<br/><br/>
        
        <b>QUINTA - AFILIACIÓN:</b> LA EMPRESA afiliará al APRENDIZ al sistema de riesgos laborales 
        durante el tiempo de la práctica.<br/><br/>
        
        <b>SEXTA - NATURALEZA:</b> Este contrato NO genera relación laboral ni obliga a LA EMPRESA 
        a vincular al APRENDIZ una vez terminado el período de práctica.
        """
    
    else:
        clausulas = f"""
        <b>PRIMERA - OBJETO:</b> Contrato para <b>{contrato_data.get('cargo', '')}</b>.<br/><br/>
        <b>SEGUNDA - REMUNERACIÓN:</b> <b>${contrato_data.get('salario', 0):,.0f} pesos colombianos</b>.
        """
    
    story.append(Paragraph(clausulas, body_style))
    story.append(Spacer(1, 0.3*inch))
    
    # FIRMAS - CAMBIO A VILLAVICENCIO
    firma_texto = f"""
    <b>Firmado en la ciudad de Villavicencio - Meta, a los {datetime.now().day} días del mes de 
    {datetime.now().strftime('%B')} de {datetime.now().year}.</b>
    """
    story.append(Paragraph(firma_texto, body_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Tabla de firmas
    firma_table_data = [
        ['_' * 40, '_' * 40],
        ['EL EMPLEADOR', 'EL TRABAJADOR'],
        ['ECOMARKET', f"{empleado_data.get('nombre', '')} {empleado_data.get('apellido', '')}"],
        ['NIT: 900.123.456-7', f"CC: {empleado_data.get('nro_documento', '')}"]
    ]
    
    firma_table = Table(firma_table_data, colWidths=[3*inch, 3*inch])
    firma_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 20),
    ]))
    
    story.append(firma_table)
    
    # Generar PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

def crear_contrato(empleado_id, tipo_contrato, fecha_inicio, fecha_fin, 
                   salario, cargo, observaciones=""):
    """Crea un nuevo contrato y genera su PDF"""
    id_contrato = obtener_siguiente_id("contrato")
    
    # Obtener datos del empleado
    empleado_doc = empleados.get(str(empleado_id))
    if not empleado_doc:
        print("❌ Empleado no encontrado")
        return None
    
    contrato_data = {
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
    
    # Generar PDF del contrato
    try:
        pdf_bytes = generar_pdf_contrato(contrato_data, empleado_doc)
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        contrato_data["pdf_base64"] = pdf_base64
    except Exception as e:
        print(f"❌ Error generando PDF: {e}")
        contrato_data["pdf_base64"] = None
    
    try:
        res = contratos.insert(contrato_data)
        return res["_key"]
    except Exception as e:
        print(f"❌ Error crear_contrato: {e}")
        return None

def listar_contratos(busqueda=None):
    """Lista todos los contratos con información del empleado"""
    if busqueda:
        busqueda_sin_acentos = remover_acentos(busqueda).lower()
        
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
        
        resultados = []
        for contrato in todos_contratos:
            nombre = remover_acentos(contrato.get('empleado_nombre_completo', '')).lower()
            apellido = remover_acentos(contrato.get('empleado_apellido_completo', '')).lower()
            documento = remover_acentos(contrato.get('empleado_documento', '')).lower()
            tipo_contrato = remover_acentos(contrato.get('tipo_contrato', '')).lower()
            cargo = remover_acentos(contrato.get('cargo', '')).lower()
            
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

def contar_contratos_empleado(empleado_id):
    """Cuenta cuántos contratos tiene un empleado"""
    try:
        aql = """
        FOR contrato IN contratos
            FILTER contrato.empleado_id == @empleado_id
            COLLECT WITH COUNT INTO cantidad
            RETURN cantidad
        """
        cursor = db.aql.execute(aql, bind_vars={"empleado_id": str(empleado_id)})
        resultado = list(cursor)
        return resultado[0] if resultado else 0
    except Exception as e:
        print(f"❌ Error contar_contratos_empleado: {e}")
        return 0

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
