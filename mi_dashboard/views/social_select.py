import flet as ft
from flet import Icons, FontWeight, TextThemeStyle, BoxShadow, Offset
from typing import Callable
from mi_dashboard.theme import *

def create_social_select_view(page: ft.Page) -> ft.View:

    # --- 1. LÓGICA DE NAVEGACIÓN ---
    def handle_selection(e: ft.ControlEvent) -> None:
        platform = e.control.data
        
        # Feedback visual
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Cargando dashboard de: {platform.capitalize()}...", style=ft.TextStyle(color=TEXT_ON_PRIMARY)),
            bgcolor=INFO
        )
        page.snack_bar.open = True
        page.update()
        
        # Navegar al dashboard correspondiente
        page.go(f"/dashboard/{platform}")

    # --- Componente de tarjeta ---
    def create_platform_card(title: str, icon: str, color: str, platform_key: str) -> ft.Card:
        # Crear el container con efecto hover
        card_container = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=50, color=color), 
                    ft.Text(title, style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
                    ft.Text("Analizar datos y sentimientos", style=ft.TextStyle(size=12, color=TEXT_SECONDARY)), 
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
            padding=ft.padding.all(20),
            bgcolor=BG_CARD,
            border=ft.border.all(2, ft.Colors.TRANSPARENT),
            border_radius=12,
            animate=200,
        )
        
        # Eventos de hover
        def on_hover(e):
            if e.data == "true":
                card_container.border = ft.border.all(2, color)
                card_container.elevation = 12
            else:
                card_container.border = ft.border.all(2, ft.Colors.TRANSPARENT)
                card_container.elevation = 8
            card_container.update()
        
        card_container.on_hover = on_hover
        
        return ft.Card(
            content=card_container,
            elevation=8,
            width=240,
            height=200,
        )

    # --- 2. Función Scraper ---
    def run_scrapers_and_show_log(e: ft.ControlEvent) -> None:
        if page.data and "run_all_scrapers_func" in page.data:
            run_func: Callable = page.data["run_all_scrapers_func"]
            run_func(e) 
            
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Iniciando actualización en segundo plano... (Revisa la terminal)", style=ft.TextStyle(color=TEXT_ON_PRIMARY)),
                bgcolor=INFO
            )
            page.snack_bar.open = True
            page.update()
            
        else:
            print("Error: La función 'run_all_scrapers_func' no está en 'page.data'.")
            page.snack_bar = ft.SnackBar(
                content=ft.Text("¡Error! No se pudo iniciar el scrape. Reinicia la app.", style=ft.TextStyle(color=TEXT_ON_PRIMARY)),
                bgcolor=ERROR
            )
            page.snack_bar.open = True
            page.update()

    # --- LAYOUT PRINCIPAL ---
    return ft.View(
        "/social_select",
        [
            ft.AppBar(
                title=ft.Text("🌐 Selecciona tu Fuente de Datos", style=ft.TextStyle(color=TEXT_ON_PRIMARY)), 
                bgcolor=PRIMARY_DARK
            ),
            ft.Container(
                image=ft.DecorationImage(
                    src="assets/login_bg.png", 
                    fit=ft.ImageFit.COVER,
                    opacity=0.03
                ),
                expand=True,
                bgcolor=BG_LIGHT,
                content=ft.Column(
                    [
                        ft.Text(
                            "¿Qué red social deseas analizar hoy?", 
                            style=ft.TextStyle(size=32, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
                        ),
                        ft.Text(
                            "Cada selección te llevará a un dashboard individual.", 
                            style=ft.TextStyle(italic=True, color=TEXT_SECONDARY, size=14)
                        ),
                        ft.Container(height=40),
                        
                        ft.Row(
                            [
                                create_platform_card(
                                    "Reddit", 
                                    Icons.REDDIT, 
                                    REDDIT_COLOR, 
                                    "reddit"
                                ),
                                create_platform_card(
                                    "Mastodon", 
                                    Icons.HIDE_SOURCE, 
                                    MASTODON_COLOR,
                                    "mastodon"
                                ),
                                create_platform_card(
                                    "Facebook", 
                                    Icons.FACEBOOK, 
                                    FACEBOOK_COLOR,
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
                                    on_click=lambda e: page.go("/login"),
                                    style=ft.ButtonStyle(color=PRIMARY)
                                ),
                                ft.ElevatedButton(
                                    "Actualizar Datos",
                                    icon=Icons.REFRESH,
                                    on_click=run_scrapers_and_show_log,
                                    bgcolor=ACCENT,
                                    color=TEXT_ON_PRIMARY,       
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=20 
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        ],
        padding=0
    )
