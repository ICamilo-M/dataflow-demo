
# DataFlow - Modulo 01
# Sistema de limpieza y consolidacion de datos


# DATAFLOW - MODULO 01
# Motor de procesamiento y calidad de datos

import pandas as pd
from pathlib import Path


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
            "VALIDO" if error == "" else "RECHAZADO"
        )
    )

    return resultado


def consolidar_ventas(archivos):
    """
    Valida, normaliza encabezados y consolida
    archivos Excel de diferentes sucursales.
    """
    tablas = []

    if not archivos:
        raise ValueError("No se recibieron archivos")

    for sucursal, ruta in archivos.items():
        # Leer la primera fila del Excel
        primera_fila = pd.read_excel(
            ruta,
            header=None,
            nrows=1
        )

        # Verificar que el archivo tenga encabezados
        if primera_fila.empty or primera_fila.iloc[0].isna().all():
            raise ValueError(
                f"Archivo de {sucursal}: "
                "El archivo Excel está vacío o no tiene encabezados"
            )

        # Obtener los encabezados originales
        encabezados = primera_fila.iloc[0].tolist()


        # Normalizar encabezados para compararlos
        encabezados_normalizados = [
            str(columna).strip().lower()
            for columna in encabezados
        ]

        # Detectar duplicados despues de normalizar
        indice = pd.Index(encabezados_normalizados)
        duplicados = indice[
            indice.duplicated()
        ].unique().tolist()

        if duplicados:
            raise ValueError(
                f"Archivo de {sucursal}: "
                f"Encabezados duplicados: {duplicados}"
            )

        # Leer las ventas normalmente
        datos = pd.read_excel(ruta)

        # Asignar los nombres normalizados
        datos.columns = encabezados_normalizados

        # Verificar las columnas obligatorias
        try:
            validar_columnas(datos)
        except ValueError as error:
            raise ValueError(
                f"Archivo de {sucursal}: {error}"
            ) from error

        # Identificar la sucursal de procedencia
        datos["sucursal"] = sucursal
        tablas.append(datos)

    return pd.concat(tablas, ignore_index=True)


def generar_reporte(datos):
    """
    Calcula indicadores basicos de calidad.
    """
    total = len(datos)
    validos = (datos["estado"] == "VALIDO").sum()
    rechazados = (datos["estado"] == "RECHAZADO").sum()

    tasa = (validos / total * 100) if total else 0

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



def mascara_duplicados(datos, columnas=None):
    """
    Identifica claves repetidas normalizando id_venta.
    No modifica los datos originales.
    """
    if columnas is None:
        columnas = ["id_venta"]

    faltantes = [
        columna for columna in columnas
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

    return claves.duplicated(keep=False)


def detectar_duplicados(datos, columnas=None):
    """
    Devuelve los registros con claves repetidas.
    Conserva sus valores originales.
    """
    mascara = mascara_duplicados(datos, columnas)

    return datos.loc[mascara].copy()



def validar_columnas(datos, columnas_obligatorias=None):
    """
    Verifica que existan las columnas necesarias
    para procesar las ventas.
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
            f"Columnas obligatorias faltantes: {faltantes}"
        )

    return True



def procesar_dataflow(
    archivos,
    columnas_duplicados=None,
    rechazar_duplicados=False
):
    """
    Ejecuta el procesamiento integrado de DataFlow.

    Los duplicados se reportan siempre.
    Opcionalmente, pueden marcarse como rechazados.
    """
    if columnas_duplicados is None:
        columnas_duplicados = ["id_venta"]

    # 1. Consolidar y comprobar columnas
    datos = consolidar_ventas(archivos)
    validar_columnas(datos)

    # 2. Limpiar y normalizar
    datos_limpios = limpiar_ventas(datos)

    # 3. Detectar posibles duplicados
    duplicados = detectar_duplicados(
        datos_limpios,
        columnas=columnas_duplicados
    )

    # 4. Validar registros
    datos_validados = validar_ventas(datos_limpios)

    # 5. Aplicar regla configurable de duplicados
    if rechazar_duplicados:
        registros_repetidos = mascara_duplicados(
            datos_limpios,
            columnas_duplicados
        )

        for indice in datos_validados.index[registros_repetidos]:
            motivo_actual = datos_validados.at[
                indice, "motivo_error"
            ]

            nuevo_motivo = "Identificador duplicado"

            if motivo_actual:
                nuevo_motivo = (
                    motivo_actual + "; " + nuevo_motivo
                )

            datos_validados.at[
                indice, "motivo_error"
            ] = nuevo_motivo

            datos_validados.at[
                indice, "estado"
            ] = "RECHAZADO"

    # 6. Generar indicadores
    reporte = generar_reporte(datos_validados)

    return {
        "datos_validados": datos_validados,
        "duplicados": duplicados,
        "reporte_calidad": reporte
    }




def generar_excel_seguro(tabla):
    """
    Genera un archivo Excel en memoria.

    Evita que los textos que comienzan con =
    se almacenen como formulas ejecutables.

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

        hoja = writer.sheets["Resultados"]

        # Convertir formulas detectadas en texto
        for fila in hoja.iter_rows():
            for celda in fila:
                if celda.data_type == "f":
                    celda.data_type = "s"

    return memoria.getvalue()


def exportar_resultados(resultados, carpeta_destino):
    """
    Exporta los resultados de DataFlow
    utilizando la generacion segura de Excel.
    """
    carpeta = Path(carpeta_destino)
    carpeta.mkdir(parents=True, exist_ok=True)

    nombres_archivos = {
        "datos_validados": "ventas_validadas.xlsx",
        "duplicados": "duplicados.xlsx",
        "reporte_calidad": "reporte_calidad.xlsx"
    }

    rutas_generadas = {}

    for clave, nombre_archivo in nombres_archivos.items():

        if clave not in resultados:
            raise ValueError(
                f"Resultado requerido no encontrado: {clave}"
            )

        ruta = carpeta / nombre_archivo

        contenido_excel = generar_excel_seguro(
            resultados[clave]
        )

        ruta.write_bytes(contenido_excel)

        rutas_generadas[clave] = str(ruta)

    return rutas_generadas


def limpiar_ventas(datos):
    """
    Limpia y normaliza los datos de ventas.

    - Normaliza nombres de productos.
    - Convierte cantidades y precios a numeros.
    - Conserva los registros para validacion posterior.
    """
    resultado = datos.copy()

    # Normalizar nombres de productos
    resultado["producto"] = (
        resultado["producto"]
        .astype("string")
        .str.strip()
        .str.title()
    )

    # Convertir cantidades a valores numericos
    resultado["cantidad"] = pd.to_numeric(
        resultado["cantidad"],
        errors="coerce"
    )

    # Convertir precios a valores numericos
    resultado["precio_unitario"] = pd.to_numeric(
        resultado["precio_unitario"],
        errors="coerce"
    )

    return resultado
