from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from app.routers import analisis, documentos

app = FastAPI(
    title="FondoIA Backend API",
    description="API de backend para FondoIA: automatiza el matching probabilístico entre contabilidad de Pymes y normativas de fondos públicos.",
    version="1.0.0"
)

app.include_router(analisis.router)
app.include_router(documentos.router)

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "online",
        "message": "Bienvenido a la API de FondoIA. Visite /docs para la documentación de Swagger."
    }
