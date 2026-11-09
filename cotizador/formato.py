"""Conversión y formato de valores: moneda, fechas, números a letra y validación de entradas."""

from __future__ import annotations

import re
from datetime import date

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre")


# ---------------------------------------------------------------------------
# Formato de salida
# ---------------------------------------------------------------------------

def fmt_money(valor: float) -> str:
    """1234.5 -> '$1,234.50'"""
    return f"${valor:,.2f}"


def fecha_larga(d: date) -> str:
    """date(2026, 11, 9) -> '9 de noviembre de 2026'"""
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def nombre_archivo_seguro(texto: str, largo_max: int = 60) -> str:
    """Quita caracteres no permitidos en nombres de archivo de Windows."""
    return re.sub(r'[<>:"/\\|?*\n\r\t]+', "", texto).strip()[:largo_max]


# ---------------------------------------------------------------------------
# Lectura de entradas del usuario
# ---------------------------------------------------------------------------

def parse_numero(texto: str, campo: str, permitir_negativo: bool = False) -> float:
    """
    Convierte texto a número. Acepta coma decimal ('3,5'), separador de miles
    ('1,234.5') y símbolos '$' o '%'. Lanza ValueError con un mensaje legible.
    """
    limpio = texto.strip().replace("$", "").replace("%", "").replace(" ", "")
    if "," in limpio and "." not in limpio:
        limpio = limpio.replace(",", ".")   # coma decimal
    else:
        limpio = limpio.replace(",", "")    # comas de miles
    if not limpio:
        raise ValueError(f"El campo «{campo}» está vacío.")
    try:
        valor = float(limpio)
    except ValueError:
        raise ValueError(f"El campo «{campo}» no es un número válido: «{texto}».") from None
    if not permitir_negativo and valor < 0:
        raise ValueError(f"El campo «{campo}» no puede ser negativo.")
    return valor


def parse_medida(texto: str, campo: str) -> float:
    """Medida en metros: número mayor a cero."""
    valor = parse_numero(texto, campo)
    if valor <= 0:
        raise ValueError(f"El campo «{campo}» debe ser mayor a cero.")
    return valor


def parse_entero(texto: str, campo: str, minimo: int = 0) -> int:
    """Como parse_numero, pero exige un entero mayor o igual a `minimo`."""
    valor = parse_numero(texto, campo)
    if valor != int(valor):
        raise ValueError(f"El campo «{campo}» debe ser un número entero.")
    if valor < minimo:
        raise ValueError(f"El campo «{campo}» debe ser al menos {minimo}.")
    return int(valor)


# ---------------------------------------------------------------------------
# Importe con letra (pesos mexicanos)
# ---------------------------------------------------------------------------

_UNIDADES = ("cero", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
             "nueve", "diez", "once", "doce", "trece", "catorce", "quince", "dieciséis",
             "diecisiete", "dieciocho", "diecinueve", "veinte", "veintiuno", "veintidós",
             "veintitrés", "veinticuatro", "veinticinco", "veintiséis", "veintisiete",
             "veintiocho", "veintinueve")
_DECENAS = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta",
            7: "setenta", 8: "ochenta", 9: "noventa"}
_CENTENAS = {1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos",
             5: "quinientos", 6: "seiscientos", 7: "setecientos", 8: "ochocientos",
             9: "novecientos"}


def _apocope(texto: str) -> str:
    """'uno' -> 'un' delante de sustantivo (veintiún mil, un peso)."""
    if texto.endswith("veintiuno"):
        return texto[:-len("veintiuno")] + "veintiún"
    if texto.endswith("uno"):
        return texto[:-3] + "un"
    return texto


def numero_a_letras(n: int) -> str:
    """Entero no negativo a palabras en español: 356 -> 'trescientos cincuenta y seis'."""
    if n < 0:
        raise ValueError("Sólo se admiten números no negativos.")
    if n < 30:
        return _UNIDADES[n]
    if n < 100:
        d, u = divmod(n, 10)
        return _DECENAS[d] + (f" y {_UNIDADES[u]}" if u else "")
    if n < 1000:
        if n == 100:
            return "cien"
        c, resto = divmod(n, 100)
        return _CENTENAS[c] + (f" {numero_a_letras(resto)}" if resto else "")
    if n < 1_000_000:
        m, resto = divmod(n, 1000)
        miles = "mil" if m == 1 else f"{_apocope(numero_a_letras(m))} mil"
        return miles + (f" {numero_a_letras(resto)}" if resto else "")
    m, resto = divmod(n, 1_000_000)
    millones = "un millón" if m == 1 else f"{_apocope(numero_a_letras(m))} millones"
    return millones + (f" {numero_a_letras(resto)}" if resto else "")


def importe_con_letra(valor: float) -> str:
    """3356.85 -> 'TRES MIL TRESCIENTOS CINCUENTA Y SEIS PESOS 85/100 M.N.'"""
    pesos, centavos = divmod(round(valor * 100), 100)
    texto = _apocope(numero_a_letras(pesos))
    if texto.endswith(("millón", "millones")):
        texto += " de"
    unidad = "peso" if pesos == 1 else "pesos"
    return f"{texto} {unidad} {centavos:02d}/100 M.N.".upper()
