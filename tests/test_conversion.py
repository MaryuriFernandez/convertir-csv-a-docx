import tempfile
import unittest
from pathlib import Path

from docx import Document

from csv_a_word.conversor import convertir
from csv_a_word.descripcion import extraer_campos
from csv_a_word.jerarquia import FaltaJerarquia, armar_ubicacion

EJEMPLOS = Path(__file__).resolve().parent.parent / "ejemplos"


def textos(ruta):
    return [p.text for p in Document(ruta).paragraphs]


class CamposTest(unittest.TestCase):
    def test_remitente_y_destinatario_por_tipo_de_evento(self):
        fila = {
            "referenceCode": "1 (X)",
            "eventTypes": "Remitente|Destinatario",
            "eventActors": "Ana.|Luis.",
            "eventDates": "1820.|1820.",
        }
        campos = dict(extraer_campos(fila))
        self.assertEqual(campos["Remitente"], "Ana.")
        self.assertEqual(campos["Destinatario"], "Luis.")
        self.assertEqual(campos["Fecha"], "1820.")  # fecha repetida: aparece una sola vez

    def test_varios_remitentes_se_unen_con_coma(self):
        fila = {"eventTypes": "Remitente|Remitente", "eventActors": "Pedro Tobar.|Antonia Olave."}
        self.assertEqual(dict(extraer_campos(fila))["Remitente"], "Pedro Tobar, Antonia Olave.")

    def test_campos_vacios_o_null_se_omiten(self):
        fila = {"referenceCode": "1 (X)", "generalNote": "", "extentAndMedium": "NULL", "eventPlaces": "NULL|NULL"}
        self.assertEqual([e for e, _ in extraer_campos(fila)], ["Signatura"])

    def test_orden_de_campos(self):
        fila = {
            "referenceCode": "1", "scopeAndContent": "c", "placeAccessPoints": "p", "eventDates": "f",
            "extentAndMedium": "3", "generalNote": "o", "eventTypes": "Remitente", "eventActors": "r",
        }
        self.assertEqual(
            [e for e, _ in extraer_campos(fila)],
            ["Signatura", "Remitente", "Contenido", "Lugar de Procedencia", "Fecha", "Folios", "Observaciones"],
        )


class UbicacionTest(unittest.TestCase):
    def test_titulo_en_tres_lineas_y_nombre_de_archivo(self):
        u = armar_ubicacion(["Archivo Central del Cauca", "Independencia", "Civil", "Minas"])
        self.assertEqual(u.lineas, ("ARCHIVO CENTRAL DEL CAUCA", "CIVIL", "Minas"))
        self.assertEqual(u.archivo, "INDEPENDENCIA")


class ConversionTest(unittest.TestCase):
    def test_ejemplo_genera_un_docx_con_titulo_y_numeracion(self):
        with tempfile.TemporaryDirectory() as tmp:
            creados = convertir(EJEMPLOS / "isad_ejemplo.csv", tmp, EJEMPLOS / "jerarquia.csv", avisar=lambda *_: None)
            self.assertEqual([c.name for c in creados], ["INDEPENDENCIA.docx"])
            lineas = textos(creados[0])
            self.assertNotIn("Catálogo General", lineas)
            self.assertEqual([l for l in lineas if l][:3], ["ARCHIVO CENTRAL DEL CAUCA", "CIVIL", "Minas"])
            numeros = [l for l in lineas if l.startswith("-") and l.endswith("-") and len(l) > 2]
            self.assertEqual(numeros, [f"-{i}-" for i in range(1, 7)])

    def test_sin_jerarquia_pide_plantilla(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FaltaJerarquia) as ctx:
                convertir(EJEMPLOS / "isad_ejemplo.csv", tmp, avisar=lambda *_: None)
            self.assertIn("455", ctx.exception.faltantes)
            self.assertTrue(ctx.exception.plantilla.exists())


if __name__ == "__main__":
    unittest.main()


class SeccionesPorFondoTest(unittest.TestCase):
    """CSV con filas padre (sin levelOfDescription, como a veces exporta AtoM) y dos fondos."""

    @staticmethod
    def _csv(carpeta):
        cabecera = "legacyId,parentId,qubitParentSlug,title,levelOfDescription,referenceCode,scopeAndContent,slug\n"
        filas = [
            "1,,,Fondo A,,,,fa", "2,1,,Independencia,,,,ia", "3,2,,Civil,,,,ca", "4,3,,Minas,,,,ma",
            "5,4,,Doc A1,,A1,uno,d1", "6,4,,Doc A2,,A2,dos,d2",
            "10,,,Fondo B,,,,fb", "11,10,,Independencia,,,,ib", "12,11,,Civil,,,,cb", "13,12,,Minas,,,,mb",
            "14,13,,Doc B1,,B1,tres,d3",
        ]
        ruta = Path(carpeta) / "e.csv"
        ruta.write_text(cabecera + "\n".join(filas) + "\n", encoding="utf-8")
        return ruta

    def test_misma_seccion_en_dos_fondos_genera_dos_docx(self):
        with tempfile.TemporaryDirectory() as tmp:
            creados = convertir(self._csv(tmp), Path(tmp) / "out", avisar=lambda *_: None)
            self.assertEqual(sorted(c.name for c in creados), ["INDEPENDENCIA - FONDO A.docx", "INDEPENDENCIA - FONDO B.docx"])
            a = textos(next(c for c in creados if "FONDO A" in c.name))
            self.assertEqual([l for l in a if l][:3], ["FONDO A", "CIVIL", "Minas"])
            self.assertEqual([l for l in a if l.startswith("-") and len(l) > 2], ["-1-", "-2-"])
