"""Panel derecho: desglose del cálculo, total y botones de acción."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

import customtkinter as ctk

from ..formato import fmt_money
from ..models import DatosCotizacion, ModoMargen, ResultadoCotizacion
from .tema import (COLOR_ACENTO, COLOR_ERROR, COLOR_SEPARADOR, COLOR_TEXTO_SECUNDARIO,
                   boton_principal, boton_secundario, fuente)

SEPARADOR = None
# (clave, título inicial, en negrita) — SEPARADOR dibuja una línea divisoria
RENGLONES = (
    ("aluminio", "Subtotal aluminio", False),
    ("vidrio", "Subtotal vidrio", False),
    ("herrajes", "Herrajes", False),
    SEPARADOR,
    ("base", "Costo base de materiales", True),
    SEPARADOR,
    ("m1", "Margen 1", False),
    ("etapa1", "Etapa 1", True),
    ("m2", "Margen 2", False),
    ("etapa2", "Etapa 2", True),
    SEPARADOR,
    ("margen_total", "Margen total aplicado", False),
)


class PanelResumen(ctk.CTkFrame):
    """Muestra el resultado de la cotización y expone las acciones principales."""

    def __init__(self, master, on_calcular: Callable[[], object],
                 on_restablecer: Callable[[], object], on_imprimir: Callable[[], object]):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._titulos: dict[str, ctk.CTkLabel] = {}
        self._valores: dict[str, ctk.CTkLabel] = {}

        ctk.CTkLabel(self, text="Resumen de la cotización", font=fuente(17, negrita=True)).grid(
            row=0, column=0, padx=18, pady=(16, 4), sticky="w")
        self.lbl_fecha = ctk.CTkLabel(self, text="", text_color=COLOR_TEXTO_SECUNDARIO)
        self.lbl_fecha.grid(row=1, column=0, padx=18, sticky="w")

        self._crear_desglose(fila=2)
        self._crear_total(fila=3)
        self.lbl_estado = ctk.CTkLabel(self, text="", wraplength=380, justify="left")
        self.lbl_estado.grid(row=4, column=0, padx=18, sticky="w")
        self._crear_botones(fila=5, on_calcular=on_calcular,
                            on_restablecer=on_restablecer, on_imprimir=on_imprimir)

    # ----- Construcción ---------------------------------------------------

    def _crear_desglose(self, fila: int) -> None:
        # Desplazable para que nunca se recorte en pantallas pequeñas
        desglose = ctk.CTkScrollableFrame(self, fg_color="transparent")
        desglose.grid(row=fila, column=0, padx=10, pady=6, sticky="nsew")
        desglose.grid_columnconfigure(0, weight=1)

        for i, renglon in enumerate(RENGLONES):
            if renglon is SEPARADOR:
                ctk.CTkFrame(desglose, height=2, fg_color=COLOR_SEPARADOR).grid(
                    row=i, column=0, columnspan=2, sticky="ew", pady=6)
                continue
            clave, titulo, negrita = renglon
            f = fuente(14, negrita)
            self._titulos[clave] = ctk.CTkLabel(desglose, text=titulo, font=f, anchor="w")
            self._titulos[clave].grid(row=i, column=0, sticky="w", pady=2)
            self._valores[clave] = ctk.CTkLabel(desglose, text=fmt_money(0), font=f, anchor="e")
            self._valores[clave].grid(row=i, column=1, sticky="e", pady=2)

    def _crear_total(self, fila: int) -> None:
        caja = ctk.CTkFrame(self, border_width=2, border_color=COLOR_ACENTO, corner_radius=12)
        caja.grid(row=fila, column=0, padx=18, pady=(4, 12), sticky="ew")
        caja.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(caja, text="PRECIO FINAL COTIZADO", font=fuente(13, negrita=True),
                     text_color=COLOR_TEXTO_SECUNDARIO).grid(row=0, column=0, pady=(12, 0))
        self.lbl_total = ctk.CTkLabel(caja, text=fmt_money(0), text_color=COLOR_ACENTO,
                                      font=fuente(40, negrita=True))
        self.lbl_total.grid(row=1, column=0, pady=(0, 12))

    def _crear_botones(self, fila: int, on_calcular, on_restablecer, on_imprimir) -> None:
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=fila, column=0, padx=18, pady=(6, 18), sticky="ew")
        barra.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(barra, text="Calcular", height=44, font=fuente(16, negrita=True),
                      command=on_calcular).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        boton_secundario(barra, "Restablecer valores", on_restablecer, height=44).grid(
            row=0, column=1, padx=(6, 0), sticky="ew")
        boton_principal(barra, "🖨  Imprimir cotización", on_imprimir, height=40,
                        font=fuente(14, negrita=True)).grid(
            row=1, column=0, columnspan=2, pady=(8, 0), sticky="ew")

    # ----- Actualización --------------------------------------------------

    def mostrar(self, datos: DatosCotizacion, r: ResultadoCotizacion) -> None:
        """Pinta el desglose y el total de una cotización."""
        base_m2 = "costo base" if datos.modo_margen is ModoMargen.GLOBAL else "Etapa 1"
        valores = {
            "aluminio": fmt_money(r.subtotal_aluminio),
            "vidrio": fmt_money(r.subtotal_vidrio),
            "herrajes": fmt_money(r.subtotal_herrajes),
            "base": fmt_money(r.costo_base),
            "m1": "+ " + fmt_money(r.monto_margen1),
            "etapa1": fmt_money(r.etapa1),
            "m2": "+ " + fmt_money(r.monto_margen2),
            "etapa2": fmt_money(r.etapa2),
            "margen_total": fmt_money(r.margen_total),
        }
        for clave, texto in valores.items():
            self._valores[clave].configure(text=texto)
        self._titulos["m1"].configure(text=f"Margen 1 ({datos.margen1_pct:g}% sobre costo base)")
        self._titulos["m2"].configure(text=f"Margen 2 ({datos.margen2_pct:g}% sobre {base_m2})")
        self._titulos["margen_total"].configure(
            text=f"Margen total aplicado ({r.margen_efectivo_pct:.2f}%)")

        self.lbl_total.configure(text=fmt_money(r.total))
        self.lbl_fecha.configure(text=datetime.now().strftime("Calculado el %d/%m/%Y a las %H:%M"))
        self.mostrar_estado(f"✔ Cotización calculada con {len(datos.perfiles)} perfil(es).")

    def mostrar_error(self, mensaje: str) -> None:
        self.lbl_total.configure(text="—")
        self.lbl_estado.configure(text=f"⚠ {mensaje}", text_color=COLOR_ERROR)

    def mostrar_estado(self, mensaje: str) -> None:
        self.lbl_estado.configure(text=mensaje, text_color=COLOR_TEXTO_SECUNDARIO)
