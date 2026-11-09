import json

import pytest

from cotizador.models import Cliente, DocumentoCotizacion, Empresa
from cotizador.services.cotizaciones import ServicioCotizaciones
from cotizador.services.preferencias import Preferencias, RepositorioPreferencias


@pytest.fixture
def servicio(tmp_path):
    repo = RepositorioPreferencias(tmp_path / "cfg" / "config.json")
    return ServicioCotizaciones(repo, tmp_path / "pdfs")


def _documento(folio="COT-0001", iva=False):
    return DocumentoCotizacion(
        empresa=Empresa(nombre="Aluminios Alumar", atiende="Luis"),
        cliente=Cliente(nombre="Juan Pérez", telefono="555"),
        folio=folio, precio_unitario=3356.85, cantidad=2, incluir_iva=iva,
        condiciones=["Válida {vigencia} días."],
    )


def test_totales_con_iva():
    doc = _documento(iva=True)
    assert doc.subtotal == 6713.70
    assert doc.iva == 1074.19
    assert doc.total == 7787.89


def test_preferencias_por_defecto_si_no_hay_archivo(tmp_path):
    prefs = RepositorioPreferencias(tmp_path / "no_existe.json").cargar()
    assert prefs.folio_sugerido == "COT-0001"


def test_preferencias_archivo_corrupto(tmp_path):
    ruta = tmp_path / "config.json"
    ruta.write_text("{no es json", encoding="utf-8")
    assert RepositorioPreferencias(ruta).cargar() == Preferencias()


def test_emitir_genera_pdf_y_guarda_preferencias(servicio):
    prefs = servicio.cargar_preferencias()
    ruta = servicio.emitir(_documento(iva=True), prefs, consumir_folio=True)

    assert ruta.name == "COT-0001 - Juan Pérez.pdf"
    assert ruta.read_bytes().startswith(b"%PDF")

    guardadas = servicio.cargar_preferencias()
    assert guardadas.siguiente_folio == 2
    assert guardadas.empresa.nombre == "Aluminios Alumar"
    assert guardadas.incluir_iva is True


def test_emitir_sin_consumir_folio(servicio):
    prefs = servicio.cargar_preferencias()
    servicio.emitir(_documento(folio="ESPECIAL"), prefs, consumir_folio=False)
    assert servicio.cargar_preferencias().siguiente_folio == 1


def test_lee_formato_de_configuracion_anterior(tmp_path):
    ruta = tmp_path / "config.json"
    ruta.write_text(json.dumps({"empresa": {"nombre": "X", "campo_viejo": 1},
                                "siguiente_folio": 7, "iva": True}), encoding="utf-8")
    prefs = RepositorioPreferencias(ruta).cargar()
    assert (prefs.empresa.nombre, prefs.siguiente_folio, prefs.incluir_iva) == ("X", 7, True)
