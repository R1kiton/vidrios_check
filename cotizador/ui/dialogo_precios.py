"""
Ventana emergente para modificar de forma permanente el precio por metro de cada perfil.

Sólo se edita el precio: el nombre y la fórmula de metros de cada perfil son fijos.
"""

from __future__ import annotations

from dataclasses import replace
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from ..calculos import catalogo_de_fabrica
from ..formato import parse_numero
from ..models import Catalogo, PerfilCatalogo
from .tema import COLOR_TEXTO_SECUNDARIO, boton_principal, boton_secundario, fuente

# Recibe el catálogo con los precios nuevos; devuelve True si se guardó correctamente.
OnGuardar = Callable[[Catalogo], bool]


class _FilaPrecio:
    """Nombre del perfil (fijo) y su precio por metro (editable)."""

    def __init__(self, tabla, fila: int, item: PerfilCatalogo):
        self.item = item
        ctk.CTkLabel(tabla, text=item.nombre, anchor="w", font=fuente(14)).grid(
            row=fila, column=0, padx=(4, 10), pady=2, sticky="w")
        ctk.CTkLabel(tabla, text="$", text_color=COLOR_TEXTO_SECUNDARIO).grid(
            row=fila, column=1, padx=(0, 4), pady=2, sticky="e")
        self.e_precio = ctk.CTkEntry(tabla, width=110, height=28, justify="right")
        self.e_precio.grid(row=fila, column=2, pady=2, sticky="e")
        ctk.CTkLabel(tabla, text="por metro", text_color=COLOR_TEXTO_SECUNDARIO).grid(
            row=fila, column=3, padx=(6, 4), pady=2, sticky="w")
        self.poner_precio(item.precio_metro)

    def poner_precio(self, precio: float) -> None:
        self.e_precio.delete(0, "end")
        self.e_precio.insert(0, f"{precio:.2f}")

    def leer(self) -> PerfilCatalogo:
        """Mismo perfil (nombre y fórmula intactos) con el precio capturado."""
        precio = parse_numero(self.e_precio.get(), f"Precio de {self.item.nombre}")
        return replace(self.item, precio_metro=precio)


class DialogoPrecios(ctk.CTkToplevel):
    """Ventana modal para editar los precios fijos de los perfiles."""

    def __init__(self, master, catalogo: Catalogo, on_guardar: OnGuardar):
        super().__init__(master)
        self.on_guardar = on_guardar

        self.title("Precios de perfiles")
        alto = min(560, int(self.winfo_screenheight() / self._get_window_scaling()) - 110)
        self.geometry(f"500x{alto}+60+30")
        self.minsize(400, 360)
        self.transient(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Precios de perfiles", font=fuente(17, negrita=True)).grid(
            row=0, column=0, padx=18, pady=(14, 0), sticky="w")
        ctk.CTkLabel(self, justify="left", text_color=COLOR_TEXTO_SECUNDARIO,
                     text="Se guardan de forma permanente para todas las cotizaciones.").grid(
            row=1, column=0, padx=18, pady=(2, 6), sticky="w")

        cuerpo = ctk.CTkScrollableFrame(self, height=330)
        cuerpo.grid(row=2, column=0, sticky="nsew", padx=12, pady=6)
        cuerpo.grid_columnconfigure(0, weight=1)
        tabla = ctk.CTkFrame(cuerpo, fg_color="transparent")
        tabla.grid(row=0, column=0, sticky="ew", padx=4)
        tabla.grid_columnconfigure(0, weight=1)
        self.filas = [_FilaPrecio(tabla, i, item) for i, item in enumerate(catalogo.perfiles)]

        self._crear_botones()
        self.after(150, self._enfocar)

    def _crear_botones(self) -> None:
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=3, column=0, sticky="ew", padx=12, pady=(4, 10))
        barra.grid_columnconfigure((0, 1, 2), weight=1)
        boton_secundario(barra, "Restaurar de fábrica", self._restaurar).grid(
            row=0, column=0, padx=4, sticky="ew")
        boton_secundario(barra, "Cancelar", self.destroy).grid(row=0, column=1, padx=4, sticky="ew")
        boton_principal(barra, "Guardar precios", self._guardar,
                        font=fuente(14, negrita=True)).grid(row=0, column=2, padx=4, sticky="ew")

    def _enfocar(self) -> None:
        self.lift()
        self.focus_force()
        self.grab_set()
        if self.filas:
            self.filas[0].e_precio.focus_set()

    # ----- Acciones -------------------------------------------------------

    def _restaurar(self) -> None:
        if not messagebox.askyesno("Restaurar de fábrica",
                                   "¿Cargar los precios originales?\n"
                                   "Se aplicarán hasta que presiones «Guardar precios».",
                                   parent=self):
            return
        fabrica = catalogo_de_fabrica()
        for fila in self.filas:
            original = fabrica.buscar(fila.item.nombre)
            if original:
                fila.poner_precio(original.precio_metro)

    def _guardar(self) -> None:
        try:
            catalogo = Catalogo([f.leer() for f in self.filas])
            catalogo.validar()
        except ValueError as err:
            messagebox.showwarning("Revisa los precios", str(err), parent=self)
            return
        if self.on_guardar(catalogo):
            self.destroy()
