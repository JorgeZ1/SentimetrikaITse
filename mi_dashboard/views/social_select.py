import flet as ft
# Importamos con mayúsculas, como especificaste para tu versión
from flet import Icons, Colors 

def create_social_select_view(page: ft.Page) -> ft.View:

    # 1. Función para manejar la selección y navegación
    def handle_selection(e):
        platform = e.control.data
        
        # Esto es correcto: siempre vamos al dashboard principal
        page.go("/dashboard") 
        
        page.snack_bar = ft.SnackBar( # type: ignore
            # Usamos Colors con mayúscula
            ft.Text(f"Seleccionaste: {platform.capitalize()}. Cargando Dashboard..."), 
            duration=3000, 
            bgcolor=Colors.GREEN_700
        )
        page.snack_bar.open = True # type: ignore
        page.update()

    # 2. Componente de tarjeta de selección
    def create_platform_card(title, icon, color, platform_key):
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(icon, size=50, color=color), # 'Icon' con mayúscula
                        ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                        # 'Colors' con mayúscula
                        ft.Text("Analizar datos y sentimientos", size=12, color=Colors.ON_SURFACE_VARIANT), 
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10
                ),
                width=220,
                height=180,
                alignment=ft.alignment.center,
                on_click=handle_selection,
                data=platform_key, 
                ink=True,
                padding=ft.padding.all(20)
            ),
            elevation=8,
            width=240,
            height=200,
        )

    return ft.View(
        "/social_select",
        [
            # 'Colors' con mayúscula
            ft.AppBar(title=ft.Text("🌐 Selecciona tu Fuente de Datos"), bgcolor=Colors.BLUE_700),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("¿Qué red social deseas analizar hoy?", size=32, weight=ft.FontWeight.BOLD),
                        # 'Colors' con mayúscula
                        ft.Text("Los datos se mostrarán en el dashboard principal.", italic=True, color=Colors.GREY_500),
                        ft.Container(height=40),
                        
                        # --- CAMBIO PRINCIPAL AQUÍ ---
                        ft.Row(
                            [
                                # 1. Reddit (se mantiene)
                                create_platform_card(
                                    "Reddit", 
                                    Icons.REDDIT, # 'Icons' mayúscula
                                    Colors.ORANGE_ACCENT_700, # 'Colors' mayúscula
                                    "reddit"
                                ),
                                
                                # 2. Mastodon (nuevo)
                                create_platform_card(
                                    "Mastodon", 
                                    Icons.HIDE_SOURCE, # 'Icons' mayúscula
                                    Colors.BLUE_500,   # 'Colors' mayúscula
                                    "mastodon"
                                ),
                                
                                # 3. Discord (nuevo)
                                create_platform_card(
                                    "Discord", 
                                    Icons.DISCORD, # 'Icons' mayúscula
                                    Colors.INDIGO_400, # 'Colors' mayúscula
                                    "discord"
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=50
                        ),
                        # --- FIN DEL CAMBIO ---
                        
                        ft.Container(height=50),
                        ft.TextButton("Volver al Login", on_click=lambda e: page.go("/login"))
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20
                ),
                padding=50
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
    )