"""Colores y fuentes compartidos por la interfaz. Tuplas = (modo claro, modo oscuro)."""

import customtkinter as ctk

COLOR_ACENTO = ("#0B6E4F", "#2ECC71")
COLOR_ACENTO_HOVER = ("#095A40", "#27AE60")
COLOR_TEXTO_SOBRE_ACENTO = ("white", "gray10")
COLOR_ERROR = ("#C0392B", "#E74C3C")
COLOR_ERROR_HOVER = ("#F5D5D1", "#4A2420")
COLOR_TEXTO = ("gray10", "gray90")
COLOR_TEXTO_SECUNDARIO = ("gray30", "gray70")
COLOR_SEPARADOR = ("gray75", "gray30")

TEMAS = {"Claro": "light", "Oscuro": "dark", "Sistema": "system"}
TEMA_INICIAL = "Oscuro"


def fuente(tamano: int = 14, negrita: bool = False) -> ctk.CTkFont:
    return ctk.CTkFont(size=tamano, weight="bold" if negrita else "normal")


def boton_principal(master, texto: str, comando, **kwargs) -> ctk.CTkButton:
    """Botón verde de acción destacada."""
    return ctk.CTkButton(master, text=texto, command=comando, fg_color=COLOR_ACENTO,
                         hover_color=COLOR_ACENTO_HOVER, text_color=COLOR_TEXTO_SOBRE_ACENTO,
                         **kwargs)


def boton_secundario(master, texto: str, comando, **kwargs) -> ctk.CTkButton:
    """Botón con borde y fondo transparente."""
    kwargs.setdefault("border_width", 2)
    return ctk.CTkButton(master, text=texto, command=comando, fg_color="transparent",
                         text_color=COLOR_TEXTO, **kwargs)
