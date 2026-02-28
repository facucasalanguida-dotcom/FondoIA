import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# Configuración de base de datos local
CHROMA_DB_DIR = "./chroma_db"

def obtener_embeddings():
    """Retorna la instancia del modelo de embeddings geométricos de Google"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("No se encontró GEMINI_API_KEY en el entorno para extraer embeddings.")
    
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=api_key
    )

def procesar_pdf_boe(ruta_archivo: str, id_documento: str):
    """
    Lee un PDF jurídico, lo divide en fragmentos (chunks) y lo vectoriza
    guardándolo en la base de datos Chroma local bajo un identificador.
    """
    # 1. Cargar el PDF
    loader = PyPDFLoader(ruta_archivo)
    docs = loader.load()
    
    # 2. Dividir el texto
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    splits = text_splitter.split_documents(docs)
    
    # Etiquetar los metadatos para poder filtrar
    for doc in splits:
        doc.metadata["id_documento"] = id_documento

    # 3. Generar embeddings y persistir en Chroma
    embeddings = obtener_embeddings()
    Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR
    )
    
    return len(splits)

def buscar_requisitos_relevantes(query: str, id_documento: str, k: int = 4) -> str:
    """
    Busca en la base de datos vectorial aquellos fragmentos del texto original
    que respondan a la query para el documento específico.
    """
    embeddings = obtener_embeddings()
    
    # Conectamos a la base de datos existente
    vectordb = Chroma(
        persist_directory=CHROMA_DB_DIR, 
        embedding_function=embeddings
    )
    
    # Forzamos una búsqueda en lenguaje natural y devolvemos los 'k' mejores bloques
    busqueda = f"requisitos de facturación, CNAE elegible, plazos, {query}"
    
    # Se filtra para buscar sólo en los fragmentos del propio ID de la convocatoria
    results = vectordb.similarity_search(
        busqueda, 
        k=k,
        filter={"id_documento": id_documento}
    )
    
    if not results:
        # Fallback por si la DB no está lista o vacía
        return "No se encontró contexto en la base de datos para este documento."
        
    contextos = [doc.page_content for doc in results]
    return "\n\n---\n\n".join(contextos)
