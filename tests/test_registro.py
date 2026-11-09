import logging
import sys

from cotizador.services import registro


def test_configurar_registro_escribe_en_archivo(tmp_path, monkeypatch):
    monkeypatch.setattr(registro, "carpeta_datos", lambda: tmp_path)
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)  # se restaura al terminar
    ruta = registro.configurar_registro()
    try:
        registro.log.error("prueba de registro")
        for manejador in logging.getLogger().handlers:
            manejador.flush()
        assert ruta == tmp_path / "errores.log"
        assert "prueba de registro" in ruta.read_text(encoding="utf-8")
    finally:
        for manejador in list(logging.getLogger().handlers):
            manejador.close()
            logging.getLogger().removeHandler(manejador)
