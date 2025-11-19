import flet as ft
from flet import Icons, Colors 

def create_social_select_view(page: ft.Page) -> ft.View:

    # --- 1. Función corregida: Crear SnackBar explícitamente ---
    def handle_selection(e):
        platform = e.control.data
        
        # Navegación
        if platform == "reddit":
            page.go("/dashboard/reddit")
        elif platform == "mastodon":
            page.go("/dashboard/mastodon")
        elif platform == "facebook":
            page.go("/dashboard/facebook")
        else:
            page.go("/login") 
        
        # CORRECCIÓN: Creamos y asignamos el SnackBar directamente
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Cargando dashboard de: {platform.capitalize()}..."),
            bgcolor=Colors.TEAL_700
        )
        page.snack_bar.open = True
        page.update()

    # --- Componente de tarjeta (Sin cambios) ---
    def create_platform_card(title, icon, color, platform_key):
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(icon, size=50, color=color), 
                        ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
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

    # --- 2. Función Scraper corregida ---
    def run_scrapers_and_show_log(e):
        if page.data and "run_all_scrapers_func" in page.data:
            run_func = page.data["run_all_scrapers_func"]
            run_func(e) 
            
            # CORRECCIÓN: Creamos y asignamos el SnackBar directamente
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Iniciando actualización en segundo plano... (Revisa la terminal)"),
                bgcolor=Colors.TEAL_700
            )
            page.snack_bar.open = True
            page.update()
            
        else:
            print("Error: La función 'run_all_scrapers_func' no está en 'page.data'.")
            # CORRECCIÓN: SnackBar de error
            page.snack_bar = ft.SnackBar(
                content=ft.Text("¡Error! No se pudo iniciar el scrape. Reinicia la app."),
                bgcolor=Colors.RED_700
            )
            page.snack_bar.open = True
            page.update()

    # --- Layout de la Vista ---
    return ft.View(
        "/social_select",
        [
            ft.AppBar(title=ft.Text("🌐 Selecciona tu Fuente de Datos"), bgcolor=Colors.TEAL_700),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("¿Qué red social deseas analizar hoy?", size=32, weight=ft.FontWeight.BOLD),
                        ft.Text("Cada selección te llevará a un dashboard individual.", italic=True, color=Colors.GREY_500),
                        ft.Container(height=40),
                        
                        ft.Row(
                            [
                                create_platform_card(
                                    "Reddit", 
                                    Icons.REDDIT, 
                                    Colors.ORANGE_ACCENT_700, 
                                    "reddit"
                                ),
                                create_platform_card(
                                    "Mastodon", 
                                    Icons.HIDE_SOURCE, 
                                    Colors.PURPLE_500,
                                    "mastodon"
                                ),
                                create_platform_card(
                                    "Facebook", 
                                    Icons.FACEBOOK, 
                                    Colors.BLUE_800,
                                    "facebook"
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=50
                        ),
                        
                        ft.Container(height=50),
                        
                        ft.Row(
                            [
                                ft.TextButton(
                                    "Volver al Login",
                                    icon=Icons.ARROW_BACK, 
                                    on_click=lambda e: page.go("/login")
                                ),
                                ft.ElevatedButton(
                                    "Actualizar Datos",
                                    icon=Icons.REFRESH,
                                    on_click=run_scrapers_and_show_log,
                                    bgcolor=Colors.TEAL_700,
                                    color=Colors.WHITE,       
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=20 
                        )
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