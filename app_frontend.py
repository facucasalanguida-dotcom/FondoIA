import os
import streamlit as st
import requests
import json

# ==========================================
# Configuración Inicial de la Página
# ==========================================
st.set_page_config(
    page_title="FondoIA - Tramitador Inteligente",
    page_icon="📋",
    layout="wide"
)

# Constantes de conexión al Backend (Preparado para Producción con EnvVar)
API_BASE = os.getenv("API_URL_BASE", "http://localhost:8000")
API_URL_EVALUAR = f"{API_BASE}/api/v1/analisis/evaluar"
API_URL_MEMORIA = f"{API_BASE}/api/v1/documentos/generar-memoria"

# Datos mockeados de la convocatoria simulada
convocatoria_mock = {
    "id_convocatoria": "FTE_AND_26",
    "titulo_ayuda": "Fondo Tecnológico de Andalucía 2026",
    "organismo_emisor": "Junta de Andalucía - Consejería de Innovación",
    "presupuesto_total_eur": 5000000.0,
    "id_documento_boe": "BOJA_FTE_AND_26_pdf"
}

# ==========================================
# Barra Lateral (Sidebar) - Formulario Ingesta
# ==========================================
with st.sidebar:
    st.header("🏢 Ingesta de Datos (Pyme)")
    st.markdown("Por favor, introduce los datos contables y fiscales de la empresa.")
    
    nombre_fiscal = st.text_input("Nombre Fiscal", value="Acme Innovación S.L.")
    cnae = st.text_input("CNAE", value="6201 - Actividades de programación informática")
    facturacion_anual = st.number_input("Facturación Anual (€)", min_value=0.0, value=250000.0, step=10000.0)
    empleados = st.number_input("Número de Empleados", min_value=1, value=15, step=1)
    
    # Lista de CCAA de España
    ccaa_opciones = [
        "Andalucía", "Aragón", "Asturias", "Baleares", "Canarias", 
        "Cantabria", "Castilla y León", "Castilla-La Mancha", "Cataluña", 
        "Comunidad Valenciana", "Extremadura", "Galicia", "Madrid", 
        "Murcia", "Navarra", "País Vasco", "La Rioja", "Ceuta", "Melilla"
    ]
    ubicacion = st.selectbox("Ubicación (CCAA)", ccaa_opciones, index=0)
    
    necesidad_inversion = st.text_area(
        "Necesidad de Inversión", 
        value="Desarrollo de una nueva plataforma SaaS de Inteligencia Artificial para el sector contable y contratación de 2 ingenieros de software senior."
    )

# Preparar el payload de la empresa
perfil_pyme = {
    "nombre_fiscal": nombre_fiscal,
    "cnae": cnae,
    "facturacion_anual_eur": facturacion_anual,
    "empleados_plantilla": empleados,
    "ubicacion_ccaa": ubicacion,
    "necesidad_inversion": necesidad_inversion
}

# ==========================================
# Pantalla Principal - Pestañas
# ==========================================
st.title("🚀 FondoIA: Matching y Tramitación")
st.markdown("Automatizando el ciclo de vida de las subvenciones públicas para Pymes.")

tab1, tab2 = st.tabs(["📊 Dashboard de Ayudas", "📄 Generador de Expedientes"])

# --- TAB 1: Dashboard de Ayudas ---
with tab1:
    st.subheader("Oportunidades Abiertas")
    
    # Tarjeta de la convocatoria simulada
    with st.container(border=True):
        st.markdown(f"### {convocatoria_mock['titulo_ayuda']}")
        st.markdown(f"**Organismo:** {convocatoria_mock['organismo_emisor']}")
        st.markdown(f"**Presupuesto Total:** {convocatoria_mock['presupuesto_total_eur']:,.2f} €")
        
        with st.expander("Ver Metadatos Legales"):
            st.info(f"ID Documento BOE Indexado en RAG: {convocatoria_mock['id_documento_boe']}")
            
        if st.button("🔍 Analizar Viabilidad", type="primary", key="btn_evaluar"):
            with st.spinner("Motor IA analizando elegibilidad..."):
                payload = {
                    "empresa": perfil_pyme,
                    "convocatoria": convocatoria_mock
                }
                
                try:
                    response = requests.post(API_URL_EVALUAR, json=payload, timeout=40)
                    response.raise_for_status()
                    resultado = response.json()
                    
                    st.success("Análisis completado.")
                    
                    # Mostrar métricas del JSON devuelto
                    col1, col2 = st.columns(2)
                    with col1:
                        # Color verde si es alta, rojo si baja
                        color = "normal" if resultado['probabilidad_exito'] >= 50 else "inverse"
                        st.metric(label="Probabilidad de Éxito", value=f"{resultado['probabilidad_exito']}%", delta=color)
                        st.markdown(f"**Elegible:** {'✅ Sí' if resultado['es_elegible'] else '❌ No'}")
                        
                    with col2:
                        st.info(f"**Justificación Económica:**\n{resultado['justificacion_economica']}")
                        st.warning(f"**Coste de Oportunidad:**\n{resultado['coste_oportunidad']}")
                    
                    # Guardar el estado en sesión para usarlo en la pestaña 2
                    st.session_state['evaluacion_completada'] = True
                    st.session_state['payload_memoria'] = payload
                    st.session_state['probabilidad'] = resultado['probabilidad_exito']
                    
                except requests.exceptions.RequestException as e:
                    st.error(f"Error de conexión con el backend: {e}. ¿Está el servidor FastAPI encendido?")

# --- TAB 2: Generador de Expedientes ---
with tab2:
    st.subheader("Generación de Memoria Técnica")
    
    if st.session_state.get('evaluacion_completada', False):
        if st.session_state['probabilidad'] >= 50:
            st.success("El proyecto tiene un alto índice de elegibilidad. Listo para generar el documento formal.")
            
            if st.button("✍️ Generar Memoria Técnica Completa", type="primary"):
                with st.spinner("Agente Experto redactando el expediente. Esto puede tomar unos 30-40 segundos..."):
                    try:
                        response_memoria = requests.post(
                            API_URL_MEMORIA, 
                            json=st.session_state['payload_memoria'],
                            timeout=60
                        )
                        response_memoria.raise_for_status()
                        documento_md = response_memoria.json()['documento_markdown']
                        
                        st.session_state['documento_generado'] = documento_md
                        st.toast("Memoria generada correctamente!", icon="🎉")
                        
                    except requests.exceptions.RequestException as e:
                        st.error(f"Error al generar la memoria: {e}")
            
            # Si el documento ya está generado en la sesión, mostrarlo y dar botón de descarga
            if st.session_state.get('documento_generado'):
                st.markdown("---")
                st.markdown("### Vista Previa del Documento")
                
                # Contenedor con scroll (o expander) para el markdown largo
                with st.expander("Abrir Documento Markdown", expanded=True):
                    st.markdown(st.session_state['documento_generado'])
                
                # Botón nativo de Streamlit para descargar
                st.download_button(
                    label="💾 Descargar Memoria (.md)",
                    data=st.session_state['documento_generado'],
                    file_name=f"Memoria_Tecnica_{nombre_fiscal.replace(' ', '_')}.md",
                    mime="text/markdown",
                )
        else:
            st.error("⚠️ La viabilidad es menor al 50%. Se desaconseja dedicar recursos a generar esta memoria técnica.")
            st.info("Revisa la Justificación Económica en el Dashboard de Ayudas para realizar ajustes en tu perfil.")
    else:
        st.info("Primero debes ir al 'Dashboard de Ayudas' y 'Analizar Viabilidad' antes de poder generar el expediente.")
