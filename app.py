# app.py
# streamlit run app.py

import time
import base64
import re
from pathlib import Path
import streamlit as st

# ====== IMPORTS ======
from corelogic import get_llm
from utils import extract_text_from_pdf_bytes, resumen_documento
from promots import get_prompt_summary_str
from database_supabase import (
    init_database,
    guardar_analisis,
    buscar_por_nombre_pdf,
    is_production
)

# ====================================

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
ASSETS = Path("assets")
HERO_PATH = ASSETS / "banner.png"
LOGO = ASSETS / "logo.png"
CORP = "#0f6db4"

st.set_page_config(
    page_title="Analizador MultiPDF IA - Magnetron",
    page_icon=str(LOGO) if LOGO.exists() else "📄",
    layout="wide",
)

# Indicador de entorno (justo después de set_page_config)
if is_production():
    st.success("🟢 MODO PRODUCCIÓN - Los datos se guardarán en Supabase")
else:
    st.warning("🟢 MODO PRODUCCIÓN - Los datos se guardarán en Supabase")

# -----------------------------
# UTILIDADES
# -----------------------------
def _b64(path: Path):
    if path.exists():
        return base64.b64encode(path.read_bytes()).decode("utf-8")
    return ""

def limpiar_nombre_archivo(nombre):
    nombre_sin_ext = nombre.replace('.pdf', '').replace('.PDF', '')
    nombre_limpio = re.sub(r'[^a-zA-Z0-9_-]', '_', nombre_sin_ext)
    nombre_limpio = re.sub(r'_+', '_', nombre_limpio)
    if len(nombre_limpio) > 50:
        nombre_limpio = nombre_limpio[:50]
    return nombre_limpio

def apply_skin():
    st.markdown(
        f"""
        <style>
        /* Fondo transparente */
        [data-testid="stAppViewContainer"] {{
            background: transparent !important;
        }}

        [data-testid="stHeader"] {{
            background-color: rgba(0,0,0,0);
        }}

        /* OCULTAR SIDEBAR */
        [data-testid="stSidebar"] {{
            display: none;
        }}

        /* Banner azul ANCHO COMPLETO */
        .hero-banner {{
            background: {CORP};
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            color: white;
            margin-bottom: 2rem;
            width: 100%;
        }}

        .hero-banner h1 {{
            margin: 0;
            font-size: 2rem;
            font-weight: 600;
        }}

        .hero-banner p {{
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
        }}

        /* Botones azules */
        .stButton>button {{
            border-radius: 5px;
        }}

        /* Remover padding de columnas */
        .block-container {{
            padding-left: 1rem;
            padding-right: 1rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def hero_header(title, subtitle):
    """Banner con logo integrado (no duplicado)"""
    logo_html = ""
    if LOGO.exists():
        logo_b64 = _b64(LOGO)
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="80" style="margin-bottom:1rem">'

    st.markdown(
        f"""
        <div class="hero-banner">
            {logo_html}
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# PANTALLA DE BIENVENIDA
# -----------------------------
def pantalla_bienvenida():
    apply_skin()

    # Banner superior SOLO (sin logo adicional arriba)
    hero_header(
        title="📄 Analizador MultiPDF con IA",
        subtitle="Sistema de análisis de pliegos técnicos - Magnetron S.A.S."
    )

    # Formulario centrado
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Iniciar Sesión")
        st.markdown("Ingresa tu nombre para continuar")

        nombre = st.text_input(
            "Nombre completo",
            placeholder="Ej: Juan Pérez",
            key="input_nombre"
        )

        # Botón AZUL (type="primary" lo hace azul por defecto)
        if st.button("🚀 Ingresar", type="primary", use_container_width=True):
            if nombre.strip():
                st.session_state.usuario = nombre.strip()
                st.rerun()
            else:
                st.error("Por favor ingresa tu nombre")

# -----------------------------
# FUNCIÓN PRINCIPAL
# -----------------------------
def main():
    # Inicializar session state
    if 'usuario' not in st.session_state:
        st.session_state.usuario = ""

    if 'ultimo_resumen' not in st.session_state:
        st.session_state.ultimo_resumen = None

    if 'ultimas_tablas' not in st.session_state:
        st.session_state.ultimas_tablas = None

    if 'nombre_pdfs' not in st.session_state:
        st.session_state.nombre_pdfs = ""

    # Inicializar BD
    try:
        init_database()
    except:
        pass

    # Control de sesión
    if not st.session_state.usuario:
        pantalla_bienvenida()
        return

    # Aplicar diseño
    apply_skin()

    # Header
    hero_header(
        title="📄 Analizador MultiPDF con IA",
        subtitle=f"Usuario: {st.session_state.usuario} | {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # Botón salir
    col1, col2 = st.columns([9, 1])
    with col2:
        if st.button("🚪 Salir", use_container_width=True):
            st.session_state.usuario = ""
            st.session_state.ultimo_resumen = None
            st.session_state.ultimas_tablas = None
            st.session_state.nombre_pdfs = ""
            st.rerun()

    # Descripción
    st.info(
        "📋 **Sube uno o varios pliegos en PDF** y genera un **Resumen Ejecutivo** "
        "detallado con información técnica clave"
    )

    # Carga de archivos
    st.markdown("### 📁 Arrastra o selecciona tus archivos PDF")

    uploaded_file = st.file_uploader(
        "Limit 200MB per file • PDF",
        type=["pdf"],
        help="Arrastra tus archivos PDF aquí"
    )

    # Procesamiento
    if uploaded_file:
        st.success(f"✅ Archivo cargado: **{uploaded_file.name}**")

        if st.button("🚀 Generar Resumen y Tablas", type="primary", use_container_width=True):
            with st.spinner("⏳ Procesando PDF..."):
                try:
                    nombre_pdf = uploaded_file.name

                    # Buscar en BD
                    analisis_existente = buscar_por_nombre_pdf(nombre_pdf)

                    regenerar = False

                    if analisis_existente:
                        st.info(f"📚 Este PDF ya fue analizado el {analisis_existente['fecha_hora'].strftime('%d/%m/%Y %H:%M')}")

                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.success("✅ Resumen disponible en caché")
                        with col2:
                            regenerar = st.button("🔄 Regenerar", key="regenerar")

                        if not regenerar:
                            st.session_state.ultimo_resumen = analisis_existente['resumen']
                            st.session_state.ultimas_tablas = analisis_existente.get('tablas_tecnicas')
                            st.session_state.nombre_pdfs = nombre_pdf
                            st.rerun()

                    # Procesar
                    if not analisis_existente or regenerar:
                        pdf_bytes = uploaded_file.read()
                        docs = extract_text_from_pdf_bytes(pdf_bytes, nombre_pdf)

                        if not docs:
                            st.error("⚠️ No se pudo extraer texto del PDF")
                        else:
                            llm = get_llm()
                            prompt = get_prompt_summary_str()
                            
                            # Generar resumen
                            with st.spinner("📝 Generando resumen ejecutivo..."):
                                resumen = resumen_documento(docs, llm, prompt)
                                st.session_state.ultimo_resumen = resumen
                            
                            st.session_state.nombre_pdfs = nombre_pdf

                            try:
                                guardar_analisis(
                                    nombre_archivo=nombre_pdf,
                                    resumen=resumen,
                                    tablas=tablas
                                )
                            except Exception as e:
                                st.warning(f"⚠️ No se pudo guardar en BD: {e}")

                            st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {e}")

    # Mostrar resultados en dos columnas
    if st.session_state.ultimo_resumen:
        st.markdown("---")
        
        # Dos columnas: Resumen | Tablas
        col_resumen, col_tablas = st.columns([1, 1])
        
        with col_resumen:
            st.markdown("### 📄 Resumen Ejecutivo")
            if st.session_state.nombre_pdfs:
                st.caption(f"📎 **Archivo:** {st.session_state.nombre_pdfs}")
            
            st.markdown(st.session_state.ultimo_resumen)
            
            # Botón descarga resumen
            nombre_archivo = limpiar_nombre_archivo(st.session_state.nombre_pdfs)
            st.download_button(
                label="📥 Descargar Resumen (TXT)",
                data=st.session_state.ultimo_resumen,
                file_name=f"resumen_{nombre_archivo}.txt",
                mime="text/plain",
                use_container_width=True,
                key="download_resumen"
            )
    
# ----------------------------- 
# BOTÓN DE FEEDBACK FLOTANTE
# ----------------------------- 
def render_feedback_button():
    """Renderiza botón flotante que abre Forms para feedback"""
    
    # URL de tu Microsoft Forms
    FORMS_URL = "https://forms.office.com/r/yLAnpwJw1V"
    
    st.markdown("""
    <style>
    .feedback-float-container {
        position: fixed;
        bottom: 20px;
        left: 20px;
        z-index: 999;
    }
    .feedback-float-btn {
        background: linear-gradient(135deg, #0f6db4 0%, #1a8fd9 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 14px 28px;
        font-weight: 600;
        font-size: 15px;
        box-shadow: 0 4px 15px rgba(15, 109, 180, 0.4);
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
    }
    .feedback-float-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(15, 109, 180, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="feedback-float-container">
        <a href="{FORMS_URL}" target="_blank" class="feedback-float-btn">
            💬 Déjanos tu Feedback
        </a>
    </div>
    """, unsafe_allow_html=True)

render_feedback_button()

if __name__ == "__main__":
    main()



