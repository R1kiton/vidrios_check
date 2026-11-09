"""Diálogo para capturar datos del cliente y generar / imprimir la cotización formal."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable

import customtkinter as ctk

from ..calculos import describir_materiales
from ..config import DESCRIPCION_DEFAULT, EMPRESA_NOMBRE_DEFAULT
from ..formato import fmt_money, parse_entero
from ..models import Cliente, DatosCotizacion, DocumentoCotizacion, Empresa, ResultadoCotizacion
from ..services.cotizaciones import ServicioCotizaciones
from ..services.sistema import abrir_archivo, imprimir_archivo
from .tema import COLOR_TEXTO_SECUNDARIO, boton_principal, boton_secundario, fuente
from .widgets import Seccion

ANCHO_ETIQUETAS = 190


class DialogoImpresion(ctk.CTkToplevel):
    """Ventana modal que arma un `DocumentoCotizacion` y lo emite como PDF."""

    def __init__(self, master, datos: DatosCotizacion, resultado: ResultadoCotizacion,
                 servicio: ServicioCotizaciones, on_estado: Callable[[str], None]):
        super().__init__(master)
        self.datos = datos
        self.resultado = resultado
        self.servicio = servicio
        self.on_estado = on_estado
        self.preferencias = servicio.cargar_preferencias()
        self.folio_sugerido = self.preferencias.folio_sugerido
        self.folio_consumido = False

        self.title("Imprimir cotización")
        self._ajustar_tamano()
        self.transient(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        cuerpo = ctk.CTkScrollableFrame(self)
        cuerpo.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 0))
        cuerpo.grid_columnconfigure(0, weight=1)
        self._crear_cliente(cuerpo, 0)
        self._crear_concepto(cuerpo, 1)
        self._crear_opciones(cuerpo, 2)
        self._crear_empresa(cuerpo, 3)
        self._crear_botones()

        self.after(150, self._enfocar)  # CTkToplevel necesita un instante para mostrarse

    # ----- Construcción ---------------------------------------------------

    def _ajustar_tamano(self) -> None:
        """Alto acorde a la pantalla (con escalado de Windows) para que los botones se vean."""
        alto = min(720, int(self.winfo_screenheight() / self._get_window_scaling()) - 140)
        self.geometry(f"620x{alto}+40+20")
        self.minsize(560, 400)

    def _seccion(self, master, fila: int, titulo: str) -> Seccion:
        sec = Seccion(master, titulo, ancho_etiqueta=ANCHO_ETIQUETAS, campos_expandidos=True)
        sec.grid(row=fila, column=0, sticky="ew", padx=4, pady=6)
        return sec

    def _crear_cliente(self, master, fila: int) -> None:
        sec = self._seccion(master, fila, "Datos del cliente")
        self.e_cliente = sec.agregar_campo("Nombre del cliente *")
        self.e_tel_cliente = sec.agregar_campo("Teléfono")
        self.e_obra = sec.agregar_campo("Dirección / obra")

    def _crear_concepto(self, master, fila: int) -> None:
        sec = self._seccion(master, fila, "Concepto")
        self.e_folio = sec.agregar_campo("Folio", self.folio_sugerido)
        self.e_desc = sec.agregar_campo("Descripción", DESCRIPCION_DEFAULT)
        self.e_medidas = sec.agregar_campo(
            "Medidas", f"{self.datos.ancho:.2f} m de ancho × {self.datos.alto:.2f} m de alto")
        self.e_cantidad = sec.agregar_campo("Cantidad de ventanas", "1")
        sec.agregar_widget(ctk.CTkLabel(
            sec, text=f"Precio unitario: {fmt_money(self.resultado.total)}",
            text_color=COLOR_TEXTO_SECUNDARIO), pady=(0, 10))

    def _crear_opciones(self, master, fila: int) -> None:
        sec = self._seccion(master, fila, "Opciones")
        self.e_vigencia = sec.agregar_campo("Vigencia (días)", str(self.preferencias.vigencia))
        self.chk_iva = ctk.CTkCheckBox(sec, text="Agregar IVA (16%)")
        if self.preferencias.incluir_iva:
            self.chk_iva.select()
        sec.agregar_widget(self.chk_iva)
        sec.agregar_widget(ctk.CTkLabel(sec, text="Términos y condiciones (uno por línea)"),
                           pady=(8, 2))
        self.t_condiciones = ctk.CTkTextbox(sec, height=90, wrap="word")
        self.t_condiciones.insert("1.0", self.preferencias.condiciones)
        sec.agregar_widget(self.t_condiciones, sticky="ew", pady=(0, 10))

    def _crear_empresa(self, master, fila: int) -> None:
        emp = self.preferencias.empresa
        sec = self._seccion(master, fila, "Datos de tu empresa (se guardan)")
        self.e_emp_nombre = sec.agregar_campo("Nombre / razón social", emp.nombre)
        self.e_emp_dir = sec.agregar_campo("Dirección", emp.direccion)
        self.e_emp_tel = sec.agregar_campo("Teléfono", emp.telefono)
        self.e_emp_correo = sec.agregar_campo("Correo", emp.correo)
        self.e_emp_rfc = sec.agregar_campo("RFC", emp.rfc)
        self.e_emp_atiende = sec.agregar_campo("Atiende / firma", emp.atiende)
        self.e_emp_logo = sec.agregar_campo("Logo (PNG/JPG)", emp.logo)
        sec.agregar_widget(ctk.CTkButton(sec, text="Buscar logo…", width=120,
                                         command=self._buscar_logo), sticky="e", pady=(0, 10))

    def _crear_botones(self) -> None:
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=1, column=0, sticky="ew", padx=12, pady=12)
        barra.grid_columnconfigure((0, 1, 2), weight=1)
        boton_secundario(barra, "Cancelar", self.destroy).grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkButton(barra, text="Vista previa (PDF)", command=self.vista_previa).grid(
            row=0, column=1, padx=4, sticky="ew")
        boton_principal(barra, "🖨  Imprimir", self.imprimir, font=fuente(14, negrita=True)).grid(
            row=0, column=2, padx=4, sticky="ew")

    def _enfocar(self) -> None:
        self.lift()
        self.focus_force()
        self.grab_set()
        self.e_cliente.focus_set()

    def _buscar_logo(self) -> None:
        ruta = filedialog.askopenfilename(
            parent=self, title="Selecciona el logo",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg"), ("Todos", "*.*")])
        if ruta:
            self.e_emp_logo.delete(0, "end")
            self.e_emp_logo.insert(0, ruta)

    # ----- Acciones -------------------------------------------------------

    def vista_previa(self) -> None:
        ruta = self._emitir()
        if ruta:
            abrir_archivo(ruta)
            self.on_estado(f"✔ Vista previa generada:\n{ruta}")

    def imprimir(self) -> None:
        ruta = self._emitir()
        if not ruta:
            return
        folio = self.e_folio.get().strip()
        if imprimir_archivo(ruta):
            self.on_estado(f"✔ Cotización {folio} enviada a imprimir. Guardada en:\n{ruta}")
        else:
            self.on_estado(f"✔ Cotización {folio} abierta: usa Ctrl+P para imprimir.\n{ruta}")
        self.destroy()

    def _emitir(self) -> Path | None:
        """Valida el formulario y genera el PDF. Devuelve la ruta o None si hubo un problema."""
        try:
            documento = self._leer_documento()
        except ValueError as err:
            messagebox.showwarning("Faltan datos", str(err), parent=self)
            return None

        consumir = documento.folio == self.folio_sugerido and not self.folio_consumido
        try:
            ruta = self.servicio.emitir(documento, self.preferencias, consumir_folio=consumir)
        except PermissionError:
            messagebox.showerror(
                "No se pudo guardar",
                "El PDF está abierto en otro programa. Ciérralo e inténtalo de nuevo.",
                parent=self)
            return None
        except Exception as err:  # noqa: BLE001 - mostrar cualquier error al usuario
            messagebox.showerror("Error al generar PDF", str(err), parent=self)
            return None
        self.folio_consumido = self.folio_consumido or consumir
        return ruta

    def _leer_documento(self) -> DocumentoCotizacion:
        """Construye el documento a partir del formulario. Lanza ValueError si falta algo."""
        nombre_cliente = self.e_cliente.get().strip()
        if not nombre_cliente:
            raise ValueError("Escribe el nombre del cliente.")

        return DocumentoCotizacion(
            empresa=Empresa(
                nombre=self.e_emp_nombre.get().strip() or EMPRESA_NOMBRE_DEFAULT,
                direccion=self.e_emp_dir.get().strip(),
                telefono=self.e_emp_tel.get().strip(),
                correo=self.e_emp_correo.get().strip(),
                rfc=self.e_emp_rfc.get().strip(),
                atiende=self.e_emp_atiende.get().strip(),
                logo=self.e_emp_logo.get().strip(),
            ),
            cliente=Cliente(
                nombre=nombre_cliente,
                telefono=self.e_tel_cliente.get().strip(),
                direccion=self.e_obra.get().strip(),
            ),
            folio=self.e_folio.get().strip() or self.folio_sugerido,
            precio_unitario=round(self.resultado.total, 2),
            cantidad=parse_entero(self.e_cantidad.get(), "Cantidad de ventanas", minimo=1),
            descripcion=self.e_desc.get().strip() or DESCRIPCION_DEFAULT,
            medidas=self.e_medidas.get().strip(),
            incluye=describir_materiales(self.datos),
            vigencia_dias=parse_entero(self.e_vigencia.get(), "Vigencia", minimo=0),
            incluir_iva=bool(self.chk_iva.get()),
            condiciones=self.t_condiciones.get("1.0", "end").strip().splitlines(),
        )
