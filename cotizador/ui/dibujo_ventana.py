"""Dibujo ilustrativo de la ventana (corrediza de dos hojas) a escala con sus cotas."""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

# Colores por modo (claro, oscuro)
_COLORES = {
    "marco": ("#6B7785", "#9AA6B2"),
    "hoja": ("#8A96A3", "#B8C2CC"),
    "vidrio": ("#CFE5F5", "#2C4A63"),
    "reflejo": ("#F4FAFF", "#4B6F8C"),
    "cota": ("#33414F", "#C9D3DD"),
}


class DibujoVentana(ctk.CTkFrame):
    """Lienzo que dibuja un rectángulo proporcional al ancho × alto indicados."""

    def __init__(self, master, ancho_px: int = 300, alto_px: int = 200):
        super().__init__(master, fg_color="transparent")
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0,
                                width=self._apply_widget_scaling(ancho_px),
                                height=self._apply_widget_scaling(alto_px))
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self._redibujar())
        self._medidas: tuple[float, float] | None = None
        self._aplicar_fondo()

    # ----- API pública ----------------------------------------------------

    def dibujar(self, ancho: float, alto: float) -> None:
        self._medidas = (ancho, alto)
        self._redibujar()

    def limpiar(self) -> None:
        """Muestra un aviso en lugar del dibujo (medidas inválidas)."""
        self._medidas = None
        self._redibujar()

    # ----- Tema -----------------------------------------------------------

    def _set_appearance_mode(self, mode_string):
        """customtkinter llama a este método al cambiar entre modo claro y oscuro."""
        super()._set_appearance_mode(mode_string)
        self._aplicar_fondo()
        self._redibujar()

    def _aplicar_fondo(self) -> None:
        self.canvas.configure(bg=self._apply_appearance_mode(self._detect_color_of_master()))

    def _color(self, clave: str) -> str:
        return self._apply_appearance_mode(_COLORES[clave])

    def _px(self, valor: float) -> int:
        return int(self._apply_widget_scaling(valor))

    # ----- Dibujo ---------------------------------------------------------

    def _redibujar(self) -> None:
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 20 or h < 20:
            return
        fuente = ("Segoe UI", -self._px(12))

        if not self._medidas:
            c.create_text(w / 2, h / 2, text="Ingresa ancho y alto\npara ver la ventana",
                          fill=self._color("cota"), font=fuente, justify="center")
            return

        ancho, alto = self._medidas
        # Márgenes para las cotas (abajo y a la derecha)
        m_izq, m_sup, m_der, m_inf = self._px(10), self._px(10), self._px(46), self._px(40)
        escala = min((w - m_izq - m_der) / ancho, (h - m_sup - m_inf) / alto)
        rw, rh = ancho * escala, alto * escala
        x0 = m_izq + (w - m_izq - m_der - rw) / 2
        y0 = m_sup + (h - m_sup - m_inf - rh) / 2
        x1, y1 = x0 + rw, y0 + rh

        self._dibujar_ventana(x0, y0, x1, y1)
        self._dibujar_cotas(x0, y0, x1, y1, ancho, alto, fuente)

    def _dibujar_ventana(self, x0: float, y0: float, x1: float, y1: float) -> None:
        c = self.canvas
        marco = max(self._px(4), min(x1 - x0, y1 - y0) * 0.06)  # grosor del cerco
        hoja = marco * 0.6                                        # grosor de cada hoja

        # Marco exterior (cerco/jambas)
        c.create_rectangle(x0, y0, x1, y1, fill=self._color("marco"), outline="")
        ix0, iy0, ix1, iy1 = x0 + marco, y0 + marco, x1 - marco, y1 - marco
        medio = (ix0 + ix1) / 2
        traslape = hoja / 2

        # Dos hojas corredizas que se traslapan al centro
        for hx0, hx1 in ((ix0, medio + traslape), (medio - traslape, ix1)):
            c.create_rectangle(hx0, iy0, hx1, iy1, fill=self._color("hoja"), outline="")
            vx0, vy0, vx1, vy1 = hx0 + hoja, iy0 + hoja, hx1 - hoja, iy1 - hoja
            if vx1 > vx0 and vy1 > vy0:
                c.create_rectangle(vx0, vy0, vx1, vy1, fill=self._color("vidrio"), outline="")
                self._reflejo(vx0, vy0, vx1, vy1)

        # Línea de traslape al centro
        c.create_line(medio, iy0, medio, iy1, fill=self._color("marco"), width=max(1, hoja / 3))

    def _reflejo(self, x0: float, y0: float, x1: float, y1: float) -> None:
        """Dos líneas diagonales cortas que sugieren vidrio."""
        w, h = x1 - x0, y1 - y0
        lado = min(w, h) * 0.35
        for desplazamiento in (0.18, 0.30):
            ax, ay = x0 + w * desplazamiento, y0 + h * 0.15
            self.canvas.create_line(ax, ay + lado, ax + lado, ay,
                                    fill=self._color("reflejo"), width=max(1, self._px(2)))

    def _dibujar_cotas(self, x0, y0, x1, y1, ancho: float, alto: float, fuente) -> None:
        c = self.canvas
        color = self._color("cota")
        sep = self._px(14)
        flecha = (self._px(6), self._px(7), self._px(3))

        # Ancho (abajo)
        yc = y1 + sep
        c.create_line(x0, yc, x1, yc, fill=color, arrow=tk.BOTH, arrowshape=flecha)
        for x in (x0, x1):
            c.create_line(x, y1 + self._px(3), x, yc + self._px(4), fill=color)
        c.create_text((x0 + x1) / 2, yc + self._px(4), text=f"Ancho {ancho:.2f} m",
                      fill=color, font=fuente, anchor="n")

        # Alto (derecha, texto vertical)
        xc = x1 + sep
        c.create_line(xc, y0, xc, y1, fill=color, arrow=tk.BOTH, arrowshape=flecha)
        for y in (y0, y1):
            c.create_line(x1 + self._px(3), y, xc + self._px(4), y, fill=color)
        c.create_text(xc + self._px(5), (y0 + y1) / 2, text=f"Alto {alto:.2f} m",
                      fill=color, font=fuente, angle=90, anchor="n")
