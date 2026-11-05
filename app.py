
import streamlit as st

st.set_page_config(
    page_title="DataFlow | Analítica de Datos",
    page_icon="📊",
    layout="wide"
)

st.title("📊 DataFlow")

st.subheader(
    "Plataforma de procesamiento y calidad de datos"
)

st.write(
    "Consolida, limpia y valida archivos Excel "
    "de diferentes sucursales desde una sola plataforma."
)

st.divider()

st.header("¿Qué puedes hacer con DataFlow?")

col1, col2, col3 = st.columns(3)

with col1:
    st.info(
        "📁 Consolidar archivos Excel "
        "de diferentes sucursales."
    )

with col2:
    st.info(
        "✅ Detectar registros inválidos "
        "e identificadores duplicados."
    )

with col3:
    st.info(
        "📈 Generar reportes de calidad "
        "y descargar resultados."
    )

st.divider()

st.caption(
    "DataFlow | Soluciones de analítica y automatización de datos"
)
