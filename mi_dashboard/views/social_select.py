import flet as ft

def create_social_select_view(page: ft.Page) -> ft.View:

    # 1. Función para manejar la selección y navegación
    def handle_selection(e):
        platform = e.control.data
        
        # --- CAMBIO CLAVE AQUÍ: Redirigir siempre a la ruta de Reddit ---
        # Mantenemos 'platform' para la notificación, pero el destino es fijo.
        page.go("/dashboard") 
        # -------------------------------------------------------------
        
        page.snack_bar = ft.SnackBar(
            ft.Text(f"Seleccionaste: {platform.capitalize()}. Cargando Dashboard de Reddit (Integración en curso)..."), 
            duration=3000, 
            bgcolor=ft.Colors.GREEN_700
        )
        page.snack_bar.open = True
        page.update()

    # 2. Componente de tarjeta de selección (mantener el código sin cambios)
    def create_platform_card(title, icon, color, platform_key):
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(icon, size=50, color=color),
                        ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                        ft.Text("Analizar datos y sentimientos", size=12, color=ft.Colors.ON_SURFACE_VARIANT),
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
            # [ELIMINADO] border_radius no es un argumento válido para ft.Card
        )

    return ft.View(
        # ... (el resto de la vista permanece igual)
        "/social_select",
        [
            ft.AppBar(title=ft.Text("🌐 Selecciona tu Fuente de Datos"), bgcolor=ft.Colors.BLUE_700),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("¿Qué red social deseas analizar hoy?", size=32, weight=ft.FontWeight.BOLD),
                        ft.Text("Actualmente solo Reddit tiene integración completa.", italic=True, color=ft.Colors.RED_400),
                        ft.Container(height=40),
                        ft.Row(
                            [
                                create_platform_card("Reddit", ft.Icons.REDDIT, ft.Colors.ORANGE_ACCENT_700, "reddit"),
                                # --- CORRECCIÓN: Usar un icono compatible (CHAT_BUBBLE_OUTLINE) ---
                                create_platform_card("Twitter/X", ft.Icons.CHAT_BUBBLE_OUTLINE, ft.Colors.BLACK, "twitter"),
                                # ------------------------------------------------------------------
                                create_platform_card("Instagram", ft.Icons.CHAT_BUBBLE_OUTLINE, ft.Colors.PINK_400, "instagram"),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=50
                        ),
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
