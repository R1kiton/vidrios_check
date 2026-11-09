"""Ventana principal: une los paneles con la lógica de cálculo y los servicios."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

from ..calculos import calcular_cotizacion, datos_por_defecto
from ..config import APP_TITLE
from ..models import Catalogo, DatosCotizacion, ResultadoCotizacion
from ..services.catalogo import RepositorioCatalogo
from ..services.cotizaciones import ServicioCotizaciones
from ..services.preferencias import RepositorioPreferencias
from ..services.rutas import carpeta_cotizaciones, ruta_catalogo, ruta_preferencias
from .dialogo_impresion import DialogoImpresion
from .dialogo_precios import DialogoPrecios
from .panel_entrada import PanelEntrada
from .panel_resumen import PanelResumen
from .tema import TEMA_INICIAL, TEMAS, fuente


class App(ctk.CTk):
    """Ventana principal del cotizador."""

    def __init__(self, servicio: ServicioCotizaciones, repo_catalogo: RepositorioCatalogo):
        super().__init__()
        self.servicio = servicio
        self.repo_catalogo = repo_catalogo
        self.catalogo = repo_catalogo.cargar()
        self._ultimo: tuple[DatosCotizacion, ResultadoCotizacion] | None = None

        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(900, 560)
        self.after(0, lambda: self.state("zoomed"))  # maximizada en Windows

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        self._crear_encabezado()
        self.panel_entrada = PanelEntrada(self, self.catalogo,
                                          on_modificar_precios=self.modificar_precios)
        self.panel_entrada.grid(row=1, column=0, padx=(16, 8), pady=16, sticky="nsew")
        self.panel_resumen = PanelResumen(self, on_calcular=self.calcular,
                                          on_restablecer=self.restablecer,
                                          on_imprimir=self.imprimir)
        self.panel_resumen.grid(row=1, column=1, padx=(8, 16), pady=16, sticky="nsew")

        self.restablecer(confirmar=False)
        self.bind("<Return>", lambda _e: self.calcular())
        self.bind("<F5>", lambda _e: self.calcular())

    def _crear_encabezado(self) -> None:
        header = ctk.CTkFrame(self, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(header, text="🪟  " + APP_TITLE, font=fuente(22, negrita=True)).grid(
            row=0, column=0, padx=20, pady=14, sticky="w")
        ctk.CTkLabel(header, text="Tema:").grid(row=0, column=2, padx=(0, 6))
        selector = ctk.CTkSegmentedButton(
            header, values=list(TEMAS),
            command=lambda nombre: ctk.set_appearance_mode(TEMAS[nombre]))
        selector.set(TEMA_INICIAL)
        selector.grid(row=0, column=3, padx=(0, 20))

    # ----- Acciones -------------------------------------------------------

    def calcular(self) -> bool:
        """Lee el formulario, calcula y muestra el resultado. Devuelve True si tuvo éxito."""
        self.panel_entrada.actualizar_perfiles()
        try:
            datos = self.panel_entrada.leer()
        except ValueError as err:
            self._ultimo = None
            self.panel_resumen.mostrar_error(str(err))
            return False
        resultado = calcular_cotizacion(datos)
        self._ultimo = (datos, resultado)
        self.panel_resumen.mostrar(datos, resultado)
        return True

    def restablecer(self, confirmar: bool = True) -> None:
        if confirmar and not messagebox.askyesno(
                "Restablecer valores",
                "¿Deseas restablecer todos los valores por defecto?\n"
                "Se perderán los cambios actuales."):
            return
        self.panel_entrada.cargar(datos_por_defecto(self.catalogo))
        self.calcular()

    def modificar_precios(self) -> None:
        DialogoPrecios(self, self.catalogo, on_guardar=self._guardar_catalogo)

    def _guardar_catalogo(self, catalogo: Catalogo, renombres: dict[str, str]) -> bool:
        """Guarda el catálogo en disco y lo aplica a la cotización actual."""
        try:
            self.repo_catalogo.guardar(catalogo)
        except (OSError, ValueError) as err:
            messagebox.showerror("No se pudieron guardar los precios", str(err))
            return False
        self.catalogo = catalogo
        self.panel_entrada.aplicar_catalogo(catalogo, renombres)
        if self.calcular():
            self.panel_resumen.mostrar_estado("✔ Precios actualizados y guardados.")
        return True

    def imprimir(self) -> None:
        if not self.calcular() or self._ultimo is None:
            messagebox.showwarning("Datos inválidos",
                                   "Corrige los datos marcados antes de imprimir la cotización.")
            return
        datos, resultado = self._ultimo
        DialogoImpresion(self, datos, resultado, self.servicio,
                         on_estado=self.panel_resumen.mostrar_estado)


def run() -> None:
    """Arranca la aplicación con sus dependencias reales."""
    ctk.set_appearance_mode(TEMAS[TEMA_INICIAL])
    ctk.set_default_color_theme("blue")
    servicio = ServicioCotizaciones(RepositorioPreferencias(ruta_preferencias()),
                                    carpeta_cotizaciones())
    App(servicio, RepositorioCatalogo(ruta_catalogo())).mainloop()
