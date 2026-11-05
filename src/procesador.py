
# ==========================================
# DATAFLOW - MODULO 01
# Motor de procesamiento y calidad de datos
# ==========================================

from pathlib import Path
from zipfile import BadZipFile, LargeZipFile
from xml.etree.ElementTree import ParseError

import pandas as pd
from openpyxl.utils.exceptions import InvalidFileException


# ==========================================
# 1. VALIDACION DE VENTAS
# ==========================================

def validar_ventas(datos):
    """
    Valida los registros de ventas.

    Comprueba:
    - Identificadores faltantes.
    - Productos vacios.
    - Cantidades no validas.
    - Precios no validos.

    Conserva los registros y sus motivos de rechazo.
    """

    resultado = datos.copy()

    def identificar_errores(fila):

        errores = []

        # Validar identificador
        if (
            pd.isna(fila["id_venta"])
            or str(fila["id_venta"]).strip() == ""
        ):
            errores.append("ID de venta faltante")

        # Validar producto
        if (
            pd.isna(fila["producto"])
            or str(fila["producto"]).strip() == ""
        ):
            errores.append("Producto faltante")

        # Validar cantidad
        cantidad = pd.to_numeric(
            fila["cantidad"],
            errors="coerce"
        )

        if pd.isna(cantidad) or cantidad <= 0:
            errores.append("Cantidad no valida")

        # Validar precio
        precio = pd.to_numeric(
            fila["precio_unitario"],
            errors="coerce"
        )

        if pd.isna(precio) or precio < 0:
            errores.append("Precio no valido")

        return "; ".join(errores)

    resultado["motivo_error"] = resultado.apply(
        identificar_errores,
        axis=1
    )

    resultado["estado"] = resultado["motivo_error"].apply(
        lambda error: (
            "VALIDO"
            if error == ""
            else "RECHAZADO"
        )
    )

    return resultado


# ==========================================
# 2. LECTURA SEGURA DE ARCHIVOS EXCEL
# ==========================================

def _leer_excel_ventas(ruta, sucursal, **opciones):
    """
    Lee un archivo Excel.

    Convierte errores conocidos de archivos
    danados o ilegibles en mensajes claros
    para el usuario.

    No oculta otros errores de programacion.
    """

    try:

        return pd.read_excel(
            ruta,
            **opciones
        )

    except (
        BadZipFile,
        LargeZipFile,
        InvalidFileException,
        EOFError,
        ParseError
    ) as error:

        raise ValueError(
            f"Archivo de {sucursal}: "
            "El archivo Excel está dañado o "
            "no tiene un formato válido. "
            "Verifica el archivo e intenta "
            "cargarlo nuevamente."
        ) from error

    except ValueError as error:

        mensaje = str(error).lower()

        formato_desconocido = (
            "excel file format cannot be determined"
            in mensaje
        )

        zip_invalido = (
            "file is not a zip file"
            in mensaje
        )

        if formato_desconocido or zip_invalido:

            raise ValueError(
                f"Archivo de {sucursal}: "
                "El archivo Excel está dañado o "
                "no tiene un formato válido. "
                "Verifica el archivo e intenta "
                "cargarlo nuevamente."
            ) from error

        raise


# ==========================================
# 3. CONSOLIDACION DE VENTAS
# ==========================================

def consolidar_ventas(archivos):
    """
    Valida, normaliza encabezados y consolida
    archivos Excel de diferentes sucursales.
    """

    tablas = []

    if not archivos:
        raise ValueError(
            "No se recibieron archivos"
        )

    for sucursal, ruta in archivos.items():

        # Leer primera fila
        primera_fila = _leer_excel_ventas(
            ruta,
            sucursal,
            header=None,
            nrows=1
        )

        # Verificar encabezados
        if (
            primera_fila.empty
            or primera_fila.iloc[0].isna().all()
        ):

            raise ValueError(
                f"Archivo de {sucursal}: "
                "El archivo Excel esta vacio "
                "o no tiene encabezados"
            )

        encabezados = primera_fila.iloc[0].tolist()

        # Normalizar encabezados
        encabezados_normalizados = [
            str(columna).strip().lower()
            for columna in encabezados
        ]

        # Detectar encabezados duplicados
        indice = pd.Index(
            encabezados_normalizados
        )

        duplicados = indice[
            indice.duplicated()
        ].unique().tolist()

        if duplicados:

            raise ValueError(
                f"Archivo de {sucursal}: "
                f"Encabezados duplicados: {duplicados}"
            )

        # Leer datos completos
        datos = _leer_excel_ventas(
            ruta,
            sucursal
        )

        datos.columns = encabezados_normalizados

        # Validar columnas obligatorias
        try:

            validar_columnas(datos)

        except ValueError as error:

            raise ValueError(
                f"Archivo de {sucursal}: {error}"
            ) from error

        # Registrar sucursal
        datos["sucursal"] = sucursal

        tablas.append(datos)

    return pd.concat(
        tablas,
        ignore_index=True
    )


# ==========================================
# 4. GENERACION DE REPORTE DE CALIDAD
# ==========================================

def generar_reporte(datos):
    """
    Calcula indicadores basicos de calidad.
    """

    total = len(datos)

    validos = (
        datos["estado"] == "VALIDO"
    ).sum()

    rechazados = (
        datos["estado"] == "RECHAZADO"
    ).sum()

    tasa = (
        validos / total * 100
        if total
        else 0
    )

    return pd.DataFrame({
        "Indicador": [
            "Registros analizados",
            "Registros validos",
            "Registros rechazados",
            "Tasa de calidad (%)"
        ],
        "Valor": [
            total,
            validos,
            rechazados,
            round(tasa, 2)
        ]
    })


# ==========================================
# 5. IDENTIFICACION DE DUPLICADOS
# ==========================================

def mascara_duplicados(datos, columnas=None):
    """
    Identifica registros repetidos.

    Normaliza los identificadores antes de
    compararlos, sin modificar los datos
    originales.
    """

    if columnas is None:
        columnas = ["id_venta"]

    faltantes = [
        columna
        for columna in columnas
        if columna not in datos.columns
    ]

    if faltantes:

        raise ValueError(
            f"Columnas no encontradas: {faltantes}"
        )

    claves = datos[columnas].copy()

    if "id_venta" in claves.columns:

        claves["id_venta"] = (
            claves["id_venta"]
            .astype("string")
            .str.strip()
        )

    return claves.duplicated(
        keep=False
    )


def detectar_duplicados(datos, columnas=None):
    """
    Devuelve los registros duplicados.

    Conserva sus valores originales.
    """

    mascara = mascara_duplicados(
        datos,
        columnas
    )

    return datos.loc[mascara].copy()


# ==========================================
# 6. VALIDACION DE COLUMNAS
# ==========================================

def validar_columnas(
    datos,
    columnas_obligatorias=None
):
    """
    Comprueba que existan las columnas
    necesarias para procesar ventas.
    """

    if columnas_obligatorias is None:

        columnas_obligatorias = [
            "id_venta",
            "producto",
            "cantidad",
            "precio_unitario"
        ]

    faltantes = [
        columna
        for columna in columnas_obligatorias
        if columna not in datos.columns
    ]

    if faltantes:

        raise ValueError(
            "Columnas obligatorias faltantes: "
            f"{faltantes}"
        )

    return True


# ==========================================
# 7. PROCESAMIENTO PRINCIPAL
# ==========================================

def procesar_dataflow(
    archivos,
    columnas_duplicados=None,
    rechazar_duplicados=False
):
    """
    Ejecuta el procesamiento completo.

    - Consolida archivos.
    - Normaliza registros.
    - Detecta duplicados.
    - Valida ventas.
    - Genera indicadores.

    Permite rechazar duplicados cuando
    el usuario activa esa opcion.
    """

    if columnas_duplicados is None:
        columnas_duplicados = ["id_venta"]

    # 1. Consolidar
    datos = consolidar_ventas(
        archivos
    )

    validar_columnas(datos)

    # 2. Limpiar
    datos_limpios = limpiar_ventas(
        datos
    )

    # 3. Detectar duplicados
    duplicados = detectar_duplicados(
        datos_limpios,
        columnas=columnas_duplicados
    )

    # 4. Validar registros
    datos_validados = validar_ventas(
        datos_limpios
    )

    # 5. Rechazo opcional de duplicados
    if rechazar_duplicados:

        registros_repetidos = mascara_duplicados(
            datos_limpios,
            columnas_duplicados
        )

        for indice in datos_validados.index[
            registros_repetidos
        ]:

            motivo_actual = datos_validados.at[
                indice,
                "motivo_error"
            ]

            nuevo_motivo = (
                "Identificador duplicado"
            )

            if motivo_actual:

                nuevo_motivo = (
                    motivo_actual
                    + "; "
                    + nuevo_motivo
                )

            datos_validados.at[
                indice,
                "motivo_error"
            ] = nuevo_motivo

            datos_validados.at[
                indice,
                "estado"
            ] = "RECHAZADO"

    # 6. Generar reporte
    reporte = generar_reporte(
        datos_validados
    )

    return {
        "datos_validados": datos_validados,
        "duplicados": duplicados,
        "reporte_calidad": reporte
    }


# ==========================================
# 8. GENERACION SEGURA DE EXCEL
# ==========================================

def generar_excel_seguro(tabla):
    """
    Genera un archivo Excel en memoria.

    Convierte las celdas interpretadas como
    formulas en celdas de texto.

    No modifica el DataFrame original.
    """

    from io import BytesIO

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

        hoja = writer.sheets[
            "Resultados"
        ]

        # Convertir formulas en texto
        for fila in hoja.iter_rows():

            for celda in fila:

                if celda.data_type == "f":
                    celda.data_type = "s"

    return memoria.getvalue()


# ==========================================
# 9. EXPORTACION DE RESULTADOS
# ==========================================

def exportar_resultados(
    resultados,
    carpeta_destino
):
    """
    Exporta los tres archivos principales
    de DataFlow.
    """

    carpeta = Path(
        carpeta_destino
    )

    carpeta.mkdir(
        parents=True,
        exist_ok=True
    )

    nombres_archivos = {
        "datos_validados": "ventas_validadas.xlsx",
        "duplicados": "duplicados.xlsx",
        "reporte_calidad": "reporte_calidad.xlsx"
    }

    rutas_generadas = {}

    for clave, nombre_archivo in (
        nombres_archivos.items()
    ):

        if clave not in resultados:

            raise ValueError(
                "Resultado requerido no "
                f"encontrado: {clave}"
            )

        ruta = carpeta / nombre_archivo

        contenido_excel = generar_excel_seguro(
            resultados[clave]
        )

        ruta.write_bytes(
            contenido_excel
        )

        rutas_generadas[clave] = str(
            ruta
        )

    return rutas_generadas


# ==========================================
# 10. LIMPIEZA DE VENTAS
# ==========================================

def limpiar_ventas(datos):
    """
    Limpia y normaliza los registros.

    - Normaliza nombres de productos.
    - Convierte cantidades a numeros.
    - Convierte precios a numeros.
    - Conserva los datos para validacion.
    """

    resultado = datos.copy()

    # Normalizar nombres de productos
    resultado["producto"] = (
        resultado["producto"]
        .astype("string")
        .str.strip()
        .str.title()
    )

    # Convertir cantidad a numerico
    resultado["cantidad"] = pd.to_numeric(
        resultado["cantidad"],
        errors="coerce"
    )

    # Convertir precio a numerico
    resultado["precio_unitario"] = pd.to_numeric(
        resultado["precio_unitario"],
        errors="coerce"
    )

    return resultado
