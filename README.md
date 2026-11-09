# Cotizador de Ventanas de Aluminio

Aplicación de escritorio para Windows que calcula el precio de una ventana de aluminio
(perfiles, vidrio, herrajes y márgenes) e imprime una cotización formal en PDF.

## Requisitos

- Windows 10/11
- Python 3.10 o superior (con *tcl/tk*, viene por defecto en el instalador oficial)

## Ejecutar localmente

```powershell
python -m pip install -r requirements.txt
python main.py
```

Desde **VS Code**: presiona `F5` (configuración *Cotizador de Ventanas* en `.vscode/launch.json`).
También funciona `python -m cotizador`.

> Siempre arranca desde `main.py`. Los archivos dentro de `cotizador/` son módulos de un
> paquete y no se pueden ejecutar directamente (darían `ImportError: attempted relative import`).

## Pruebas

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

Las pruebas cubren el cálculo, el formato (incluido el importe con letra), la
persistencia de preferencias y la generación del PDF. No requieren abrir la interfaz.

## Generar el ejecutable (.exe)

**Opción 1:** doble clic en `build.bat`. Instala dependencias, corre las pruebas y compila.

**Opción 2 – manual:**

```powershell
python -m pip install -r requirements.txt
python -m PyInstaller --noconsole --onefile --clean --name "CotizadorVentanas" --collect-data customtkinter main.py
```

Resultado: `dist\CotizadorVentanas.exe`, *standalone* (no necesita Python en la PC destino).

> Se usa `python -m PyInstaller` porque el comando `pyinstaller` a veces no está en el PATH.
> `--collect-data customtkinter` incluye los temas de la librería dentro del .exe.

## Estructura del proyecto

El código está organizado por capas: la lógica de negocio no depende de la interfaz,
lo que permite probarla y modificarla por separado.

```
ventanas_alumar/
├── main.py                      # Punto de entrada (sólo arranca la app)
├── cotizador/
│   ├── config.py                # Constantes y valores por defecto (precios, IVA, folio…)
│   ├── models.py                # Modelos de datos (Perfil, DatosCotizacion, DocumentoCotizacion…)
│   ├── calculos.py              # Reglas de negocio: cálculo del precio (funciones puras)
│   ├── formato.py               # Moneda, fechas, importe con letra, validación de entradas
│   ├── services/
│   │   ├── catalogo.py          # Lectura/escritura del catálogo de precios en JSON
│   │   ├── cotizaciones.py      # Caso de uso: emitir cotización (PDF + preferencias)
│   │   ├── pdf.py               # Diseño del PDF formal (reportlab)
│   │   ├── preferencias.py      # Lectura/escritura de preferencias en JSON
│   │   ├── rutas.py             # Ubicación de Documentos y de la configuración
│   │   └── sistema.py           # Abrir / imprimir archivos con Windows
│   └── ui/
│       ├── app.py               # Ventana principal (conecta paneles y servicios)
│       ├── panel_entrada.py     # Panel izquierdo: formulario de datos
│       ├── panel_resumen.py     # Panel derecho: desglose, total y botones
│       ├── dialogo_impresion.py # Ventana de datos del cliente para imprimir
│       ├── dialogo_precios.py   # Ventana para modificar los precios de perfiles
│       ├── widgets.py           # Componentes reutilizables (Seccion, FilaPerfil)
│       └── tema.py              # Colores, fuentes y estilos de botones
├── tests/                       # Pruebas automáticas (pytest)
├── requirements.txt             # Dependencias de ejecución
├── requirements-dev.txt         # Dependencias de desarrollo (pytest)
├── pyproject.toml               # Metadatos del proyecto y configuración de pytest
└── build.bat                    # Compila el .exe
```

Dependencias entre capas (de arriba hacia abajo, nunca al revés):

```
ui  →  services  →  calculos / formato  →  models  →  config
```

**¿Dónde cambio…?**

| Quiero cambiar… | Archivo |
|---|---|
| Precios de los perfiles | Botón **⚙ Modificar precios** dentro de la app |
| Precios *de fábrica* de perfiles, vidrio, herrajes o márgenes | `cotizador/config.py` |
| La fórmula del cálculo | `cotizador/calculos.py` |
| El diseño del PDF | `cotizador/services/pdf.py` |
| Colores de la interfaz | `cotizador/ui/tema.py` |

## Uso

| Sección | Qué se captura | Valores por defecto |
|---|---|---|
| Medidas de la ventana | Ancho y alto en metros (se dibuja la ventana a escala) | 1.50 m × 1.20 m |
| Perfiles de aluminio | Nada: los metros salen de las medidas y el precio por metro es fijo | Jamba $100, Riel $55, Zoclo $55, Traslape $70, Cerco $70, Mosquitero $30 |
| Vidrio | Área (m²) y precio por m² | 1.8 m² × $380 |
| Herrajes | Costo total fijo | $250 |
| Márgenes | Margen 1 (ganancia base) y Margen 2 (gasto/secundario) | 30% y 30% |

- Al escribir el **ancho** y el **alto** se redibuja la ventana y se recalculan los metros
  de cada perfil con su fórmula (ver *Lógica de cálculo*).
- **Precio de cada pieza** = metros × precio fijo por metro.
- **＋ Agregar perfil** añade una fila **en blanco** para capturar a mano nombre, metros y
  precio por metro de un perfil extra (sólo para esa cotización). **✕** quita cualquier
  fila (p. ej. una ventana sin mosquitero); *Restablecer valores* vuelve a cargar todos.
- **⚙ Modificar precios** abre una ventana para cambiar de forma **permanente** el
  catálogo: nombre, precio por metro y fórmula de cada perfil (*× Alto* y *× Ancho*).
  También permite agregar o eliminar perfiles y *Restaurar de fábrica*.
- **Calcular** (o `Enter` / `F5`) actualiza el resumen.
- **Restablecer valores** vuelve a cargar los valores por defecto.
- **🖨 Imprimir cotización** genera la cotización formal en PDF (ver abajo).
- El selector **Tema** cambia entre claro, oscuro o el del sistema.
- Se aceptan decimales con punto o coma (`3.5` o `3,5`).

## Cotización formal (PDF)

Al presionar **Imprimir cotización** se capturan:

- **Cliente**: nombre (obligatorio), teléfono y dirección/obra.
- **Concepto**: folio (consecutivo automático `COT-0001`, `COT-0002`…), descripción,
  medidas y cantidad de ventanas.
- **Opciones**: vigencia en días, IVA 16% y términos y condiciones
  (`{vigencia}` se reemplaza por los días capturados).
- **Datos de tu empresa**: nombre, dirección, teléfono, correo, RFC, quién firma y logo.
  Se guardan para la próxima vez.

**Vista previa (PDF)** abre el documento; **Imprimir** lo envía a la impresora
predeterminada (si el visor de PDF no permite impresión directa, lo abre para `Ctrl+P`).

El PDF incluye encabezado con datos de la empresa, folio, fecha y vigencia, datos del
cliente, tabla de conceptos, subtotal/IVA/total, **importe con letra**, términos y firma.
**No muestra costos internos ni márgenes.**

- Los PDF se guardan en `Documentos\Cotizaciones\` (ej. `COT-0001 - Juan Pérez.pdf`).
- Las preferencias se guardan en `%APPDATA%\CotizadorVentanas\config.json`.
- Los precios de perfiles se guardan en `%APPDATA%\CotizadorVentanas\catalogo.json`.

## Lógica de cálculo

Metros de cada perfil según las medidas de la ventana:

| Perfil | Fórmula | Con 1.50 × 1.20 m |
|---|---|---|
| Jamba | alto + ancho + alto | 3.90 m |
| Zoclo | ancho + ancho | 3.00 m |
| Traslape | alto + alto | 2.40 m |
| Cerco | alto + alto | 2.40 m |
| Riel | ancho | 1.50 m |
| Mosquitero | alto + ancho + alto | 3.90 m |

```
Metros perfil     = (× Alto) · alto + (× Ancho) · ancho
Precio pieza      = Metros × Precio por metro
Subtotal Aluminio = Σ precio de cada pieza
Subtotal Vidrio   = Área × Precio/m²
Costo Base        = Aluminio + Vidrio + Herrajes
```

Márgenes ("Forma de aplicar"):

- **Encadenado** (por defecto): `Etapa 1 = Base × (1 + M1%)`, `Etapa 2 = Etapa 1 × (1 + M2%)`
- **Global**: `Total = Base × (1 + M1% + M2%)`

### Ejemplo con valores por defecto (ventana de 1.50 × 1.20 m)

| Concepto | Monto |
|---|---|
| Subtotal aluminio (390 + 82.50 + 165 + 168 + 168 + 117) | $1,090.50 |
| Subtotal vidrio (1.8 × 380) | $684.00 |
| Herrajes | $250.00 |
| **Costo base** | **$2,024.50** |
| Margen 1 (30%) | $607.35 → Etapa 1 = $2,631.85 |
| Margen 2 (30% sobre Etapa 1) | $789.56 → Etapa 2 = $3,421.40 |
| **Precio final (encadenado)** | **$3,421.40** |
| Precio final (global, 60% sobre base) | $3,239.20 |
