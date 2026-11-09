"""Reglas de negocio: cálculo del precio de la ventana (funciones puras)."""

from __future__ import annotations

from .config import ALTO_DEFAULT, ANCHO_DEFAULT, PERFILES_DEFAULT
from .models import (Catalogo, DatosCotizacion, ModoMargen, Perfil, PerfilCatalogo,
                     ResultadoCotizacion)


def catalogo_de_fabrica() -> Catalogo:
    """Catálogo con los precios y fórmulas originales definidos en config.py."""
    return Catalogo([PerfilCatalogo(nombre, precio, veces_alto, veces_ancho)
                     for nombre, precio, veces_alto, veces_ancho in PERFILES_DEFAULT])


def validar_medidas(ancho: float, alto: float) -> None:
    """Lanza ValueError si las medidas de la ventana no son positivas."""
    if ancho <= 0 or alto <= 0:
        raise ValueError("El ancho y el alto de la ventana deben ser mayores a cero.")


def perfil_desde_catalogo(item: PerfilCatalogo, ancho: float, alto: float) -> Perfil:
    """Perfil de cotización: metros según la fórmula del catálogo y su precio fijo."""
    return Perfil(item.nombre, item.metros(alto=alto, ancho=ancho), item.precio_metro)


def armar_datos(items: list[PerfilCatalogo], ancho: float, alto: float, **otros) -> DatosCotizacion:
    """Cotización con los perfiles indicados calculados para las medidas dadas."""
    validar_medidas(ancho, alto)
    return DatosCotizacion(perfiles=[perfil_desde_catalogo(i, ancho, alto) for i in items],
                           ancho=ancho, alto=alto, **otros)


def datos_por_defecto(catalogo: Catalogo | None = None) -> DatosCotizacion:
    """Cotización inicial: todos los perfiles del catálogo con las medidas por defecto."""
    catalogo = catalogo or catalogo_de_fabrica()
    return armar_datos(catalogo.perfiles, ANCHO_DEFAULT, ALTO_DEFAULT)


def calcular_cotizacion(datos: DatosCotizacion) -> ResultadoCotizacion:
    """
    Calcula el precio de la ventana.

    - Subtotal Aluminio = Σ (metros × precio por metro) de cada perfil
    - Subtotal Vidrio   = área × precio/m²
    - Costo Base        = aluminio + vidrio + herrajes
    - Encadenado: Etapa 1 = Base × (1 + M1%),  Etapa 2 = Etapa 1 × (1 + M2%)
    - Global:     Etapa 2 = Base × (1 + M1% + M2%)
    """
    subtotal_aluminio = sum(p.costo for p in datos.perfiles)
    subtotal_vidrio = datos.vidrio_area * datos.vidrio_precio_m2
    costo_base = subtotal_aluminio + subtotal_vidrio + datos.herrajes

    monto_margen1 = costo_base * datos.margen1_pct / 100.0
    etapa1 = costo_base + monto_margen1

    base_margen2 = costo_base if datos.modo_margen is ModoMargen.GLOBAL else etapa1
    monto_margen2 = base_margen2 * datos.margen2_pct / 100.0

    return ResultadoCotizacion(
        subtotal_aluminio=subtotal_aluminio,
        subtotal_vidrio=subtotal_vidrio,
        subtotal_herrajes=datos.herrajes,
        costo_base=costo_base,
        monto_margen1=monto_margen1,
        etapa1=etapa1,
        monto_margen2=monto_margen2,
        etapa2=etapa1 + monto_margen2,
    )


def describir_materiales(datos: DatosCotizacion) -> str:
    """
    Texto para el cliente con lo que incluye la ventana (sin costos), p. ej.:
    'Perfiles de aluminio (Jamba, Riel), vidrio (1.8 m²) y herrajes.'
    """
    partes: list[str] = []
    if datos.perfiles:
        partes.append(f"perfiles de aluminio ({', '.join(p.nombre for p in datos.perfiles)})")
    if datos.vidrio_area > 0:
        partes.append(f"vidrio ({datos.vidrio_area:g} m²)")
    if datos.herrajes > 0:
        partes.append("herrajes")
    if not partes:
        return ""
    texto = partes[0] if len(partes) == 1 else f"{', '.join(partes[:-1])} y {partes[-1]}"
    return texto[0].upper() + texto[1:] + "."
