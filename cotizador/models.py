"""Modelos de datos del dominio (sin dependencias de interfaz ni de archivos)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum

from .config import (ALTO_DEFAULT, ANCHO_DEFAULT, DESCRIPCION_DEFAULT, EMPRESA_NOMBRE_DEFAULT, HERRAJES_DEFAULT,
                     MARGEN1_DEFAULT, MARGEN2_DEFAULT, TASA_IVA, VIDRIO_AREA_DEFAULT,
                     VIDRIO_PRECIO_DEFAULT, VIGENCIA_DEFAULT)


class ModoMargen(str, Enum):
    """Forma de aplicar los dos márgenes de ganancia."""

    ENCADENADO = "Encadenado (Etapa 1 → Etapa 2)"
    GLOBAL = "Global (suma de porcentajes)"


# ---------------------------------------------------------------------------
# Catálogo de precios (fijos, se editan sólo desde "Modificar precios")
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PerfilCatalogo:
    """
    Perfil disponible con su precio fijo por metro y la fórmula de sus metros:
    metros = veces_alto × alto + veces_ancho × ancho.
    """

    nombre: str
    precio_metro: float
    veces_alto: float = 0.0
    veces_ancho: float = 0.0

    def metros(self, alto: float, ancho: float) -> float:
        return self.veces_alto * alto + self.veces_ancho * ancho

    @property
    def formula(self) -> str:
        """Texto legible, p. ej. '2 × alto + ancho'."""
        def termino(veces: float, medida: str) -> str:
            return "" if not veces else medida if veces == 1 else f"{veces:g} × {medida}"

        partes = [t for t in (termino(self.veces_alto, "alto"),
                              termino(self.veces_ancho, "ancho")) if t]
        return " + ".join(partes) or "—"


@dataclass
class Catalogo:
    """Lista de perfiles con precio fijo. Es la única fuente de precios de aluminio."""

    perfiles: list[PerfilCatalogo] = field(default_factory=list)

    @property
    def nombres(self) -> list[str]:
        return [p.nombre for p in self.perfiles]

    def buscar(self, nombre: str) -> PerfilCatalogo | None:
        return next((p for p in self.perfiles if p.nombre == nombre), None)

    def validar(self) -> None:
        """Lanza ValueError si hay nombres vacíos/repetidos o valores negativos."""
        if not self.perfiles:
            raise ValueError("El catálogo debe tener al menos un perfil.")
        vistos: set[str] = set()
        for p in self.perfiles:
            nombre = p.nombre.strip()
            if not nombre:
                raise ValueError("Todos los perfiles deben tener nombre.")
            if nombre.casefold() in vistos:
                raise ValueError(f"El perfil «{nombre}» está repetido.")
            vistos.add(nombre.casefold())
            if min(p.precio_metro, p.veces_alto, p.veces_ancho) < 0:
                raise ValueError(f"El perfil «{nombre}» tiene valores negativos.")


# ---------------------------------------------------------------------------
# Cálculo
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Perfil:
    """Un perfil de aluminio: su precio es metros × precio fijo por metro."""

    nombre: str
    metros: float
    precio_metro: float

    @property
    def costo(self) -> float:
        return self.metros * self.precio_metro


@dataclass
class DatosCotizacion:
    """Datos de entrada para calcular el precio de una ventana."""

    perfiles: list[Perfil] = field(default_factory=list)
    ancho: float = ANCHO_DEFAULT   # medidas de la ventana (m), de donde salen los metros
    alto: float = ALTO_DEFAULT
    vidrio_area: float = VIDRIO_AREA_DEFAULT
    vidrio_precio_m2: float = VIDRIO_PRECIO_DEFAULT
    herrajes: float = HERRAJES_DEFAULT
    margen1_pct: float = MARGEN1_DEFAULT
    margen2_pct: float = MARGEN2_DEFAULT
    modo_margen: ModoMargen = ModoMargen.ENCADENADO


@dataclass(frozen=True)
class ResultadoCotizacion:
    """Resultado desglosado del cálculo."""

    subtotal_aluminio: float
    subtotal_vidrio: float
    subtotal_herrajes: float
    costo_base: float
    monto_margen1: float
    etapa1: float
    monto_margen2: float
    etapa2: float

    @property
    def total(self) -> float:
        return self.etapa2

    @property
    def margen_total(self) -> float:
        return self.total - self.costo_base

    @property
    def margen_efectivo_pct(self) -> float:
        return self.margen_total / self.costo_base * 100.0 if self.costo_base else 0.0


# ---------------------------------------------------------------------------
# Documento impreso
# ---------------------------------------------------------------------------

@dataclass
class Empresa:
    """Datos de la empresa que emite la cotización."""

    nombre: str = EMPRESA_NOMBRE_DEFAULT
    direccion: str = ""
    telefono: str = ""
    correo: str = ""
    rfc: str = ""
    atiende: str = ""   # persona que firma
    logo: str = ""      # ruta a PNG/JPG (opcional)


@dataclass
class Cliente:
    nombre: str
    telefono: str = ""
    direccion: str = ""


@dataclass
class DocumentoCotizacion:
    """Todo lo necesario para imprimir una cotización formal."""

    empresa: Empresa
    cliente: Cliente
    folio: str
    precio_unitario: float
    cantidad: int = 1
    descripcion: str = DESCRIPCION_DEFAULT
    medidas: str = ""
    incluye: str = ""
    vigencia_dias: int = VIGENCIA_DEFAULT
    incluir_iva: bool = False
    condiciones: list[str] = field(default_factory=list)
    fecha: date = field(default_factory=date.today)

    @property
    def subtotal(self) -> float:
        return round(self.precio_unitario * self.cantidad, 2)

    @property
    def iva(self) -> float:
        return round(self.subtotal * TASA_IVA, 2) if self.incluir_iva else 0.0

    @property
    def total(self) -> float:
        return round(self.subtotal + self.iva, 2)

    @property
    def fecha_vencimiento(self) -> date:
        return self.fecha + timedelta(days=self.vigencia_dias)
