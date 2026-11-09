"""Panel izquierdo: medidas de la ventana, perfiles, vidrio, herrajes y márgenes."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ..calculos import validar_medidas
from ..formato import parse_medida, parse_numero
from ..models import Catalogo, DatosCotizacion, ModoMargen
from .dibujo_ventana import DibujoVentana
from .tema import COLOR_TEXTO_SECUNDARIO, boton_secundario, fuente
from .widgets import FilaPerfil, FilaPerfilManual, Seccion, poner_texto

ENCABEZADOS_TABLA = ("Perfil", "Metros", "Precio / m", "Precio pieza", "")

Fila = FilaPerfil | FilaPerfilManual


class PanelEntrada(ctk.CTkScrollableFrame):
    """Formulario de datos de la cotización."""

    def __init__(self, master, catalogo: Catalogo, on_modificar_precios: Callable[[], object]):
        super().__init__(master, label_text="Datos de la cotización",
                         label_font=fuente(15, negrita=True))
        self.grid_columnconfigure(0, weight=1)
        self.catalogo = catalogo
        self.filas: list[Fila] = []

        self._crear_medidas(fila=0)
        self._crear_perfiles(fila=1, on_modificar_precios=on_modificar_precios)
        self._crear_vidrio(fila=2)
        self._crear_herrajes(fila=3)
        self._crear_margenes(fila=4)

    # ----- Construcción ---------------------------------------------------

    def _seccion(self, fila: int, titulo: str) -> Seccion:
        seccion = Seccion(self, titulo)
        seccion.grid(row=fila, column=0, sticky="ew", padx=4, pady=6)
        return seccion

    def _crear_medidas(self, fila: int) -> None:
        sec = self._seccion(fila, "Medidas de la ventana")
        contenido = ctk.CTkFrame(sec, fg_color="transparent")
        sec.agregar_widget(contenido, sticky="ew", pady=(0, 10))
        contenido.grid_columnconfigure(1, weight=1)

        formulario = ctk.CTkFrame(contenido, fg_color="transparent")
        formulario.grid(row=0, column=0, sticky="n", padx=(0, 10))
        self.e_ancho = self._campo_medida(formulario, 0, "Ancho (m)")
        self.e_alto = self._campo_medida(formulario, 1, "Alto (m)")
        ctk.CTkLabel(formulario, text="Con estas medidas se calculan\nel aluminio y el vidrio.",
                     text_color=COLOR_TEXTO_SECUNDARIO, justify="left").grid(
            row=2, column=0, columnspan=2, pady=(10, 0), sticky="w")

        self.dibujo = DibujoVentana(contenido)
        self.dibujo.grid(row=0, column=1, sticky="nsew")

    def _campo_medida(self, master, fila: int, etiqueta: str) -> ctk.CTkEntry:
        ctk.CTkLabel(master, text=etiqueta, font=fuente(14, negrita=True)).grid(
            row=fila, column=0, padx=(0, 8), pady=5, sticky="w")
        entrada = ctk.CTkEntry(master, width=100, justify="right", font=fuente(15))
        entrada.grid(row=fila, column=1, pady=5)
        entrada.bind("<KeyRelease>", lambda _e: self.actualizar_perfiles())
        return entrada

    def _crear_perfiles(self, fila: int, on_modificar_precios) -> None:
        sec = self._seccion(fila, "Perfiles de aluminio")
        boton_secundario(sec, "⚙  Modificar precios", on_modificar_precios, width=170,
                         height=30, border_width=1).grid(row=0, column=1, padx=10, pady=(10, 6),
                                                         sticky="e")

        self.tabla = ctk.CTkFrame(sec, fg_color="transparent")
        sec.agregar_widget(self.tabla, sticky="ew")
        self.tabla.grid_columnconfigure(0, weight=1)
        for col, texto in enumerate(ENCABEZADOS_TABLA):
            ctk.CTkLabel(self.tabla, text=texto, text_color=COLOR_TEXTO_SECUNDARIO,
                         font=fuente(12, negrita=True)).grid(
                row=0, column=col, padx=4, sticky="w" if col == 0 else "")

        # Agrega una fila en blanco para capturar un perfil a mano
        sec.agregar_widget(ctk.CTkButton(sec, text="＋  Agregar perfil", width=150,
                                         command=self.agregar_perfil_manual), pady=(4, 12))

    def _crear_vidrio(self, fila: int) -> None:
        sec = self._seccion(fila, "Vidrio")
        fila_area = sec.siguiente_fila()
        ctk.CTkLabel(sec, text="Área (ancho × alto)").grid(
            row=fila_area, column=0, padx=10, pady=4, sticky="w")
        self.lbl_vidrio_area = ctk.CTkLabel(sec, text="—", font=fuente(14, negrita=True))
        self.lbl_vidrio_area.grid(row=fila_area, column=1, padx=10, pady=4, sticky="e")
        self.e_vidrio_precio = sec.agregar_campo("Precio por m² ($)")

    def _crear_herrajes(self, fila: int) -> None:
        sec = self._seccion(fila, "Herrajes")
        self.e_herrajes = sec.agregar_campo("Costo total fijo ($)")

    def _crear_margenes(self, fila: int) -> None:
        sec = self._seccion(fila, "Márgenes de ganancia")
        self.e_margen1 = sec.agregar_campo("Margen 1 – Ganancia base (%)")
        self.e_margen2 = sec.agregar_campo("Margen 2 – Gasto / secundario (%)")
        fila_modo = sec.siguiente_fila()
        ctk.CTkLabel(sec, text="Forma de aplicar").grid(
            row=fila_modo, column=0, padx=10, pady=(4, 12), sticky="w")
        self.cb_modo_margen = ctk.CTkOptionMenu(sec, values=[m.value for m in ModoMargen], width=260)
        self.cb_modo_margen.grid(row=fila_modo, column=1, padx=10, pady=(4, 12), sticky="e")

    # ----- Medidas y perfiles ---------------------------------------------

    def _leer_medidas(self) -> tuple[float, float]:
        """Devuelve (ancho, alto). Lanza ValueError si no son válidas."""
        ancho = parse_medida(self.e_ancho.get(), "Ancho")
        alto = parse_medida(self.e_alto.get(), "Alto")
        validar_medidas(ancho, alto)
        return ancho, alto

    def actualizar_perfiles(self) -> None:
        """Redibuja la ventana y recalcula metros de aluminio y área de vidrio con las medidas."""
        try:
            medidas = self._leer_medidas()
        except ValueError:
            medidas = None
            self.dibujo.limpiar()
            self.lbl_vidrio_area.configure(text="—")
        else:
            ancho, alto = medidas
            self.dibujo.dibujar(ancho, alto, perfiles=[f.nombre for f in self.filas])
            self.lbl_vidrio_area.configure(
                text=f"{ancho * alto:.2f} m²   ({ancho:.2f} × {alto:.2f})")

        for fila in self.filas:
            fila.refrescar(self.catalogo, medidas)

    def agregar_perfil_manual(self) -> None:
        """Agrega una fila en blanco y pone el cursor en su nombre."""
        fila = FilaPerfilManual(self.tabla, on_eliminar=self._eliminar_fila,
                                on_cambio=self.actualizar_perfiles)
        self._colocar_nueva(fila)
        fila.e_nombre.focus_set()

    def _colocar_nueva(self, fila: Fila) -> None:
        self.filas.append(fila)
        fila.colocar(len(self.filas))

    def _eliminar_fila(self, fila: Fila) -> None:
        fila.destruir()
        self.filas.remove(fila)
        for i, restante in enumerate(self.filas, start=1):
            restante.colocar(i)
        self.actualizar_perfiles()  # el dibujo refleja qué perfiles lleva la ventana

    def aplicar_catalogo(self, catalogo: Catalogo) -> None:
        """Aplica los precios nuevos a las filas actuales (las capturadas a mano no cambian)."""
        self.catalogo = catalogo
        self.actualizar_perfiles()

    # ----- Lectura / escritura de datos -----------------------------------

    def cargar(self, datos: DatosCotizacion) -> None:
        """Llena el formulario con los datos indicados."""
        for fila in self.filas:
            fila.destruir()
        self.filas.clear()
        for perfil in datos.perfiles:
            if self.catalogo.buscar(perfil.nombre):
                self._colocar_nueva(FilaPerfil(self.tabla, perfil.nombre,
                                               on_eliminar=self._eliminar_fila))
            else:
                self._colocar_nueva(FilaPerfilManual(self.tabla, on_eliminar=self._eliminar_fila,
                                                     on_cambio=self.actualizar_perfiles,
                                                     perfil=perfil))

        poner_texto(self.e_ancho, f"{datos.ancho:.2f}")
        poner_texto(self.e_alto, f"{datos.alto:.2f}")
        poner_texto(self.e_vidrio_precio, f"{datos.vidrio_precio_m2:.2f}")
        poner_texto(self.e_herrajes, f"{datos.herrajes:.2f}")
        poner_texto(self.e_margen1, f"{datos.margen1_pct:.2f}")
        poner_texto(self.e_margen2, f"{datos.margen2_pct:.2f}")
        self.cb_modo_margen.set(datos.modo_margen.value)
        self.actualizar_perfiles()

    def leer(self) -> DatosCotizacion:
        """Lee y valida el formulario. Lanza ValueError con un mensaje para el usuario."""
        ancho, alto = self._leer_medidas()
        return DatosCotizacion(
            perfiles=[f.perfil(self.catalogo, ancho, alto) for f in self.filas],
            ancho=ancho, alto=alto,
            vidrio_precio_m2=parse_numero(self.e_vidrio_precio.get(), "Precio por m²"),
            herrajes=parse_numero(self.e_herrajes.get(), "Herrajes"),
            margen1_pct=parse_numero(self.e_margen1.get(), "Margen 1"),
            margen2_pct=parse_numero(self.e_margen2.get(), "Margen 2"),
            modo_margen=ModoMargen(self.cb_modo_margen.get()),
        )
