import flet as ft

# --- PALETA DE COLORES OSCURA/GRISÁCEA ---

# Tema Principal
PRIMARY_DARK = ft.Colors.BLUE_900
PRIMARY = ft.Colors.BLUE_700
PRIMARY_LIGHT = ft.Colors.BLUE_400

# Acentos
ACCENT = ft.Colors.TEAL_600
ACCENT_LIGHT = ft.Colors.TEAL_300

# Fondos - TEMA OSCURO
BG_LIGHT = ft.Colors.GREY_900           # #212121 - Fondo principal oscuro
BG_CARD = ft.Colors.GREY_800            # #424242 - Tarjetas gris oscuro
BG_DARK = ft.Colors.BLACK               # #000000 - Secciones más oscuras

# Texto - Ajustado para fondo oscuro
TEXT_PRIMARY = ft.Colors.GREY_100       # #F5F5F5 - Texto principal claro
TEXT_SECONDARY = ft.Colors.GREY_400     # #BDBDBD - Texto secundario
TEXT_ON_PRIMARY = ft.Colors.WHITE       # #FFFFFF - Texto sobre colores oscuros

# Redes Sociales
REDDIT_COLOR = ft.Colors.DEEP_ORANGE_600
MASTODON_COLOR = ft.Colors.PURPLE_600
FACEBOOK_COLOR = ft.Colors.BLUE_800

# Sentimientos
SENTIMENT_POSITIVE = ft.Colors.GREEN_600
SENTIMENT_NEGATIVE = ft.Colors.RED_600
SENTIMENT_NEUTRAL = ft.Colors.GREY_500

# Estados
SUCCESS = ft.Colors.GREEN_700
ERROR = ft.Colors.RED_700
WARNING = ft.Colors.ORANGE_700
INFO = ft.Colors.BLUE_600

def get_theme() -> ft.Theme:
    """
    Devuelve el objeto Theme configurado para modo oscuro.
    """
    theme = ft.Theme()
    theme.color_scheme_seed = ft.Colors.BLUE_700
    theme.use_material3 = True
    return theme