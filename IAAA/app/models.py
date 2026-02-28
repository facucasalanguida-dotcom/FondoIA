from pydantic import BaseModel, Field

class PerfilPyme(BaseModel):
    nombre_fiscal: str = Field(..., description="Nombre fiscal de la empresa")
    cnae: str = Field(..., description="Código Nacional de Actividades Económicas")
    facturacion_anual_eur: float = Field(..., description="Facturación anual en euros")
    empleados_plantilla: int = Field(..., description="Número de empleados en plantilla")
    ubicacion_ccaa: str = Field(..., description="Comunidad Autónoma donde está ubicada")
    necesidad_inversion: str = Field(..., description="Descripción de la necesidad de inversión")

class ConvocatoriaSubvencion(BaseModel):
    id_convocatoria: str = Field(..., description="Identificador único de la convocatoria")
    titulo_ayuda: str = Field(..., description="Título de la ayuda o subvención")
    organismo_emisor: str = Field(..., description="Organismo que emite la convocatoria")
    presupuesto_total_eur: float = Field(..., description="Presupuesto total en euros de la convocatoria")
    id_documento_boe: str = Field(..., description="ID del documento PDF indexado en ChromaDB (BOE/BOJA)")

class ResultadoEvaluacion(BaseModel):
    es_elegible: bool = Field(..., description="Indicar si la empresa es elegible para la subvención")
    probabilidad_exito: int = Field(..., ge=0, le=100, description="Probabilidad de éxito del 0 al 100")
    justificacion_economica: str = Field(..., description="Justificación corta explicando por qué cumple o incumple (referente a facturación, CNAE o ubicación)")
    coste_oportunidad: str = Field(..., description="Evaluación corta de si el esfuerzo compensa el importe")

class EvaluacionRequest(BaseModel):
    empresa: PerfilPyme
    convocatoria: ConvocatoriaSubvencion

class SolicitudMemoria(BaseModel):
    empresa: PerfilPyme
    convocatoria: ConvocatoriaSubvencion

class RespuestaMemoria(BaseModel):
    documento_markdown: str = Field(..., description="Memoria técnica generada en formato Markdown")
