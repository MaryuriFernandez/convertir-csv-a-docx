"""Lectura tolerante del CSV exportado por AtoM."""

import csv
import io
from pathlib import Path

# AtoM escribe NULL en las columnas vacías de eventos.
VALORES_VACIOS = {"", "NULL", "null"}


def limpiar(valor):
    """Devuelve el texto en una sola línea y sin espacios sobrantes; '' si viene vacío o NULL."""
    if valor is None:
        return ""
    texto = " ".join(str(valor).split())
    return "" if texto in VALORES_VACIOS else texto


def _decodificar(datos: bytes) -> str:
    for codificacion in ("utf-8-sig", "cp1252"):
        try:
            return datos.decode(codificacion)
        except UnicodeDecodeError:
            continue
    return datos.decode("latin-1")


def _detectar_delimitador(texto: str) -> str:
    encabezado = texto.splitlines()[0] if texto else ""
    return max((",", ";", "\t"), key=encabezado.count)


def leer_csv(ruta) -> list[dict]:
    """Lee el CSV y devuelve una lista de diccionarios (una por fila)."""
    texto = _decodificar(Path(ruta).read_bytes())
    delimitador = _detectar_delimitador(texto)
    lector = csv.DictReader(io.StringIO(texto, newline=""), delimiter=delimitador)
    return [fila for fila in lector if any((v or "").strip() for v in fila.values())]
