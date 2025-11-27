import flet as ft
from flet import Colors, Icons

# --- Configuración de Redes ---
SOCIAL_NETWORKS = [
    {
        "name": "Facebook",
        "icon": Icons.FACEBOOK,
        "color": "#1877F2", # Azul
        "route": "/dashboard/facebook",
        "desc": "Gestiona páginas y comentarios"
    },
    {
        "name": "Reddit",
        "icon": Icons.REDDIT,
        "color": "#FF4500", # Naranja
        "route": "/dashboard/reddit",
        "desc": "Analiza subreddits y tendencias"
    },
    {
        "name": "Mastodon",
        "icon": Icons.ROCKET_LAUNCH, 
        "color": "#6364FF", # Violeta
        "route": "/dashboard/mastodon",
        "desc": "Monitorea el fediverso"
    }
]

def create_social_select_view(page: ft.Page) -> ft.View:
    
    # --- Lógica de Tema (Día/Noche) ---
    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            theme_icon.icon = Icons.LIGHT_MODE
            theme_icon.tooltip = "Cambiar a Modo Claro"
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_icon.icon = Icons.DARK_MODE
            theme_icon.tooltip = "Cambiar a Modo Oscuro"
        page.update()

    initial_icon = Icons.DARK_MODE if page.theme_mode == ft.ThemeMode.LIGHT else Icons.LIGHT_MODE
    
    theme_icon = ft.IconButton(
        icon=initial_icon,
        icon_color="onSurface",
        on_click=toggle_theme,
        tooltip="Cambiar Tema"
    )

    def logout(e):
        page.go("/login")

    # --- Componente: Tarjeta de Red Social ---
    def create_network_card(network):
        
        # Lógica de Hover Personalizada (Color Brillante)
        def on_card_hover(e):
            container = e.control
            if e.data == "true":
                # AL ENTRAR: Escalar y cambiar sombra al color de la red
                container.scale = 1.05
                container.shadow = ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=20,
                    color=network["color"], # <--- AQUÍ ESTÁ EL BRILLO DEL COLOR DE LA RED
                    offset=ft.Offset(0, 0)
                )
                # Opcional: Cambiar borde al color de la red
                container.border = ft.border.all(2, network["color"])
            else:
                # AL SALIR: Regresar a estado normal (sombra negra suave)
                container.scale = 1.0
                container.shadow = ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=10,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                    offset=ft.Offset(0, 4)
                )
                container.border = ft.border.all(1, "outlineVariant")
            
            container.update()

        return ft.Container(
            content=ft.Column([
                # Icono
                ft.Container(
                    content=ft.Icon(network["icon"], size=40, color=network["color"]),
                    padding=15,
                    bgcolor=ft.Colors.with_opacity(0.1, network["color"]),
                    border_radius=50,
                ),
                ft.Divider(height=10, color="transparent"),
                # Título
                ft.Text(
                    network["name"], 
                    size=20, 
                    weight=ft.FontWeight.BOLD, 
                    color="onSurface"
                ),
                # Descripción
                ft.Text(
                    network["desc"], 
                    size=12, 
                    color="onSurfaceVariant", 
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Divider(height=10, color="transparent"),
                # Botón visual (simulado)
                ft.Container(
                    content=ft.Text("Entrar", size=12, weight="bold", color=network["color"]),
                    padding=ft.padding.symmetric(horizontal=20, vertical=8),
                    border=ft.border.all(1, network["color"]),
                    border_radius=20
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER),
            
            # --- ESTILOS VISUALES ---
            width=320,
            height=350,
            
            # CORRECCIÓN: Usamos "surface" para que sea Blanco en Día y Gris en Noche
            bgcolor="surface", 
            
            border=ft.border.all(1, "outlineVariant"),
            border_radius=20,
            padding=25,
            
            # Sombra inicial (neutra)
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 4)
            ),
            
            # Animaciones e Interactividad
            ink=True,
            animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT), # Suavizado
            on_click=lambda _: page.go(network["route"]),
            on_hover=on_card_hover # <--- Vinculamos la función de brillo
        )

    # --- Construcción de la Grilla ---
    cards_layout = ft.Row(
        controls=[create_network_card(net) for net in SOCIAL_NETWORKS],
        alignment=ft.MainAxisAlignment.CENTER,
        wrap=True,
        spacing=30,
        run_spacing=30
    )



    # --- Vista Final ---
    return ft.View(
        "/social_select",
        bgcolor="background", # Fondo general adaptable
        appbar=ft.AppBar(
            leading=ft.Icon(Icons.ANALYTICS, color="primary"),
            title=ft.Text("Sentimetrika Hub", weight=ft.FontWeight.BOLD, color="onSurface"),
            center_title=False,
            bgcolor="surface",
            elevation=0,
            actions=[
                theme_icon,
                ft.IconButton(
                    icon=Icons.LOGOUT,
                    icon_color="error", 
                    tooltip="Cerrar Sesión",
                    on_click=logout
                ),
                ft.Container(width=15)
            ]
        ),
        controls=[
            ft.Container(
                content=ft.Column([
                    ft.Column([
                        ft.Text("Bienvenido al Panel de Control", size=32, weight=ft.FontWeight.BOLD, color="onSurface"),
                        ft.Text("Selecciona una red social para gestionar y analizar.", 
                               size=16, color="onSurfaceVariant")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                    
                    ft.Divider(height=40, color="transparent"),
                    
                    cards_layout
                    
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                
                padding=ft.padding.symmetric(vertical=50, horizontal=20),
                alignment=ft.alignment.center,
                expand=True 
            )
        ]
    )