"""
Registro de errores en archivo.

El .exe se compila sin consola (--noconsole), así que sin esto cualquier error
desaparecería sin dejar rastro. Todo queda en %APPDATA%\\CotizadorVentanas\\errores.log.
"""

from __future__ import annotations

import faulthandler
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .rutas import carpeta_datos

log = logging.getLogger("cotizador")
_archivo_fallos = None  # se mantiene abierto: faulthandler escribe ahí si Python se cae


def ruta_registro() -> Path:
    return carpeta_datos() / "errores.log"


def configurar_registro() -> Path:
    """Envía logs, excepciones no atrapadas y caídas graves al archivo de registro."""
    global _archivo_fallos
    ruta = ruta_registro()
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        manejador = RotatingFileHandler(ruta, maxBytes=500_000, backupCount=2, encoding="utf-8")
    except OSError:
        return ruta  # sin permisos de escritura: la app funciona igual, sólo sin registro
    manejador.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[manejador], force=True)

    sys.excepthook = lambda tipo, valor, tb: log.critical("Error no atrapado",
                                                          exc_info=(tipo, valor, tb))
    try:
        _archivo_fallos = open(ruta.with_name("fallos_graves.log"), "a", encoding="utf-8")
        faulthandler.enable(_archivo_fallos)
    except OSError:
        pass
    return ruta
