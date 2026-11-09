"""Persistencia del catálogo de precios de perfiles en un archivo JSON."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path

from ..calculos import catalogo_de_fabrica
from ..models import Catalogo, PerfilCatalogo

log = logging.getLogger(__name__)


class RepositorioCatalogo:
    """Lee y guarda el `Catalogo`. La ruta se inyecta para facilitar pruebas."""

    def __init__(self, ruta: Path):
        self.ruta = Path(ruta)

    def cargar(self) -> Catalogo:
        """Devuelve el catálogo guardado, o el de fábrica si no existe o está dañado."""
        try:
            crudo = json.loads(self.ruta.read_text(encoding="utf-8"))
            catalogo = Catalogo([_perfil_desde_json(p) for p in crudo["perfiles"]])
            catalogo.validar()
            return catalogo
        except FileNotFoundError:
            return catalogo_de_fabrica()
        except (OSError, ValueError, KeyError, TypeError) as err:
            log.warning("Catálogo inválido (%s); se usan los precios de fábrica.", err)
            return catalogo_de_fabrica()

    def guardar(self, catalogo: Catalogo) -> None:
        """
        Valida y guarda el catálogo. A diferencia de las preferencias, aquí un fallo
        sí se propaga (OSError/ValueError): el usuario debe saber si sus precios no se guardaron.
        """
        catalogo.validar()
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = self.ruta.with_suffix(".tmp")
        temporal.write_text(json.dumps(asdict(catalogo), ensure_ascii=False, indent=2),
                            encoding="utf-8")
        temporal.replace(self.ruta)  # escritura atómica: nunca queda un archivo a medias


def _perfil_desde_json(dato: dict) -> PerfilCatalogo:
    """
    Convierte un registro del JSON. Los catálogos de versiones anteriores no tenían
    fórmula: en ese caso se toma la de fábrica del perfil con el mismo nombre (o 0).
    """
    nombre = str(dato["nombre"])
    fabrica = catalogo_de_fabrica().buscar(nombre)
    return PerfilCatalogo(
        nombre=nombre,
        precio_metro=float(dato["precio_metro"]),
        veces_alto=float(dato.get("veces_alto", fabrica.veces_alto if fabrica else 0.0)),
        veces_ancho=float(dato.get("veces_ancho", fabrica.veces_ancho if fabrica else 0.0)),
    )
