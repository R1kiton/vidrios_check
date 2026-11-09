"""Integración con el sistema operativo: abrir e imprimir archivos."""

from __future__ import annotations

import os
import sys
import webbrowser
from pathlib import Path


def abrir_archivo(ruta: Path) -> None:
    """Abre el archivo con el programa predeterminado."""
    if sys.platform == "win32":
        os.startfile(ruta)  # type: ignore[attr-defined]
    else:
        webbrowser.open(Path(ruta).resolve().as_uri())


def imprimir_archivo(ruta: Path) -> bool:
    """
    Envía el archivo a la impresora predeterminada.

    Devuelve True si se envió directamente. Si el visor de PDF no admite impresión
    directa, abre el archivo (para imprimir con Ctrl+P) y devuelve False.
    """
    if sys.platform == "win32":
        try:
            os.startfile(ruta, "print")  # type: ignore[attr-defined]
            return True
        except OSError:
            pass
    abrir_archivo(ruta)
    return False
