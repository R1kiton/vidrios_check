"""Caso de uso: emitir una cotización (generar el PDF y actualizar preferencias)."""

from __future__ import annotations

from pathlib import Path

from ..formato import nombre_archivo_seguro
from ..models import DocumentoCotizacion
from .pdf import generar_pdf
from .preferencias import Preferencias, RepositorioPreferencias


class ServicioCotizaciones:
    """Coordina la generación de PDFs y la persistencia de preferencias."""

    def __init__(self, repositorio: RepositorioPreferencias, carpeta_salida: Path):
        self.repositorio = repositorio
        self.carpeta_salida = Path(carpeta_salida)

    def cargar_preferencias(self) -> Preferencias:
        return self.repositorio.cargar()

    def ruta_para(self, documento: DocumentoCotizacion) -> Path:
        """Ruta del PDF, p. ej. 'Cotizaciones/COT-0001 - Juan Pérez.pdf'."""
        nombre = (f"{nombre_archivo_seguro(documento.folio)} - "
                  f"{nombre_archivo_seguro(documento.cliente.nombre)}.pdf")
        return self.carpeta_salida / nombre

    def emitir(self, documento: DocumentoCotizacion, preferencias: Preferencias,
               consumir_folio: bool) -> Path:
        """
        Genera el PDF y guarda los datos a recordar (empresa, vigencia, IVA, condiciones).
        Si `consumir_folio` es True, avanza el consecutivo de folios.

        Lanza PermissionError si el PDF está abierto en otro programa.
        """
        ruta = generar_pdf(documento, self.ruta_para(documento))

        preferencias.empresa = documento.empresa
        preferencias.vigencia = documento.vigencia_dias
        preferencias.incluir_iva = documento.incluir_iva
        preferencias.condiciones = "\n".join(documento.condiciones)
        if consumir_folio:
            preferencias.siguiente_folio += 1
        self.repositorio.guardar(preferencias)
        return ruta
