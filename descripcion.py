"""Convierte una fila del CSV de AtoM en los campos de una descripción del catálogo."""

from .lector import limpiar

# Orden y nombre de los campos tal como aparecen en el catálogo (ver ejemplos/).
SIGNATURA = "Signatura"
REMITENTE = "Remitente"
DESTINATARIO = "Destinatario"
CONTENIDO = "Contenido"
LUGAR = "Lugar de Procedencia"
FECHA = "Fecha"
FOLIOS = "Folios"
OBSERVACIONES = "Observaciones"


def _lista(valor) -> list[str]:
    """Las columnas de eventos de AtoM vienen como listas separadas por '|'."""
    return [limpiar(parte) for parte in (valor or "").split("|")]


def _unicos(valores) -> list[str]:
    vistos, resultado = set(), []
    for valor in valores:
        if valor and valor not in vistos:
            vistos.add(valor)
            resultado.append(valor)
    return resultado


def _unir_personas(nombres: list[str]) -> str:
    """'Pedro Tobar.' + 'Antonia Olave.' -> 'Pedro Tobar, Antonia Olave.'"""
    if len(nombres) <= 1:
        return "".join(nombres)
    return ", ".join(n.rstrip(".") for n in nombres[:-1]) + ", " + nombres[-1]


def _actores_por_tipo(fila: dict, tipo: str) -> str:
    tipos = [t.lower() for t in _lista(fila.get("eventTypes"))]
    actores = _lista(fila.get("eventActors"))
    elegidos = [a for t, a in zip(tipos, actores) if t == tipo.lower() and a]
    return _unir_personas(_unicos(elegidos))


def extraer_campos(fila: dict) -> list[tuple[str, str]]:
    """Devuelve [(etiqueta, valor)] en el orden del catálogo; omite los campos vacíos."""
    signatura = limpiar(fila.get("referenceCode")) or limpiar(fila.get("identifier"))
    lugar = limpiar(fila.get("placeAccessPoints")) or ", ".join(_unicos(_lista(fila.get("eventPlaces"))))
    fecha = "; ".join(_unicos(_lista(fila.get("eventDates"))))

    campos = [
        (SIGNATURA, signatura),
        (REMITENTE, _actores_por_tipo(fila, "Remitente")),
        (DESTINATARIO, _actores_por_tipo(fila, "Destinatario")),
        (CONTENIDO, limpiar(fila.get("scopeAndContent"))),
        (LUGAR, lugar),
        (FECHA, fecha),
        (FOLIOS, limpiar(fila.get("extentAndMedium"))),
        (OBSERVACIONES, limpiar(fila.get("generalNote"))),
    ]
    return [(etiqueta, valor) for etiqueta, valor in campos if valor]
