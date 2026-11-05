
import hashlib
from io import BytesIO

import pandas as pd
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

# Validar la configuracion de sucursales
configuracion_valida = (
    bool(archivos_cargados)
    and len(archivos_por_sucursal) == len(archivos_cargados)
    and len(set(nombres_ingresados)) == len(nombres_ingresados)
    and all(nombres_ingresados)
)

# Identificar cambios en archivos y configuracion
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

# Evitar mostrar resultados de una configuracion anterior
if st.session_state.get("configuracion_anterior") != configuracion_actual:
    st.session_state.pop("resultados_dataflow", None)
    st.session_state["configuracion_anterior"] = configuracion_actual

# Ejecutar el procesamiento
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

        st.success(
            "Los archivos fueron procesados correctamente."
        )

    except ValueError as error:
        st.error(f"No se pudo procesar: {error}")

    except Exception:
        st.error(
            "Ocurrio un error inesperado durante el procesamiento."
        )


# ----------------------------------------
# RESULTADOS Y DESCARGAS
# ----------------------------------------

if "resultados_dataflow" in st.session_state:

    resultados = st.session_state["resultados_dataflow"]
    datos = resultados["datos_validados"]

    # Resumen del procesamiento
    st.subheader("📊 Resumen del procesamiento")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Registros analizados",
            len(datos)
        )

    with col2:
        st.metric(
            "Registros validos",
            int((datos["estado"] == "VALIDO").sum())
        )

    with col3:
        st.metric(
            "Registros rechazados",
            int((datos["estado"] == "RECHAZADO").sum())
        )

    # Vista previa
    st.subheader("Vista previa de resultados")

    st.dataframe(
        datos,
        use_container_width=True
    )

    # ----------------------------------------
    # DESCARGAR RESULTADOS EN EXCEL
    # ----------------------------------------

    st.divider()
    st.subheader("📥 Descargar resultados")

    st.write(
        "Descarga los resultados del procesamiento "
        "en archivos Excel independientes."
    )

    def convertir_a_excel(tabla):
        memoria = BytesIO()

        with pd.ExcelWriter(
            memoria,
            engine="openpyxl"
        ) as writer:
            tabla.to_excel(
                writer,
                index=False,
                sheet_name="Resultados"
            )

        return memoria.getvalue()

    archivos_salida = {
        "datos_validados": (
            "ventas_validadas.xlsx",
            "📄 Descargar ventas validadas"
        ),
        "duplicados": (
            "duplicados.xlsx",
            "🔎 Descargar duplicados"
        ),
        "reporte_calidad": (
            "reporte_calidad.xlsx",
            "📊 Descargar reporte de calidad"
        )
    }

    col_descarga1, col_descarga2, col_descarga3 = st.columns(3)

    columnas_descarga = [
        col_descarga1,
        col_descarga2,
        col_descarga3
    ]

    for columna, (clave, informacion) in zip(
        columnas_descarga,
        archivos_salida.items()
    ):

        nombre_archivo, etiqueta = informacion

        with columna:
            st.download_button(
                label=etiqueta,
                data=convertir_a_excel(resultados[clave]),
                file_name=nombre_archivo,
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                key=f"descarga_{clave}",
                use_container_width=True
            )


# ----------------------------------------
# PIE DE PAGINA
# ----------------------------------------

st.divider()

st.caption(
    "DataFlow | Soluciones de analítica y automatización de datos"
)
