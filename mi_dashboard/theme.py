import flet as ft

# --- Constantes de Color ---
PRIMARY_COLOR = ft.Colors.BLUE_800
ACCENT_MAGENTA = ft.Colors.PINK_ACCENT_700
TEXT_DARK = ft.Colors.GREY_900
TEXT_LIGHT = ft.Colors.WHITE

def get_theme():
    """
    Devuelve el objeto Theme configurado.
    """
    theme = ft.Theme()
    theme.color_scheme_seed = ft.Colors.BLUE
    theme.use_material3 = True
    # Hemos eliminado la línea de 'visual_density' para evitar el error en tu versión
    return theme