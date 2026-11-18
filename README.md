# csv-a-word

Convierte el CSV que exporta **AtoM** (Archivo Central del Cauca) en los catálogos Word del archivo.

## Qué genera

- Un `.docx` por fondo/sección, con el nombre en mayúsculas (p. ej. `INDEPENDENCIA.docx`).
- Un título de 3 líneas por cada cambio de subserie: **fondo**, **serie** y **subserie** (sin «Catálogo General»).
- Cada descripción numerada `-1-`, `-2-`… (la numeración reinicia en cada subserie) con los campos
  Signatura, Remitente, Destinatario, Contenido, Lugar de Procedencia, Fecha, Folios y Observaciones.
  Los campos que no vienen en el CSV no se escriben.

## Uso

```
pip install -r requirements.txt
python -m csv_a_word                                   # abre la ventana
python -m csv_a_word ejemplos/isad_ejemplo.csv -j ejemplos/jerarquia.csv -o salida_word
```

### Jerarquía (fondo / serie / subserie)

El CSV de AtoM solo trae el `parentId` de cada descripción. Si el CSV incluye también las filas de
fondo, serie y subserie (exportar «con descendientes»), los nombres se toman de ahí. Si no, el programa
crea `jerarquia_pendiente.csv` con cada `parentId` pendiente: complétalo (`fondo`, `serie`, `subserie` y,
si quieres, `archivo` = nombre del .docx) y pásalo con `-j`. Ver `ejemplos/jerarquia.csv`.

## Generar el .exe (Windows)

```
build_exe.bat
```

Crea `dist\csv-a-word.exe` (corre las pruebas antes). Para ver errores, quita `--windowed` del `.bat`.

## Pruebas

```
python -m unittest discover -s tests -t .
```
