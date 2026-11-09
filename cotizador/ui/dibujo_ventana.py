"""
Dibujo ilustrativo de una ventana corrediza de dos hojas, a escala, con cada perfil
de aluminio en su lugar y en su propio color:

    Jamba       marco fijo: arriba + lado izquierdo + lado derecho
    Riel        marco fijo: abajo (por donde corren las hojas)
    Zoclo       arriba y abajo de cada hoja
    Cerco       lado exterior de cada hoja
    Traslape    lado de cada hoja que se encima al centro
    Mosquitero  marco de la malla (cubre media ventana)

Al pasar el mouse sobre una pieza o sobre la leyenda se resalta ese perfil.
"""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from .tema import COLOR_TEXTO_SECUNDARIO, fuente

# Perfiles que conoce el dibujo: clave -> (nombre, color)
PERFILES_DIBUJO = {
    "jamba": ("Jamba", "#3B82F6"),
    "riel": ("Riel", "#F59E0B"),
    "zoclo": ("Zoclo", "#10B981"),
    "cerco": ("Cerco", "#8B5CF6"),
    "traslape": ("Traslape", "#EF4444"),
    "mosquitero": ("Mosquitero", "#14B8A6"),
}

# Colores neutros por modo (claro, oscuro)
_COLORES = {
    "neutro": ("#8A96A3", "#7D8894"),      # perfil que no está en la cotización
    "hueco": ("#5B6670", "#1E2933"),
    "vidrio": ("#CFE5F5", "#2C4A63"),
    "reflejo": ("#F4FAFF", "#4B6F8C"),
    "cota": ("#33414F", "#C9D3DD"),
}


class DibujoVentana(ctk.CTkFrame):
    """Lienzo con la ventana a escala y una leyenda de perfiles."""

    def __init__(self, master, ancho_px: int = 340, alto_px: int = 220):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0,
                                width=self._apply_widget_scaling(ancho_px),
                                height=self._apply_widget_scaling(alto_px))
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda _e: self._redibujar())
        # Los eventos por etiqueta sobreviven a canvas.delete("all"): se registran una sola
        # vez aquí (registrarlos en cada redibujo acumulaba comandos Tcl sin liberar).
        for clave in PERFILES_DIBUJO:
            self.canvas.tag_bind(clave, "<Enter>", lambda _e, k=clave: self._resaltar(k))
            self.canvas.tag_bind(clave, "<Leave>", lambda _e: self._quitar_resaltado())
        self._resaltado: str | None = None

        self.leyenda = ctk.CTkFrame(self, fg_color="transparent")
        self.leyenda.grid(row=1, column=0, pady=(4, 0))
        self._etiquetas: dict[str, ctk.CTkLabel] = {}

        self._medidas: tuple[float, float] | None = None
        self._presentes: set[str] = set(PERFILES_DIBUJO)
        self._aplicar_fondo()
        self._crear_leyenda()

    # ----- API pública ----------------------------------------------------

    def dibujar(self, ancho: float, alto: float, perfiles: list[str] | None = None) -> None:
        """Dibuja la ventana. `perfiles` = nombres en la cotización (los demás van en gris)."""
        self._medidas = (ancho, alto)
        if perfiles is not None:
            presentes = {n.strip().casefold() for n in perfiles} & set(PERFILES_DIBUJO)
            if presentes != self._presentes:
                self._presentes = presentes
                self._crear_leyenda()
        self._redibujar()

    def limpiar(self) -> None:
        """Muestra un aviso en lugar del dibujo (medidas inválidas)."""
        self._medidas = None
        self._redibujar()

    # ----- Tema y utilidades ----------------------------------------------

    def _set_appearance_mode(self, mode_string):
        """customtkinter llama a este método al cambiar entre modo claro y oscuro."""
        super()._set_appearance_mode(mode_string)
        self._aplicar_fondo()
        self._redibujar()

    def _aplicar_fondo(self) -> None:
        self.canvas.configure(bg=self._apply_appearance_mode(self._detect_color_of_master()))

    def _color(self, clave: str) -> str:
        if clave in PERFILES_DIBUJO:
            if clave in self._presentes:
                return PERFILES_DIBUJO[clave][1]
            return self._apply_appearance_mode(_COLORES["neutro"])
        return self._apply_appearance_mode(_COLORES[clave])

    def _px(self, valor: float) -> int:
        return int(self._apply_widget_scaling(valor))

    # ----- Leyenda --------------------------------------------------------

    def _crear_leyenda(self) -> None:
        for widget in self.leyenda.winfo_children():
            widget.destroy()
        self._etiquetas.clear()
        visibles = [k for k in PERFILES_DIBUJO if k in self._presentes]
        for i, clave in enumerate(visibles):
            nombre, color = PERFILES_DIBUJO[clave]
            chip = ctk.CTkFrame(self.leyenda, fg_color="transparent")
            chip.grid(row=i // 3, column=i % 3, padx=6, pady=1, sticky="w")
            muestra = ctk.CTkFrame(chip, width=12, height=12, corner_radius=3, fg_color=color)
            muestra.grid(row=0, column=0, padx=(0, 5))
            etiqueta = ctk.CTkLabel(chip, text=nombre, font=fuente(12),
                                    text_color=COLOR_TEXTO_SECUNDARIO, height=18)
            etiqueta.grid(row=0, column=1)
            self._etiquetas[clave] = etiqueta
            for w in (chip, muestra, etiqueta):
                w.bind("<Enter>", lambda _e, k=clave: self._resaltar(k))
                w.bind("<Leave>", lambda _e: self._quitar_resaltado())

    # ----- Resaltado ------------------------------------------------------

    def _resaltar(self, clave: str) -> None:
        """Marca con un contorno todas las piezas de un perfil."""
        if self._resaltado == clave:
            return  # ya está resaltado: no redibujar (evita parpadeo)
        self._quitar_resaltado()
        self._resaltado = clave
        c = self.canvas
        for item in c.find_withtag(clave):
            x0, y0, x1, y1 = c.bbox(item)
            # state="disabled": el contorno no recibe eventos del mouse. Si los recibiera,
            # al quedar el cursor sobre él Tk dispararía <Leave> de la pieza -> se borra el
            # contorno -> <Enter> otra vez -> ... un ciclo infinito que congelaba la app.
            c.create_rectangle(x0, y0, x1, y1, outline=self._color("cota"),
                               width=max(2, self._px(2)), tags="resaltado", state="disabled")
        if clave in self._etiquetas:
            self._etiquetas[clave].configure(font=fuente(12, negrita=True),
                                             text_color=PERFILES_DIBUJO[clave][1])

    def _quitar_resaltado(self) -> None:
        if self._resaltado is None:
            return
        self._resaltado = None
        self.canvas.delete("resaltado")
        for etiqueta in self._etiquetas.values():
            etiqueta.configure(font=fuente(12), text_color=COLOR_TEXTO_SECUNDARIO)

    # ----- Dibujo ---------------------------------------------------------

    def _redibujar(self) -> None:
        c = self.canvas
        self._quitar_resaltado()
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 20 or h < 20:
            return
        fuente_cotas = ("Segoe UI", -self._px(12))

        if not self._medidas:
            c.create_text(w / 2, h / 2, text="Ingresa ancho y alto\npara ver la ventana",
                          fill=self._color("cota"), font=fuente_cotas, justify="center")
            return

        ancho, alto = self._medidas
        # Márgenes para las cotas (abajo y a la derecha)
        m_izq, m_sup, m_der, m_inf = self._px(8), self._px(8), self._px(46), self._px(40)
        escala = min((w - m_izq - m_der) / ancho, (h - m_sup - m_inf) / alto)
        rw, rh = ancho * escala, alto * escala
        x0 = m_izq + (w - m_izq - m_der - rw) / 2
        y0 = m_sup + (h - m_sup - m_inf - rh) / 2
        x1, y1 = x0 + rw, y0 + rh

        self._dibujar_ventana(x0, y0, x1, y1)
        self._dibujar_cotas(x0, y0, x1, y1, ancho, alto, fuente_cotas)

    def _barra(self, x0, y0, x1, y1, clave: str, contorno: bool = False) -> None:
        """Pieza de perfil. `contorno` dibuja un filo oscuro para separar piezas contiguas."""
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=self._color(clave),
                                     outline=self._color("hueco") if contorno else "",
                                     tags=clave)

    def _dibujar_ventana(self, x0: float, y0: float, x1: float, y1: float) -> None:
        c = self.canvas
        lado = min(x1 - x0, y1 - y0)
        marco = max(self._px(5), lado * 0.07)   # grosor del marco fijo
        hoja = marco * 0.8                       # grosor de los perfiles de cada hoja
        traslape = hoja                          # las hojas se enciman al centro: los dos
                                                 # traslapes quedan uno junto al otro

        # Marco fijo: jamba arriba y a los lados, riel abajo
        self._barra(x0, y0, x1, y0 + marco, "jamba")
        self._barra(x0, y0 + marco, x0 + marco, y1 - marco, "jamba")
        self._barra(x1 - marco, y0 + marco, x1, y1 - marco, "jamba")
        self._barra(x0, y1 - marco, x1, y1, "riel")

        ix0, iy0, ix1, iy1 = x0 + marco, y0 + marco, x1 - marco, y1 - marco
        c.create_rectangle(ix0, iy0, ix1, iy1, fill=self._color("hueco"), outline="")
        medio = (ix0 + ix1) / 2

        # Dos hojas: primero los vidrios y luego los perfiles, para que el vidrio de una
        # hoja no tape el traslape de la otra
        hojas = ((ix0, iy0, medio + traslape, iy1, True),
                 (medio - traslape, iy0, ix1, iy1, False))
        for hx0, hy0, hx1, hy1, _ in hojas:
            self._vidrio_hoja(hx0, hy0, hx1, hy1, hoja)
        for hx0, hy0, hx1, hy1, cerco_izq in hojas:
            self._perfiles_hoja(hx0, hy0, hx1, hy1, hoja, cerco_izq)

        # Mosquitero: marco con malla sobre la hoja izquierda
        if "mosquitero" in self._presentes:
            m = hoja * 1.4
            mx0, my0, mx1, my1 = ix0 + m, iy0 + m, medio - traslape - m * 0.4, iy1 - m
            if mx1 - mx0 > 4 and my1 - my0 > 4:
                c.create_rectangle(mx0, my0, mx1, my1, fill=self._color("mosquitero"),
                                   stipple="gray12", outline="", tags="mosquitero")
                c.create_rectangle(mx0, my0, mx1, my1, outline=self._color("mosquitero"),
                                   width=max(2, hoja * 0.45), tags="mosquitero")

    def _vidrio_hoja(self, x0, y0, x1, y1, grosor: float) -> None:
        if x1 - x0 <= 2 * grosor or y1 - y0 <= 2 * grosor:
            return
        self.canvas.create_rectangle(x0 + grosor, y0 + grosor, x1 - grosor, y1 - grosor,
                                     fill=self._color("vidrio"), outline="")
        self._reflejo(x0 + grosor, y0 + grosor, x1 - grosor, y1 - grosor)

    def _perfiles_hoja(self, x0, y0, x1, y1, grosor: float, cerco_a_la_izquierda: bool) -> None:
        """Perfiles de una hoja: zoclos arriba/abajo, cerco afuera y traslape al centro."""
        if x1 - x0 <= 2 * grosor or y1 - y0 <= 2 * grosor:
            return
        self._barra(x0, y0, x1, y0 + grosor, "zoclo", contorno=True)
        self._barra(x0, y1 - grosor, x1, y1, "zoclo", contorno=True)
        izquierda, derecha = ("cerco", "traslape") if cerco_a_la_izquierda else ("traslape", "cerco")
        self._barra(x0, y0 + grosor, x0 + grosor, y1 - grosor, izquierda, contorno=True)
        self._barra(x1 - grosor, y0 + grosor, x1, y1 - grosor, derecha, contorno=True)

    def _reflejo(self, x0: float, y0: float, x1: float, y1: float) -> None:
        """Dos líneas diagonales cortas que sugieren vidrio."""
        w, h = x1 - x0, y1 - y0
        lado = min(w, h) * 0.3
        for desplazamiento in (0.55, 0.68):
            ax, ay = x0 + w * desplazamiento, y0 + h * 0.15
            self.canvas.create_line(ax, ay + lado, ax + lado, ay,
                                    fill=self._color("reflejo"), width=max(1, self._px(2)))

    def _dibujar_cotas(self, x0, y0, x1, y1, ancho: float, alto: float, fuente_cotas) -> None:
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
                      fill=color, font=fuente_cotas, anchor="n")

        # Alto (derecha, texto vertical)
        xc = x1 + sep
        c.create_line(xc, y0, xc, y1, fill=color, arrow=tk.BOTH, arrowshape=flecha)
        for y in (y0, y1):
            c.create_line(x1 + self._px(3), y, xc + self._px(4), y, fill=color)
        c.create_text(xc + self._px(5), (y0 + y1) / 2, text=f"Alto {alto:.2f} m",
                      fill=color, font=fuente_cotas, angle=90, anchor="n")
