"""Punto de entrada: línea de comandos (con argumentos) o ventana (sin argumentos)."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .conversor import convertir
from .jerarquia import FaltaJerarquia


def _mensaje_falta(error: FaltaJerarquia) -> str:
    detalle = "\n".join(f"  - parentId {pid}: {d['cantidad']} descripción(es), p. ej. {d['ejemplo']}" for pid, d in error.faltantes.items())
    return (
        "El CSV solo trae el id del padre de cada descripción, no su fondo/serie/subserie.\n"
        f"{detalle}\n\n"
        f"Completa las columnas fondo, serie y subserie en:\n  {error.plantilla}\n"
        "y vuelve a convertir indicando ese archivo como jerarquía."
    )


def ejecutar_cli(args) -> int:
    csv_ruta = Path(args.csv)
    salida = Path(args.salida) if args.salida else csv_ruta.parent / "salida_word"
    try:
        creados = convertir(csv_ruta, salida, args.jerarquia, args.nivel_archivo)
    except FaltaJerarquia as error:
        print(_mensaje_falta(error), file=sys.stderr)
        return 2
    except (OSError, ValueError) as error:
        print(f"No se pudo convertir: {error}", file=sys.stderr)
        return 1
    print(f"Listo: {len(creados)} documento(s) en {salida}")
    return 0


def ejecutar_gui() -> int:
    from .gui import abrir_ventana

    abrir_ventana()
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="csv-a-word", description="Convierte un CSV de AtoM en catálogos Word.")
    parser.add_argument("csv", nargs="?", help="CSV exportado desde AtoM (sin argumentos se abre la ventana)")
    parser.add_argument("-o", "--salida", help="carpeta de salida (por defecto, 'salida_word' junto al CSV)")
    parser.add_argument("-j", "--jerarquia", help="jerarquia.csv con fondo/serie/subserie por parentId")
    parser.add_argument("--nivel-archivo", type=int, help="nivel que da nombre al .docx (0 = primer nivel)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)
    return ejecutar_cli(args) if args.csv else ejecutar_gui()
