"""Persistencia de las preferencias del usuario en un archivo JSON."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from ..config import CONDICIONES_DEFAULT, PREFIJO_FOLIO, VIGENCIA_DEFAULT
from ..models import Empresa

log = logging.getLogger(__name__)


@dataclass
class Preferencias:
    """Datos que la aplicación recuerda entre usos."""

    empresa: Empresa = field(default_factory=Empresa)
    siguiente_folio: int = 1
    vigencia: int = VIGENCIA_DEFAULT
    incluir_iva: bool = False
    condiciones: str = CONDICIONES_DEFAULT

    @property
    def folio_sugerido(self) -> str:
        return f"{PREFIJO_FOLIO}-{self.siguiente_folio:04d}"


class RepositorioPreferencias:
    """Lee y guarda `Preferencias` en disco. La ruta se inyecta para facilitar pruebas."""

    def __init__(self, ruta: Path):
        self.ruta = Path(ruta)

    def cargar(self) -> Preferencias:
        """Devuelve las preferencias guardadas o los valores por defecto si no hay archivo."""
        try:
            crudo = json.loads(self.ruta.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return Preferencias()
        except (OSError, ValueError) as err:
            log.warning("No se pudieron leer las preferencias (%s); se usan valores por defecto.", err)
            return Preferencias()

        campos_empresa = {f.name for f in fields(Empresa)}
        empresa = Empresa(**{k: str(v) for k, v in crudo.get("empresa", {}).items()
                             if k in campos_empresa})
        base = Preferencias()
        return Preferencias(
            empresa=empresa,
            siguiente_folio=_entero(crudo.get("siguiente_folio"), base.siguiente_folio),
            vigencia=_entero(crudo.get("vigencia"), base.vigencia),
            incluir_iva=bool(crudo.get("incluir_iva", crudo.get("iva", base.incluir_iva))),
            condiciones=str(crudo.get("condiciones", base.condiciones)),
        )

    def guardar(self, preferencias: Preferencias) -> None:
        """Guarda las preferencias. Un fallo aquí no es crítico: sólo se registra."""
        try:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            self.ruta.write_text(json.dumps(asdict(preferencias), ensure_ascii=False, indent=2),
                                 encoding="utf-8")
        except OSError as err:
            log.warning("No se pudieron guardar las preferencias: %s", err)


def _entero(valor, por_defecto: int) -> int:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return por_defecto
