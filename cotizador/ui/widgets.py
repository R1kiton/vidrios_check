"""Componentes reutilizables de la interfaz."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ..calculos import perfil_desde_catalogo
from ..formato import fmt_money, parse_numero
from ..models import Catalogo, Perfil
from .tema import COLOR_ERROR, COLOR_ERROR_HOVER, COLOR_TEXTO, COLOR_TEXTO_SECUNDARIO, fuente


class Seccion(ctk.CTkFrame):
    """Tarjeta con título y filas de 'etiqueta + campo'."""

    def __init__(self, master, titulo: str, ancho_etiqueta: int | None = None,
                 campos_expandidos: bool = False):
        super().__init__(master)
        self._fila = 1
        self._expandir = campos_expandidos
        self.grid_columnconfigure(1 if campos_expandidos else 0, weight=1)
        if ancho_etiqueta:
            self.grid_columnconfigure(0, minsize=self._apply_widget_scaling(ancho_etiqueta))
        ctk.CTkLabel(self, text=titulo, font=fuente(15, negrita=True)).grid(
            row=0, column=0, columnspan=2, padx=10, pady=(10, 6), sticky="w")

    def siguiente_fila(self) -> int:
        fila = self._fila
        self._fila += 1
        return fila

    def agregar_campo(self, etiqueta: str, valor: str = "", placeholder: str = "") -> ctk.CTkEntry:
        fila = self.siguiente_fila()
        ctk.CTkLabel(self, text=etiqueta).grid(row=fila, column=0, padx=10, pady=4, sticky="w")
        if self._expandir:
            entrada = ctk.CTkEntry(self, placeholder_text=placeholder or None)
            entrada.grid(row=fila, column=1, padx=10, pady=4, sticky="ew")
        else:
            entrada = ctk.CTkEntry(self, width=140, justify="right")
            entrada.grid(row=fila, column=1, padx=10, pady=4, sticky="e")
        if valor:
            entrada.insert(0, valor)
        return entrada

    def agregar_widget(self, widget, **grid) -> None:
        """Coloca un widget ocupando las dos columnas de la siguiente fila."""
        opciones = dict(padx=10, pady=4, sticky="w") | grid
        widget.grid(row=self.siguiente_fila(), column=0, columnspan=2, **opciones)


def poner_texto(entrada: ctk.CTkEntry, texto: str) -> None:
    entrada.delete(0, "end")
    entrada.insert(0, texto)


def _boton_eliminar(tabla, comando) -> ctk.CTkButton:
    return ctk.CTkButton(tabla, text="✕", width=30, fg_color="transparent", border_width=1,
                         text_color=COLOR_ERROR, hover_color=COLOR_ERROR_HOVER, command=comando)


class FilaPerfil:
    """
    Fila de un perfil del catálogo. Es de sólo lectura: los metros salen de la fórmula
    del catálogo y de las medidas de la ventana, y el precio por metro es fijo
    (se cambia desde "Modificar precios").
    """

    def __init__(self, tabla: ctk.CTkFrame, nombre: str,
                 on_eliminar: Callable[[FilaPerfil], None]):
        self.nombre = nombre
        self.lbl_nombre = ctk.CTkLabel(tabla, text=nombre, anchor="w")
        self.lbl_metros = ctk.CTkLabel(tabla, width=80, anchor="e")
        self.lbl_precio = ctk.CTkLabel(tabla, width=90, anchor="e", text_color=COLOR_TEXTO_SECUNDARIO)
        self.lbl_costo = ctk.CTkLabel(tabla, width=90, anchor="e")
        self.btn_eliminar = _boton_eliminar(tabla, lambda: on_eliminar(self))

    @property
    def _widgets(self):
        return (self.lbl_nombre, self.lbl_metros, self.lbl_precio, self.lbl_costo,
                self.btn_eliminar)

    def colocar(self, fila: int) -> None:
        for col, widget in enumerate(self._widgets):
            widget.grid(row=fila, column=col, padx=4, pady=3, sticky="ew" if col == 0 else "")

    def destruir(self) -> None:
        for widget in self._widgets:
            widget.destroy()

    def perfil(self, catalogo: Catalogo, ancho: float, alto: float) -> Perfil:
        """Perfil con los metros calculados. Lanza ValueError si ya no está en el catálogo."""
        item = catalogo.buscar(self.nombre)
        if item is None:
            raise ValueError(f"El perfil «{self.nombre}» ya no existe en el catálogo.")
        return perfil_desde_catalogo(item, ancho, alto)

    def refrescar(self, catalogo: Catalogo, medidas: tuple[float, float] | None) -> None:
        """Pinta la fila; `medidas` = (ancho, alto) o None si son inválidas."""
        item = catalogo.buscar(self.nombre)
        if item is None:
            return
        self.lbl_nombre.configure(text=item.nombre)
        self.lbl_precio.configure(text=fmt_money(item.precio_metro))
        if medidas is None:
            self.lbl_metros.configure(text="—")
            self.lbl_costo.configure(text="—", text_color=COLOR_ERROR)
            return
        perfil = perfil_desde_catalogo(item, *medidas)
        self.lbl_metros.configure(text=f"{perfil.metros:.2f} m")
        self.lbl_costo.configure(text=fmt_money(perfil.costo), text_color=COLOR_TEXTO)


class FilaPerfilManual:
    """
    Fila agregada a mano con "＋ Agregar perfil": empieza en blanco y el usuario
    escribe nombre, metros y precio por metro. Sólo vale para esta cotización.
    """

    def __init__(self, tabla: ctk.CTkFrame, on_eliminar: Callable[[FilaPerfilManual], None],
                 on_cambio: Callable[[], None], perfil: Perfil | None = None):
        self.e_nombre = ctk.CTkEntry(tabla, placeholder_text="Nombre del perfil")
        self.e_metros = ctk.CTkEntry(tabla, width=80, justify="right", placeholder_text="Metros")
        self.e_precio = ctk.CTkEntry(tabla, width=90, justify="right", placeholder_text="$ / m")
        self.lbl_costo = ctk.CTkLabel(tabla, text="—", width=90, anchor="e")
        self.btn_eliminar = _boton_eliminar(tabla, lambda: on_eliminar(self))
        if perfil:
            self.e_nombre.insert(0, perfil.nombre)
            self.e_metros.insert(0, f"{perfil.metros:.2f}")
            self.e_precio.insert(0, f"{perfil.precio_metro:.2f}")
        for entrada in (self.e_metros, self.e_precio):
            entrada.bind("<KeyRelease>", lambda _e: on_cambio())

    @property
    def nombre(self) -> str:
        return self.e_nombre.get().strip()

    @property
    def _widgets(self):
        return (self.e_nombre, self.e_metros, self.e_precio, self.lbl_costo, self.btn_eliminar)

    def colocar(self, fila: int) -> None:
        for col, widget in enumerate(self._widgets):
            widget.grid(row=fila, column=col, padx=4, pady=3, sticky="ew" if col == 0 else "")

    def destruir(self) -> None:
        for widget in self._widgets:
            widget.destroy()

    def perfil(self, catalogo: Catalogo, ancho: float, alto: float) -> Perfil:
        """Lee lo capturado. Lanza ValueError si falta algún dato."""
        if not self.nombre:
            raise ValueError("Escribe el nombre del perfil agregado.")
        return Perfil(self.nombre,
                      parse_numero(self.e_metros.get(), f"Metros de {self.nombre}"),
                      parse_numero(self.e_precio.get(), f"Precio de {self.nombre}"))

    def refrescar(self, catalogo: Catalogo, medidas: tuple[float, float] | None) -> None:
        try:
            costo = parse_numero(self.e_metros.get(), "m") * parse_numero(self.e_precio.get(), "p")
        except ValueError:
            self.lbl_costo.configure(text="—", text_color=COLOR_TEXTO_SECUNDARIO)
        else:
            self.lbl_costo.configure(text=fmt_money(costo), text_color=COLOR_TEXTO)
