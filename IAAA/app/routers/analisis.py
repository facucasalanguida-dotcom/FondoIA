from fastapi import APIRouter, status, HTTPException
from app.models import PerfilPyme, ResultadoEvaluacion, EvaluacionRequest
from app.services.ia_evaluator import evaluar_elegibilidad
from app.services.vector_db import buscar_requisitos_relevantes

router = APIRouter(
    prefix="/api/v1/analisis",
    tags=["Análisis"]
)

@router.post("/ingesta", status_code=status.HTTP_200_OK)
async def ingesta_pyme(perfil: PerfilPyme):
    """
    Endpoint para la ingesta de datos de una Pyme.
    Recibe un JSON con los datos de una empresa, los valida y simula su estructuración.
    """
    
    return {
        "status": "success",
        "message": f"Los datos de la empresa '{perfil.nombre_fiscal}' han sido validados y estructurados correctamente.",
        "data_procesada": {
            "cnae": perfil.cnae,
            "facturacion_anual_eur": perfil.facturacion_anual_eur,
            "empleados_plantilla": perfil.empleados_plantilla,
            "ubicacion_ccaa": perfil.ubicacion_ccaa,
            "necesidad_inversion": perfil.necesidad_inversion
        }
    }

@router.post("/evaluar", response_model=ResultadoEvaluacion, status_code=status.HTTP_200_OK)
async def evaluar_pyme_convocatoria(request: EvaluacionRequest):
    """
    Evalúa la elegibilidad de una Pyme frente a una convocatoria pública usando IA.
    Ahora utiliza la base de datos RAG ChromaDB para enriquecer el contexto.
    """
    try:
        # Búsqueda semántica en base de datos de los requisitos aplicables a la empresa
        query_pyme = f"CNAE: {request.empresa.cnae}, Facturación: {request.empresa.facturacion_anual_eur}, Empleados: {request.empresa.empleados_plantilla}, Inversión: {request.empresa.necesidad_inversion}"
        contexto_filtrado = buscar_requisitos_relevantes(query_pyme, request.convocatoria.id_documento_boe)
        
        resultado = await evaluar_elegibilidad(request.empresa, request.convocatoria, contexto_filtrado)
        return resultado
    except HTTPException as ht_e:
        raise ht_e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al evaluar la elegibilidad: {str(e)}"
        )
