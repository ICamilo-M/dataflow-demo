
import hashlib

import streamlit as st

from src.procesador import (
    procesar_dataflow,
    generar_excel_seguro,
)


# ==========================================
# CONFIGURACION GENERAL
# ==========================================

st.set_page_config(
    page_title="DataFlow | Analitica de Datos",
    page_icon="📊",
    layout="wide",
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
        "✅ Detectar registros invalidos "
        "e identificadores duplicados."
    )

with col3:
    st.info(
        "📈 Generar reportes de calidad "
        "y descargar resultados."
    )

st.divider()

st.caption(
    "DataFlow | Soluciones de analitica "
    "y automatizacion de datos"
)


# ==========================================
# CARGA DE ARCHIVOS EXCEL
# ==========================================

st.header("📁 Cargar archivos de ventas")

st.write(
    "Selecciona los archivos Excel de las sucursales "
    "que deseas consolidar y analizar."
)

archivos_cargados = st.file_uploader(
    "Seleccionar archivos Excel",
    type=["xlsx"],
    accept_multiple_files=True,
)


# ==========================================
# IDENTIFICACION DE SUCURSALES
# ==========================================

archivos_por_sucursal = {}
nombres_ingresados = []

if archivos_cargados:

    st.success(
        f"Se cargaron {len(archivos_cargados)} archivo(s)."
    )

    st.subheader("Identificar sucursales")

    st.write(
        "Indica a que sucursal pertenece cada archivo."
    )

    for numero, archivo in enumerate(archivos_cargados):

        nombre_sugerido = archivo.name.rsplit(".", 1)[0]

        # Asociar el campo al contenido del archivo
        # para evitar reutilizar nombres anteriores.
        identificador = hashlib.sha256(
            archivo.getvalue()
        ).hexdigest()[:12]

        sucursal = st.text_input(
            f"Sucursal del archivo: {archivo.name}",
            value=nombre_sugerido,
            key=f"sucursal_{numero}_{identificador}",
        ).strip()

        nombres_ingresados.append(sucursal)

        if sucursal:
            archivos_por_sucursal[sucursal] = archivo

    if any(not nombre for nombre in nombres_ingresados):

        st.warning(
            "Todos los archivos deben tener una sucursal."
        )

    elif len(set(nombres_ingresados)) != len(
        nombres_ingresados
    ):

        st.error(
            "Hay nombres de sucursales repetidos. "
            "Asigna un nombre diferente a cada archivo."
        )

    else:

        st.success(
            "Todas las sucursales fueron identificadas."
        )

else:

    st.info(
        "Todavia no has seleccionado archivos Excel."
    )


# ==========================================
# PROCESAMIENTO DE ARCHIVOS
# ==========================================

st.divider()

st.header("⚙️ Procesamiento de datos")

rechazar_duplicados = st.checkbox(
    "Rechazar registros con identificadores duplicados",
    value=False,
)

configuracion_valida = (
    bool(archivos_cargados)
    and len(archivos_por_sucursal) == len(archivos_cargados)
    and len(set(nombres_ingresados)) == len(nombres_ingresados)
    and all(nombres_ingresados)
)

identificadores_archivos = []

for archivo in archivos_cargados or []:

    identificador = hashlib.sha256(
        archivo.getvalue()
    ).hexdigest()

    identificadores_archivos.append(
        (archivo.name, identificador)
    )

configuracion_actual = (
    tuple(identificadores_archivos),
    tuple(nombres_ingresados),
    rechazar_duplicados,
)

# Invalidar resultados cuando cambia cualquier
# archivo, sucursal u opcion de procesamiento.

if (
    st.session_state.get("configuracion_anterior")
    != configuracion_actual
):

    st.session_state.pop(
        "resultados_dataflow",
        None,
    )

    st.session_state[
        "configuracion_anterior"
    ] = configuracion_actual


procesar = st.button(
    "🚀 Procesar archivos",
    type="primary",
    disabled=not configuracion_valida,
)

if procesar:

    st.session_state.pop(
        "resultados_dataflow",
        None,
    )

    try:

        with st.spinner(
            "Procesando archivos Excel..."
        ):

            resultados = procesar_dataflow(
                archivos_por_sucursal,
                rechazar_duplicados=rechazar_duplicados,
            )

        st.session_state[
            "resultados_dataflow"
        ] = resultados

        st.success(
            "Los archivos fueron procesados correctamente."
        )

    except ValueError as error:

        st.error(
            f"No se pudo procesar: {error}"
        )

    except Exception:

        st.error(
            "Ocurrio un error inesperado "
            "durante el procesamiento."
        )


# ==========================================
# RESUMEN DE RESULTADOS
# ==========================================

if "resultados_dataflow" in st.session_state:

    resultados = st.session_state[
        "resultados_dataflow"
    ]

    datos = resultados["datos_validados"]

    st.divider()

    st.subheader("📊 Resumen del procesamiento")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Registros analizados",
            len(datos),
        )

    with col2:

        st.metric(
            "Registros validos",
            int(
                (datos["estado"] == "VALIDO").sum()
            ),
        )

    with col3:

        st.metric(
            "Registros rechazados",
            int(
                (datos["estado"] == "RECHAZADO").sum()
            ),
        )


    # ======================================
    # VISUALIZACION DE RESULTADOS
    # ======================================

    st.subheader("📋 Datos procesados")

    st.dataframe(
        datos,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("🔎 Identificadores duplicados")

    duplicados = resultados["duplicados"]

    if duplicados.empty:

        st.info(
            "No se detectaron identificadores duplicados."
        )

    else:

        st.dataframe(
            duplicados,
            use_container_width=True,
            hide_index=True,
        )

    st.subheader("📈 Reporte de calidad")

    st.dataframe(
        resultados["reporte_calidad"],
        use_container_width=True,
        hide_index=True,
    )


    # ======================================
    # DESCARGAS EXCEL SEGURAS
    # ======================================

    st.divider()

    st.subheader("📥 Descargar resultados")

    st.write(
        "Descarga los archivos generados por DataFlow."
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.download_button(
            label="📥 Ventas validadas",
            data=generar_excel_seguro(
                resultados["datos_validados"]
            ),
            file_name="ventas_validadas.xlsx",
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            key="descargar_ventas",
        )

    with col2:

        st.download_button(
            label="📥 Duplicados",
            data=generar_excel_seguro(
                resultados["duplicados"]
            ),
            file_name="duplicados.xlsx",
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            key="descargar_duplicados",
        )

    with col3:

        st.download_button(
            label="📥 Reporte de calidad",
            data=generar_excel_seguro(
                resultados["reporte_calidad"]
            ),
            file_name="reporte_calidad.xlsx",
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            key="descargar_reporte",
        )
