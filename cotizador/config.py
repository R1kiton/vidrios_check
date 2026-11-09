"""
Constantes y valores por defecto de la aplicación.

Para cambiar precios o valores iniciales sólo hay que editar este archivo.
"""

APP_TITLE = "Cotizador de Ventanas de Aluminio"
APP_ID = "CotizadorVentanas"  # nombre de carpeta para la configuración del usuario

# --- Medidas iniciales de la ventana (metros) ---
ANCHO_DEFAULT = 1.50
ALTO_DEFAULT = 1.20

# --- Catálogo de fábrica: (nombre, precio fijo por metro, veces alto, veces ancho) ---
# Metros del perfil = veces_alto × alto + veces_ancho × ancho
#   Jamba:      alto + ancho + alto   -> 2 × alto + 1 × ancho
#   Zoclo:      ancho + ancho         -> 2 × ancho
#   Traslape:   alto + alto           -> 2 × alto
#   Cerco:      alto + alto           -> 2 × alto
#   Riel:       ancho                 -> 1 × ancho
#   Mosquitero: alto + ancho + alto   -> 2 × alto + 1 × ancho
# Los valores vigentes los edita el usuario desde "Modificar precios" y se guardan
# en catalogo.json; estos sólo se usan la primera vez o al "Restaurar de fábrica".
PERFILES_DEFAULT: tuple[tuple[str, float, float, float], ...] = (
    ("Jamba", 100.0, 2, 1),
    ("Riel", 55.0, 0, 1),
    ("Zoclo", 55.0, 0, 2),
    ("Traslape", 70.0, 2, 0),
    ("Cerco", 70.0, 2, 0),
    ("Mosquitero", 30.0, 2, 1),
)

# --- Vidrio, herrajes y márgenes ---
VIDRIO_AREA_DEFAULT = 1.8      # m²
VIDRIO_PRECIO_DEFAULT = 380.0  # $ por m²
HERRAJES_DEFAULT = 250.0       # $ costo fijo
MARGEN1_DEFAULT = 30.0         # % ganancia base
MARGEN2_DEFAULT = 30.0         # % gasto / margen secundario

# --- Cotización impresa ---
TASA_IVA = 0.16
PREFIJO_FOLIO = "COT"
VIGENCIA_DEFAULT = 15  # días
DESCRIPCION_DEFAULT = "Ventana de aluminio corrediza"
EMPRESA_NOMBRE_DEFAULT = "Mi Empresa de Aluminio"
CONDICIONES_DEFAULT = (
    "Precios expresados en pesos mexicanos (MXN).\n"
    "Esta cotización tiene una vigencia de {vigencia} días a partir de su fecha de emisión.\n"
    "Los precios pueden variar si cambian las medidas o especificaciones solicitadas."
)
