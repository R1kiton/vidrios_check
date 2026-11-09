"""Ubicaciones de archivos de la aplicación en el equipo del usuario."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from ..config import APP_ID

_CSIDL_PERSONAL = 5  # Carpeta "Documentos"


def carpeta_documentos() -> Path:
    """Carpeta 'Documentos' real del usuario (respeta la redirección a OneDrive)."""
    if sys.platform == "win32":
        try:
            import ctypes

            buf = ctypes.create_unicode_buffer(260)
            if ctypes.windll.shell32.SHGetFolderPathW(None, _CSIDL_PERSONAL, None, 0, buf) == 0:
                return Path(buf.value)
        except (OSError, AttributeError):
            pass
    return Path.home() / "Documents"


def carpeta_cotizaciones() -> Path:
    """Carpeta donde se guardan los PDF generados."""
    return carpeta_documentos() / "Cotizaciones"


def carpeta_datos() -> Path:
    """Carpeta de datos de la aplicación (%APPDATA%\\CotizadorVentanas)."""
    return Path(os.environ.get("APPDATA") or Path.home() / ".config") / APP_ID


def ruta_preferencias() -> Path:
    """Archivo JSON con los datos recordados (empresa, folio, condiciones…)."""
    return carpeta_datos() / "config.json"


def ruta_catalogo() -> Path:
    """Archivo JSON con los precios fijos de los perfiles."""
    return carpeta_datos() / "catalogo.json"
