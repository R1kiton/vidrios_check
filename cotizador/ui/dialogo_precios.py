"""Ventana emergente para modificar de forma permanente el catálogo de precios de perfiles."""

from __future__ import annotations

from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from ..calculos import catalogo_de_fabrica
from ..formato import parse_numero
from ..models import Catalogo, PerfilCatalogo
from .tema import (COLOR_ERROR, COLOR_ERROR_HOVER, COLOR_TEXTO_SECUNDARIO, boton_principal,
                   boton_secundario, fuente)

# Callback de guardado: recibe el catálogo nuevo y {nombre anterior: nombre nuevo}.
# Devuelve True si se guardó correctamente.
OnGuardar = Callable[[Catalogo, dict[str, str]], bool]


class _FilaPrecio:
    """Fila editable del catálogo: nombre, precio por metro y fórmula (veces alto / ancho)."""

    def __init__(self, tabla, item: PerfilCatalogo, original: str | None,
                 on_eliminar: Callable[[_FilaPrecio], None]):
        self.original = original  # nombre con el que se cargó (None si es nuevo)
        self.e_nombre = ctk.CTkEntry(tabla, placeholder_text="Nombre del perfil")
        self.e_precio = ctk.CTkEntry(tabla, width=100, justify="right")
        self.e_alto = ctk.CTkEntry(tabla, width=70, justify="right")
        self.e_ancho = ctk.CTkEntry(tabla, width=70, justify="right")
        self.btn = ctk.CTkButton(tabla, text="✕", width=30, fg_color="transparent",
                                 border_width=1, text_color=COLOR_ERROR,
                                 hover_color=COLOR_ERROR_HOVER, command=lambda: on_eliminar(self))
        if item.nombre:
            self.e_nombre.insert(0, item.nombre)
        self.e_precio.insert(0, f"{item.precio_metro:.2f}")
        self.e_alto.insert(0, f"{item.veces_alto:g}")
        self.e_ancho.insert(0, f"{item.veces_ancho:g}")

    @property
    def _widgets(self):
        return (self.e_nombre, self.e_precio, self.e_alto, self.e_ancho, self.btn)

    def colocar(self, fila: int) -> None:
        for col, w in enumerate(self._widgets):
            w.grid(row=fila, column=col, padx=3, pady=3, sticky="ew" if col == 0 else "")

    def destruir(self) -> None:
        for w in self._widgets:
            w.destroy()

    def leer(self) -> PerfilCatalogo:
        nombre = self.e_nombre.get().strip()
        etiqueta = nombre or "perfil sin nombre"
        return PerfilCatalogo(
            nombre=nombre,
            precio_metro=parse_numero(self.e_precio.get(), f"Precio de {etiqueta}"),
            veces_alto=parse_numero(self.e_alto.get(), f"× Alto de {etiqueta}"),
            veces_ancho=parse_numero(self.e_ancho.get(), f"× Ancho de {etiqueta}"),
        )


class DialogoPrecios(ctk.CTkToplevel):
    """Ventana modal para editar los precios fijos y las fórmulas de los perfiles."""

    def __init__(self, master, catalogo: Catalogo, on_guardar: OnGuardar):
        super().__init__(master)
        self.on_guardar = on_guardar
        self.filas: list[_FilaPrecio] = []

        self.title("Precios y fórmulas de perfiles")
        alto = min(620, int(self.winfo_screenheight() / self._get_window_scaling()) - 140)
        self.geometry(f"660x{alto}+60+30")
        self.minsize(520, 380)
        self.transient(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text="Precios y fórmulas de perfiles", font=fuente(17, negrita=True)).grid(
            row=0, column=0, padx=18, pady=(14, 0), sticky="w")
        ctk.CTkLabel(self, justify="left", text_color=COLOR_TEXTO_SECUNDARIO,
                     text="Los cambios se guardan de forma permanente y se aplican a todas "
                          "las cotizaciones.\nMetros del perfil = (× Alto) · alto + "
                          "(× Ancho) · ancho.   Ej. Jamba: 2 × alto + 1 × ancho.").grid(row=1, column=0, padx=18, pady=(2, 6),
                                                       sticky="w")

        cuerpo = ctk.CTkScrollableFrame(self)
        cuerpo.grid(row=2, column=0, sticky="nsew", padx=12, pady=6)
        cuerpo.grid_columnconfigure(0, weight=1)
        self.tabla = ctk.CTkFrame(cuerpo, fg_color="transparent")
        self.tabla.grid(row=0, column=0, sticky="ew")
        self.tabla.grid_columnconfigure(0, weight=1)
        for col, texto in enumerate(("Perfil", "Precio / m ($)", "× Alto", "× Ancho", "")):
            ctk.CTkLabel(self.tabla, text=texto, text_color=COLOR_TEXTO_SECUNDARIO,
                         font=fuente(12, negrita=True)).grid(row=0, column=col, padx=3,
                                                             sticky="w" if col == 0 else "")
        ctk.CTkButton(cuerpo, text="＋  Nuevo perfil", width=150, command=self._nuevo).grid(
            row=1, column=0, pady=(6, 4), sticky="w")

        self._cargar(catalogo, conservar_originales=True)
        self._crear_botones()
        self.after(150, self._enfocar)

    # ----- Construcción ---------------------------------------------------

    def _crear_botones(self) -> None:
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=3, column=0, sticky="ew", padx=12, pady=12)
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

    # ----- Filas ----------------------------------------------------------

    def _cargar(self, catalogo: Catalogo, conservar_originales: bool) -> None:
        for fila in self.filas:
            fila.destruir()
        self.filas.clear()
        for item in catalogo.perfiles:
            self._agregar(item, item.nombre if conservar_originales else None)

    def _agregar(self, item: PerfilCatalogo, original: str | None) -> _FilaPrecio:
        fila = _FilaPrecio(self.tabla, item, original, on_eliminar=self._eliminar)
        self.filas.append(fila)
        fila.colocar(len(self.filas))
        return fila

    def _nuevo(self) -> None:
        self._agregar(PerfilCatalogo("", 0.0), original=None).e_nombre.focus_set()

    def _eliminar(self, fila: _FilaPrecio) -> None:
        fila.destruir()
        self.filas.remove(fila)
        for i, restante in enumerate(self.filas, start=1):
            restante.colocar(i)

    # ----- Acciones -------------------------------------------------------

    def _restaurar(self) -> None:
        if messagebox.askyesno("Restaurar de fábrica",
                               "¿Cargar los precios originales?\n"
                               "Se aplicarán hasta que presiones «Guardar precios».",
                               parent=self):
            self._cargar(catalogo_de_fabrica(), conservar_originales=False)

    def _guardar(self) -> None:
        try:
            catalogo = Catalogo([f.leer() for f in self.filas])
            catalogo.validar()
        except ValueError as err:
            messagebox.showwarning("Revisa los precios", str(err), parent=self)
            return
        renombres = {f.original: f.leer().nombre for f in self.filas
                     if f.original and f.original != f.leer().nombre}
        if self.on_guardar(catalogo, renombres):
            self.destroy()
