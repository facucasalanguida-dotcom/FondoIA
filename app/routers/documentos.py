from fastapi import APIRouter, status, HTTPException
from app.models import SolicitudMemoria, RespuestaMemoria
from app.services.document_generator import generar_memoria_tecnica

router = APIRouter(
    prefix="/api/v1/documentos",
    tags=["Documentos"]
)

@router.post("/generar-memoria", response_model=RespuestaMemoria, status_code=status.HTTP_200_OK)
async def endpoint_generar_memoria(request: SolicitudMemoria):
    """
    Genera automáticamente la Memoria Técnica del Proyecto requerida por una convocatoria
    pública, basándose en los datos económicos y la necesidad de inversión de la Pyme.
    """
    try:
        documento_md = await generar_memoria_tecnica(request.empresa, request.convocatoria)
        return RespuestaMemoria(documento_markdown=documento_md)
    except HTTPException as ht_e:
        raise ht_e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al generar el documento: {str(e)}"
        )
