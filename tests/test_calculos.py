import pytest

from cotizador.calculos import (armar_datos, calcular_cotizacion, catalogo_de_fabrica,
                                datos_por_defecto, describir_materiales)
from cotizador.models import DatosCotizacion, ModoMargen, Perfil


def test_precio_de_pieza_es_metros_por_precio():
    assert Perfil("Jamba", 3.5, 100).costo == pytest.approx(350)


@pytest.mark.parametrize("nombre, metros_esperados", [
    ("Jamba", 2 * 1.2 + 1.5),       # alto + ancho + alto
    ("Zoclo", 2 * 1.5),             # ancho + ancho
    ("Traslape", 2 * 1.2),          # alto + alto
    ("Cerco", 2 * 1.2),             # alto + alto
    ("Riel", 1.5),                  # ancho
    ("Mosquitero", 2 * 1.2 + 1.5),  # alto + ancho + alto
])
def test_metros_segun_formula(nombre, metros_esperados):
    item = catalogo_de_fabrica().buscar(nombre)
    assert item.metros(alto=1.2, ancho=1.5) == pytest.approx(metros_esperados)


def test_valores_por_defecto_encadenado():
    # Ventana por defecto: 1.50 m de ancho × 1.20 m de alto
    r = calcular_cotizacion(datos_por_defecto())
    assert r.subtotal_aluminio == pytest.approx(390 + 82.5 + 165 + 168 + 168 + 117)
    assert r.subtotal_vidrio == pytest.approx(684.00)
    assert r.costo_base == pytest.approx(2024.50)
    assert r.total == pytest.approx(2024.50 * 1.3 * 1.3)


def test_las_medidas_cambian_los_metros():
    datos = armar_datos(catalogo_de_fabrica().perfiles, ancho=2.0, alto=1.0)
    jamba = next(p for p in datos.perfiles if p.nombre == "Jamba")
    assert jamba.metros == pytest.approx(4.0)
    assert (datos.ancho, datos.alto) == (2.0, 1.0)


@pytest.mark.parametrize("ancho, alto", [(0, 1), (1, 0), (-1, 1)])
def test_medidas_invalidas(ancho, alto):
    with pytest.raises(ValueError):
        armar_datos([], ancho=ancho, alto=alto)


def test_margen_global_suma_porcentajes_sobre_base():
    datos = datos_por_defecto()
    datos.modo_margen = ModoMargen.GLOBAL
    assert calcular_cotizacion(datos).total == pytest.approx(2024.50 * 1.6)


def test_sin_perfiles_ni_materiales_da_cero():
    r = calcular_cotizacion(DatosCotizacion(perfiles=[], vidrio_area=0, herrajes=0))
    assert r.total == 0
    assert r.margen_efectivo_pct == 0


def test_describir_materiales():
    datos = DatosCotizacion(perfiles=[Perfil("Jamba", 1, 1), Perfil("Riel", 1, 1)],
                            vidrio_area=1.8, herrajes=250)
    assert describir_materiales(datos) == \
        "Perfiles de aluminio (Jamba, Riel), vidrio (1.8 m²) y herrajes."


def test_describir_materiales_vacio():
    assert describir_materiales(DatosCotizacion(perfiles=[], vidrio_area=0, herrajes=0)) == ""
