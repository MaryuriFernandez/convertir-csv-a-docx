"""Ventana sencilla (tkinter, incluido con Python) para quien no use la terminal."""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext

from . import __version__
from .app import _mensaje_falta
from .conversor import convertir
from .jerarquia import FaltaJerarquia


def abrir_ventana() -> None:
    raiz = tk.Tk()
    raiz.title(f"CSV a Word · Archivo Central del Cauca  v{__version__}")
    raiz.geometry("640x420")

    rutas = {"csv": tk.StringVar(), "jerarquia": tk.StringVar(), "salida": tk.StringVar()}

    def fila(fila_n, texto, clave, es_carpeta=False, tipos=(("CSV", "*.csv"), ("Todos", "*.*"))):
        tk.Label(raiz, text=texto, anchor="w").grid(row=fila_n, column=0, sticky="w", padx=10, pady=6)
        tk.Entry(raiz, textvariable=rutas[clave], width=52).grid(row=fila_n, column=1, padx=4)

        def elegir():
            ruta = filedialog.askdirectory() if es_carpeta else filedialog.askopenfilename(filetypes=tipos)
            if ruta:
                rutas[clave].set(ruta)

        tk.Button(raiz, text="Examinar…", command=elegir).grid(row=fila_n, column=2, padx=10)

    fila(0, "CSV de AtoM:", "csv")
    fila(1, "Jerarquía (opcional):", "jerarquia")
    fila(2, "Carpeta de salida:", "salida", es_carpeta=True)

    registro = scrolledtext.ScrolledText(raiz, height=14, state="disabled")
    registro.grid(row=4, column=0, columnspan=3, padx=10, pady=8, sticky="nsew")

    def escribir(texto):
        registro.configure(state="normal")
        registro.insert("end", texto + "\n")
        registro.configure(state="disabled")
        raiz.update_idletasks()

    def convertir_ahora():
        if not rutas["csv"].get():
            messagebox.showwarning("Falta el CSV", "Elige primero el CSV exportado desde AtoM.")
            return
        salida = rutas["salida"].get() or str(Path(rutas["csv"].get()).parent / "salida_word")
        try:
            creados = convertir(rutas["csv"].get(), salida, rutas["jerarquia"].get() or None, avisar=escribir)
        except FaltaJerarquia as error:
            escribir(_mensaje_falta(error))
            messagebox.showwarning("Falta la jerarquía", "Revisa el detalle en la ventana.")
            return
        except Exception as error:  # noqa: BLE001 - se muestra al usuario, no debe cerrar la ventana
            messagebox.showerror("No se pudo convertir", str(error))
            return
        escribir(f"Listo: {len(creados)} documento(s) en {salida}")

    tk.Button(raiz, text="Convertir a Word", command=convertir_ahora, width=22).grid(row=3, column=1, pady=6)
    raiz.grid_rowconfigure(4, weight=1)
    raiz.grid_columnconfigure(1, weight=1)
    raiz.mainloop()
