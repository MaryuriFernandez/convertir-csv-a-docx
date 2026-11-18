"""Lanzador para PyInstaller (usa imports absolutos del paquete)."""

import sys

from csv_a_word.app import main

if __name__ == "__main__":
    sys.exit(main())
