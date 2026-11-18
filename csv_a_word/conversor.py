"""Orquesta la conversión: CSV -> un .docx por fondo/sección."""

import csv
import re
from collections import Counter, OrderedDict
from pathlib import Path

from .descripcion import extraer_campos
from .escritor import escribir_documento
from .jerarquia import FaltaJerarquia, Jerarquia, cargar_mapa
from .lector import leer_csv, limpiar

NOMBRE_PLANTILLA = "jerarquia_pendiente.csv"


def _nombre_seguro(nombre: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", nombre).strip() or "SIN_NOMBRE"


def _escribir_plantilla(faltantes: dict, carpeta: Path) -> Path:
    ruta = carpeta / NOMBRE_PLANTILLA
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow(["parentId", "fondo", "serie", "subserie", "archivo", "ejemplo_signatura", "cantidad"])
        for parent_id, datos in faltantes.items():
            escritor.writerow([parent_id, "", "", "", "", datos["ejemplo"], datos["cantidad"]])
    return ruta


def convertir(ruta_csv, carpeta_salida, ruta_jerarquia=None, nivel_archivo=None, avisar=print) -> list[Path]:
    """Convierte el CSV y devuelve las rutas de los .docx creados.

    Lanza FaltaJerarquia si algún padre no se puede resolver (y deja una plantilla para completarla).
    """
    filas = leer_csv(ruta_csv)
    carpeta = Path(carpeta_salida)
    carpeta.mkdir(parents=True, exist_ok=True)
    mapa = cargar_mapa(ruta_jerarquia) if ruta_jerarquia else {}
    jerarquia = Jerarquia(filas, mapa, nivel_archivo)

    # (fondo, archivo) -> ubicacion.lineas -> [descripciones], conservando el orden del CSV.
    documentos: OrderedDict = OrderedDict()
    faltantes: dict = {}
    for fila in filas:
        if not jerarquia.es_descripcion(fila):
            continue
        ubicacion = jerarquia.ubicar(fila)
        if ubicacion is None:
            clave = Jerarquia.clave_padre(fila) or "(sin padre)"
            dato = faltantes.setdefault(clave, {"cantidad": 0, "ejemplo": limpiar(fila.get("referenceCode"))})
            dato["cantidad"] += 1
            continue
        campos = extraer_campos(fila)
        clave_doc = (ubicacion.fondo, ubicacion.archivo)
        documentos.setdefault(clave_doc, OrderedDict()).setdefault(ubicacion.lineas, []).append(campos)

    if faltantes:
        raise FaltaJerarquia(faltantes, _escribir_plantilla(faltantes, carpeta))

    # La misma sección en fondos distintos no se mezcla: si el nombre se repite, se añade el fondo.
    repetidos = Counter(archivo for _, archivo in documentos)
    creados = []
    for (fondo, archivo), subseries in documentos.items():
        nombre = archivo if repetidos[archivo] == 1 or fondo == archivo else f"{archivo} - {fondo}"
        ruta = carpeta / f"{_nombre_seguro(nombre)}.docx"
        escribir_documento(ruta, list(subseries.items()))
        total = sum(len(d) for d in subseries.values())
        avisar(f"{ruta.name}: {len(subseries)} subserie(s), {total} descripción(es)")
        creados.append(ruta)
    return creados
