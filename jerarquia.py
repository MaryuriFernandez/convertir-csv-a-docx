"""Ubica cada descripción en su fondo / serie / subserie.

El CSV de AtoM solo trae `parentId` (id del padre) y `qubitParentSlug`. Los nombres de fondo, serie y
subserie salen de las filas padre cuando están en el mismo CSV (exportar «con descendientes»). Si no
están, se usa un archivo `jerarquia.csv` (ver README) que el programa ayuda a generar.
"""

import csv
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .lector import limpiar

# Niveles de descripción que son contenedores (no se imprimen como descripciones).
CONTENEDORES = {"fondo", "subfondo", "serie", "subserie", "seccion", "subseccion", "coleccion"}


def normalizar(texto: str) -> str:
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", texto or "") if unicodedata.category(c) != "Mn")
    return sin_tildes.strip().lower()


@dataclass(frozen=True)
class Ubicacion:
    lineas: tuple  # líneas del título (fondo, serie, subserie)
    archivo: str  # nombre del .docx (sección / fondo)


class FaltaJerarquia(Exception):
    """Hay descripciones cuyo padre no está en el CSV ni en jerarquia.csv."""

    def __init__(self, faltantes: dict, plantilla: Path | None = None):
        self.faltantes = faltantes  # {parentId: {"cantidad": n, "ejemplo": signatura}}
        self.plantilla = plantilla
        super().__init__(f"Falta la jerarquía de {len(faltantes)} padre(s): {', '.join(faltantes)}")


def armar_ubicacion(nombres: list, archivo: str | None = None, nivel_archivo: int | None = None) -> Ubicacion:
    """Título de 3 líneas: primer nivel, serie y subserie (los dos últimos). Fondo y serie en mayúsculas."""
    if len(nombres) >= 3:
        seleccion = [nombres[0], nombres[-2], nombres[-1]]
    else:
        seleccion = list(nombres)
    lineas = tuple(t.upper() if i < len(seleccion) - 1 else t for i, t in enumerate(seleccion))
    if not archivo:
        # Con 4 o más niveles (fondo > sección > serie > subserie) el documento lleva el nombre de la sección.
        indice = nivel_archivo if nivel_archivo is not None else (1 if len(nombres) >= 4 else 0)
        archivo = nombres[min(indice, len(nombres) - 1)]
    return Ubicacion(lineas=lineas, archivo=archivo.upper())


def cargar_mapa(ruta) -> dict:
    """jerarquia.csv: columnas parentId, fondo, serie, subserie y (opcional) archivo."""
    mapa = {}
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        for fila in csv.DictReader(f):
            parent_id = limpiar(fila.get("parentId"))
            nombres = [limpiar(fila.get(c)) for c in ("fondo", "serie", "subserie")]
            nombres = [n for n in nombres if n]
            if parent_id and nombres:
                mapa[parent_id] = armar_ubicacion(nombres, archivo=limpiar(fila.get("archivo")) or nombres[0])
    return mapa


class Jerarquia:
    def __init__(self, filas, mapa=None, nivel_archivo=None):
        self.mapa = mapa or {}
        self.nivel_archivo = nivel_archivo
        self.por_id = {limpiar(f.get("legacyId")): f for f in filas if limpiar(f.get("legacyId"))}
        self.por_slug = {limpiar(f.get("slug")): f for f in filas if limpiar(f.get("slug"))}

    @staticmethod
    def es_descripcion(fila) -> bool:
        return normalizar(fila.get("levelOfDescription")) not in CONTENEDORES

    @staticmethod
    def clave_padre(fila) -> str:
        return limpiar(fila.get("parentId")) or limpiar(fila.get("qubitParentSlug"))

    def _padre(self, fila):
        padre = self.por_id.get(limpiar(fila.get("parentId")))
        return padre or self.por_slug.get(limpiar(fila.get("qubitParentSlug")))

    def _cadena(self, fila) -> list:
        """Ancestros presentes en el CSV, de la raíz al padre directo."""
        cadena, vistos, actual = [], set(), fila
        while (padre := self._padre(actual)) is not None and id(padre) not in vistos:
            vistos.add(id(padre))
            cadena.append(padre)
            actual = padre
        return cadena[::-1]

    def ubicar(self, fila):
        """Devuelve la Ubicacion, o None si el padre no está en el CSV ni en el mapa."""
        nombres = [
            limpiar(a.get("title"))
            for a in self._cadena(fila)
            if normalizar(a.get("levelOfDescription")) in CONTENEDORES | {""}
        ]
        nombres = [n for n in nombres if n]
        if nombres:
            return armar_ubicacion(nombres, nivel_archivo=self.nivel_archivo)
        return self.mapa.get(self.clave_padre(fila))
