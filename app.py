
import hashlib

import streamlit as st

from src.procesador import procesar_dataflow


# ----------------------------------------
# CONFIGURACION GENERAL
# ----------------------------------------

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


# ----------------------------------------
# PRESENTACION DE FUNCIONALIDADES
# ----------------------------------------

st.header("¿Qué puedes hacer con DataFlow?")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("📁 Consolidar archivos Excel de diferentes sucursales.")

with col2:
    st.info("✅ Detectar registros inválidos y duplicados.")

with col3:
    st.info("📈 Generar reportes de calidad y descargar resultados.")

st.divider()


# ----------------------------------------
# CARGA DE ARCHIVOS
# ----------------------------------------

st.header("📁 Cargar archivos de ventas")

archivos_cargados = st.file_uploader(
    "Seleccionar archivos Excel",
    type=["xlsx"],
    accept_multiple_files=True
)

archivos_por_sucursal = {}
nombres_ingresados = []

if archivos_cargados:
    st.success(
        f"Se cargaron {len(archivos_cargados)} archivo(s)."
    )

    st.subheader("Identificar sucursales")

    for numero, archivo in enumerate(archivos_cargados):
        nombre_sugerido = archivo.name.rsplit(".", 1)[0]

        sucursal = st.text_input(
            f"Sucursal del archivo: {archivo.name}",
            value=nombre_sugerido,
            key=f"sucursal_{numero}"
        ).strip()

        nombres_ingresados.append(sucursal)

        if sucursal:
            archivos_por_sucursal[sucursal] = archivo

    if any(not nombre for nombre in nombres_ingresados):
        st.warning("Todos los archivos deben tener una sucursal.")

    elif len(set(nombres_ingresados)) != len(nombres_ingresados):
        st.error(
            "Hay nombres de sucursales repetidos. "
            "Asigna un nombre diferente a cada archivo."
        )

    else:
        st.success("Todas las sucursales fueron identificadas.")

else:
    st.info("Todavía no has seleccionado archivos Excel.")


# ----------------------------------------
# PROCESAMIENTO
# ----------------------------------------

st.divider()
st.header("⚙️ Procesamiento de datos")

rechazar_duplicados = st.checkbox(
    "Rechazar registros con identificadores duplicados",
    value=False
)

configuracion_valida = (
    bool(archivos_cargados)
    and len(archivos_por_sucursal) == len(archivos_cargados)
    and len(set(nombres_ingresados)) == len(nombres_ingresados)
    and all(nombres_ingresados)
)

identificadores_archivos = []

for archivo in archivos_cargados or []:
    identificadores_archivos.append(
        (
            archivo.name,
            hashlib.sha256(archivo.getvalue()).hexdigest()
        )
    )

configuracion_actual = (
    tuple(identificadores_archivos),
    tuple(nombres_ingresados),
    rechazar_duplicados
)

if st.session_state.get("configuracion_anterior") != configuracion_actual:
    st.session_state.pop("resultados_dataflow", None)
    st.session_state["configuracion_anterior"] = configuracion_actual

procesar = st.button(
    "🚀 Procesar archivos",
    type="primary",
    disabled=not configuracion_valida
)

if procesar:
    st.session_state.pop("resultados_dataflow", None)

    try:
        with st.spinner("Procesando archivos Excel..."):
            resultados = procesar_dataflow(
                archivos_por_sucursal,
                rechazar_duplicados=rechazar_duplicados
            )

        st.session_state["resultados_dataflow"] = resultados
        st.success("Los archivos fueron procesados correctamente.")

    except ValueError as error:
        st.error(f"No se pudo procesar: {error}")

    except Exception:
        st.error(
            "Ocurrió un error inesperado durante el procesamiento."
        )


# ----------------------------------------
# RESULTADOS
# ----------------------------------------

if "resultados_dataflow" in st.session_state:
    resultados = st.session_state["resultados_dataflow"]
    datos = resultados["datos_validados"]

    st.subheader("📊 Resumen del procesamiento")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Registros analizados", len(datos))

    with col2:
        st.metric(
            "Registros válidos",
            int((datos["estado"] == "VALIDO").sum())
        )

    with col3:
        st.metric(
            "Registros rechazados",
            int((datos["estado"] == "RECHAZADO").sum())
        )

    st.subheader("Vista previa de resultados")
    st.dataframe(datos, use_container_width=True)

st.divider()

st.caption(
    "DataFlow | Soluciones de analítica y automatización de datos"
)

