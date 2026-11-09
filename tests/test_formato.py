from datetime import date

import pytest

from cotizador.formato import (fecha_larga, fmt_money, importe_con_letra, nombre_archivo_seguro,
                               parse_entero, parse_numero)


@pytest.mark.parametrize("texto, esperado", [
    ("3.5", 3.5), ("3,5", 3.5), ("1,234.5", 1234.5), ("$ 250", 250), ("30%", 30),
])
def test_parse_numero(texto, esperado):
    assert parse_numero(texto, "x") == esperado


@pytest.mark.parametrize("texto", ["", "abc", "-1"])
def test_parse_numero_invalido(texto):
    with pytest.raises(ValueError):
        parse_numero(texto, "x")


def test_parse_entero():
    assert parse_entero("3", "x", minimo=1) == 3
    with pytest.raises(ValueError):
        parse_entero("0", "x", minimo=1)
    with pytest.raises(ValueError):
        parse_entero("1.5", "x")


def test_formatos():
    assert fmt_money(3356.847) == "$3,356.85"
    assert fecha_larga(date(2026, 11, 9)) == "9 de noviembre de 2026"
    assert nombre_archivo_seguro('COT-1 / "Juan"') == "COT-1  Juan"


@pytest.mark.parametrize("valor, esperado", [
    (1, "UN PESO 00/100 M.N."),
    (21, "VEINTIÚN PESOS 00/100 M.N."),
    (100, "CIEN PESOS 00/100 M.N."),
    (3356.85, "TRES MIL TRESCIENTOS CINCUENTA Y SEIS PESOS 85/100 M.N."),
    (21500.5, "VEINTIÚN MIL QUINIENTOS PESOS 50/100 M.N."),
    (101000, "CIENTO UN MIL PESOS 00/100 M.N."),
    (1_000_000, "UN MILLÓN DE PESOS 00/100 M.N."),
])
def test_importe_con_letra(valor, esperado):
    assert importe_con_letra(valor) == esperado
