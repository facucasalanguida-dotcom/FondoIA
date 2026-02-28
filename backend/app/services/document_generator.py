import os
from fastapi import HTTPException
import google.generativeai as genai

from app.models import PerfilPyme, ConvocatoriaSubvencion
from app.services.vector_db import buscar_requisitos_relevantes

async def generar_memoria_tecnica(empresa: PerfilPyme, convocatoria: ConvocatoriaSubvencion) -> str:
    """
    Función asíncrona que genera una memoria técnica en formato Markdown
    basada en el perfil de la Pyme y la convocatoria pública.
    """
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="La variable de entorno GEMINI_API_KEY no está configurada."
        )

    system_instruction = (
        "Eres un Consultor Senior de Subvenciones Públicas Especializado en Redacción de Proyectos. "
        "Tu objetivo es redactar un documento formal, persuasivo, técnico y estrictamente en español "
        "para presentar a la Administración Pública Española. "
        "El documento debe estar estructurado en Markdown y no debe contener alucinaciones creativas, "
        "solo utilizar los datos proporcionados y proyecciones realistas, serias y coherentes con la empresa."
    )
    
    prompt = f"""
    Redacta la Memoria Técnica del Proyecto para solicitar la siguiente ayuda pública.
    
    DATOS DE LA EMPRESA SOLICITANTE:
    - Razón Social: {empresa.nombre_fiscal}
    - CNAE: {empresa.cnae}
    - Facturación Anual: {empresa.facturacion_anual_eur} EUR
    - Empleados (Plantilla): {empresa.empleados_plantilla}
    - Ubicación (CCAA): {empresa.ubicacion_ccaa}
    - Necesidad de Inversión / Objeto del Proyecto: {empresa.necesidad_inversion}
    
    DATOS DE LA CONVOCATORIA (A LA QUE SE APLICA):
    - Título: {convocatoria.titulo_ayuda}
    - Órgano Convocante: {convocatoria.organismo_emisor}
    - Presupuesto Total de la Convocatoria: {convocatoria.presupuesto_total_eur} EUR
    - ID Documento Oficial: {convocatoria.id_documento_boe}
    
    TEXTO NORMATIVO / REQUISITOS (RECUPERADOS RAG): 
    {buscar_requisitos_relevantes("Normativa de la solicitud, inversión y plazos", convocatoria.id_documento_boe, k=10)}
    
    INSTRUCCIONES DE FORMATO STRICTAS:
    Debes generar un documento en formato Markdown puro (sin comillas invertidas de bloque de código, devuelve el texto plano de markdown directamente).
    El documento debe incluir, como mínimo y de forma obligatoria, las siguientes 4 secciones principales (puedes estructurarlas con subtítulos si lo ves conveniente):
    
    1. Resumen Ejecutivo: Presentación de la empresa y alineación con los objetivos de la ayuda.
    2. Memoria Descriptiva de la Inversión: Detalle de en qué se va a gastar el dinero (basado en la 'necesidad de inversión') y cómo encaja en los requisitos de la convocatoria.
    3. Impacto Económico y Sostenibilidad: Justificación de cómo esta ayuda mejorará la competitividad de la empresa (mencionando facturación actual y empleados).
    4. Cronograma de Ejecución: Estimación de plazos (ficticios pero realistas y lógicos para el tipo de proyecto).
    
    El tono debe ser: ADMINISTRATIVO FORMAL, TÉCNICO Y CONVINCENTE.
    """
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-pro", # El modelo pro generalmente redacta mejor textos largos
            system_instruction=system_instruction
        )
        
        # Configuramos baja temperatura (0.3) para reducir alucinaciones 
        # y mantener un estilo sobrio y predecible.
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3
            ),
            request_options={"timeout": 60} # Más tiempo porque la generación de texto largo demora más
        )
        
        return response.text
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Error durante la generación de la memoria con la IA: {str(e)}"
        )
