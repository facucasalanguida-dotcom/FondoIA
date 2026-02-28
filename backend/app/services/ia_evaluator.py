import os
import json
import asyncio
from fastapi import HTTPException
import google.generativeai as genai

from app.models import PerfilPyme, ConvocatoriaSubvencion, ResultadoEvaluacion

# Configurar de forma segura la clave del entorno
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

async def evaluar_elegibilidad(empresa: PerfilPyme, convocatoria: ConvocatoriaSubvencion, contexto_requisitos: str) -> ResultadoEvaluacion:
    """
    Función asíncrona que evalúa probabilísticamente la elegibilidad de una Pyme para una convocatoria.
    Utiliza el contexto RAG de ChromaDB para analizar la normativa.
    Retorna un ResultadoEvaluacion estructurado.
    """
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="La variable de entorno GEMINI_API_KEY no está configurada."
        )

    # Prompt de sistema y de usuario
    system_instruction = (
        "Eres un Auditor Jurídico-Financiero Experto en Subvenciones Españolas. "
        "Tu objetivo es realizar un matching probabilístico entre el perfil económico de una Pyme "
        "y los requisitos legales de una convocatoria pública que han sido extraídos de su documento legal original."
    )
    
    prompt = f"""
    Evalúa la siguiente empresa para la convocatoria especificada dadas ciertas normativas clave.
    
    DATOS DE LA EMPRESA:
    Nombre: {empresa.nombre_fiscal}
    CNAE: {empresa.cnae}
    Facturación Anual: {empresa.facturacion_anual_eur} EUR
    Empleados: {empresa.empleados_plantilla}
    Ubicación: {empresa.ubicacion_ccaa}
    Necesidad Inversión: {empresa.necesidad_inversion}
    
    DATOS DE LA CONVOCATORIA Y NORMATIVA EXTRAÍDA (RAG):
    Título: {convocatoria.titulo_ayuda}
    Organismo: {convocatoria.organismo_emisor}
    Presupuesto Total: {convocatoria.presupuesto_total_eur} EUR
    Documento ID: {convocatoria.id_documento_boe}
    
    TEXTO NORMATIVO EXTRÍDO DE LA CONVOCATORIA:
    {contexto_requisitos}
    
    De acuerdo con tus conocimientos, el texto normativo provisto y los datos, devuelve tu evaluación 
    exclusivamente en formato JSON, usando el esquema indicado por el sistema.
    """
    
    try:
        # Usamos un execution thread no bloqueante ya que el SDK genai de Google hasta la fecha
        # usa requests bloqueantes o asyncio.to_thread puede ser necesario.
        # Las ultimas versiones tienen `generate_content_async`
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_instruction
        )
        
        # Le indicamos explícitamente a Gemini que deseamos que el JSON 
        # retornado siga estrictamente la estructura de nuestro esquema de Pydantic ResultadoEvaluacion.
        response = await model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ResultadoEvaluacion
            ),
            # Un timeout generoso para evitar cuelgues largos
            request_options={"timeout": 30}
        )
        
        # Validar y parsear el JSON de respuesta con el modelo Pydantic
        respuesta_json = json.loads(response.text)
        resultado = ResultadoEvaluacion(**respuesta_json)
        return resultado
        
    except Exception as e:
        # Si ocurre un error, TimeOut o un fallo parseando JSON, manejamos la excepción.
        raise HTTPException(
            status_code=503,
            detail=f"Fallo en la comunicación con la IA o timeout: {str(e)}"
        )
