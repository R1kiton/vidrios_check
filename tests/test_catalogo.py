import json

import pytest

from cotizador.calculos import calcular_cotizacion, catalogo_de_fabrica, datos_por_defecto
from cotizador.models import Catalogo, PerfilCatalogo
from cotizador.services.catalogo import RepositorioCatalogo


def test_catalogo_de_fabrica_tiene_los_precios_fijos():
    precios = {p.nombre: p.precio_metro for p in catalogo_de_fabrica().perfiles}
    assert precios == {"Jamba": 100, "Riel": 55, "Zoclo": 55, "Traslape": 70,
                       "Cerco": 70, "Mosquitero": 30}


@pytest.mark.parametrize("veces_alto, veces_ancho, texto", [
    (2, 1, "2 × alto + ancho"), (0, 2, "2 × ancho"), (1, 0, "alto"), (0, 0, "—"),
])
def test_formula_legible(veces_alto, veces_ancho, texto):
    assert PerfilCatalogo("X", 1, veces_alto, veces_ancho).formula == texto


def test_cotizacion_usa_precios_y_formulas_del_catalogo():
    catalogo = Catalogo([PerfilCatalogo("Jamba", 200, veces_alto=2, veces_ancho=1),
                         PerfilCatalogo("Riel", 10, veces_ancho=1)])
    datos = datos_por_defecto(catalogo)  # 1.50 × 1.20
    assert [(p.nombre, round(p.metros, 2), p.precio_metro) for p in datos.perfiles] == \
        [("Jamba", 3.9, 200), ("Riel", 1.5, 10)]
    assert calcular_cotizacion(datos).subtotal_aluminio == pytest.approx(3.9 * 200 + 15)


@pytest.mark.parametrize("perfiles, mensaje", [
    ([], "al menos un perfil"),
    ([PerfilCatalogo("", 10)], "nombre"),
    ([PerfilCatalogo("Jamba", 10), PerfilCatalogo("jamba", 20)], "repetido"),
    ([PerfilCatalogo("Jamba", -1)], "negativos"),
    ([PerfilCatalogo("Jamba", 1, veces_alto=-2)], "negativos"),
])
def test_validacion_del_catalogo(perfiles, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        Catalogo(perfiles).validar()


def test_repositorio_sin_archivo_devuelve_fabrica(tmp_path):
    assert RepositorioCatalogo(tmp_path / "no.json").cargar() == catalogo_de_fabrica()


def test_repositorio_guarda_y_carga(tmp_path):
    repo = RepositorioCatalogo(tmp_path / "datos" / "catalogo.json")
    catalogo = Catalogo([PerfilCatalogo("Jamba", 120.5, 2, 1), PerfilCatalogo("Nuevo", 45, 0, 3)])
    repo.guardar(catalogo)
    assert RepositorioCatalogo(repo.ruta).cargar() == catalogo


def test_catalogo_de_version_anterior_recibe_formulas_de_fabrica(tmp_path):
    ruta = tmp_path / "catalogo.json"
    ruta.write_text(json.dumps({"perfiles": [
        {"nombre": "Jamba", "precio_metro": 120, "metros_default": 3.5},
        {"nombre": "Otro", "precio_metro": 10, "metros_default": 1},
    ]}), encoding="utf-8")
    jamba, otro = RepositorioCatalogo(ruta).cargar().perfiles
    assert (jamba.precio_metro, jamba.veces_alto, jamba.veces_ancho) == (120, 2, 1)
    assert (otro.veces_alto, otro.veces_ancho) == (0, 0)


def test_repositorio_no_guarda_catalogo_invalido(tmp_path):
    repo = RepositorioCatalogo(tmp_path / "catalogo.json")
    with pytest.raises(ValueError):
        repo.guardar(Catalogo([]))
    assert not repo.ruta.exists()


def test_repositorio_archivo_danado_devuelve_fabrica(tmp_path):
    ruta = tmp_path / "catalogo.json"
    ruta.write_text('{"perfiles": [{"nombre": "X"}]}', encoding="utf-8")
    assert RepositorioCatalogo(ruta).cargar() == catalogo_de_fabrica()
