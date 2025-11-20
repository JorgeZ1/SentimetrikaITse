import flet as ft
from flet import Icons, Colors, FontWeight, TextThemeStyle, BoxShadow, Offset

def create_social_select_view(page: ft.Page) -> ft.View:

    # --- 1. LÓGICA DE NAVEGACIÓN ---
    def handle_selection(e):
        platform = e.control.data
        
        # Feedback visual
        page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(Icons.ROCKET_LAUNCH, color=Colors.WHITE),
                ft.Text(f"Entrando a {platform.capitalize()}...", weight=FontWeight.BOLD)
            ], spacing=10),
            bgcolor=Colors.BLUE_GREY_900,
            duration=2000
        )
        page.snack_bar.open = True
        page.update()

        # Navegación
        if platform == "reddit": page.go("/dashboard/reddit")
        elif platform == "mastodon": page.go("/dashboard/mastodon")
        elif platform == "facebook": page.go("/dashboard/facebook")
        else: page.go("/login") 

    # --- 2. COMPONENTE: TARJETA INTERACTIVA (HOVER) ---
    def create_hover_card(title, icon, color, platform_key, description):
        
        def on_hover(e):
            is_hover = e.data == "true"
            e.control.scale = 1.05 if is_hover else 1.0
            e.control.shadow = BoxShadow(
                blur_radius=20 if is_hover else 5,
                color=color if is_hover else Colors.BLACK12,
                offset=Offset(0, 10 if is_hover else 2)
            )
            e.control.update()

        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=60, color=color),
                    ft.Text(title, size=20, weight=FontWeight.BOLD, color=Colors.BLUE_GREY_900),
                    ft.Text(description, size=12, color=Colors.GREY_500, text_align=ft.TextAlign.CENTER),
                    ft.Container(
                        content=ft.Text("VER DASHBOARD", size=10, weight=FontWeight.BOLD, color=Colors.WHITE),
                        bgcolor=color,
                        padding=ft.padding.symmetric(horizontal=15, vertical=8),
                        border_radius=20,
                        margin=ft.margin.only(top=10)
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5
            ),
            width=260,
            height=280,
            bgcolor=Colors.WHITE,
            border_radius=20,
            padding=30,
            
            # Animaciones
            scale=1, 
            animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            shadow=BoxShadow(blur_radius=5, color=Colors.BLACK12, offset=Offset(0, 2)),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            
            # Eventos
            on_click=handle_selection,
            on_hover=on_hover,
            data=platform_key
        )

    # --- LAYOUT PRINCIPAL ---
    return ft.View(
        "/social_select",
        [
            ft.Container(
                image=ft.DecorationImage(
                    src="assets/login_bg.png", 
                    fit=ft.ImageFit.COVER,
                    opacity=0.05
                ),
                expand=True,
                bgcolor=Colors.BLUE_GREY_50,
                content=ft.Column(
                    [
                        # Header
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(Icons.ANALYTICS, color=Colors.TEAL_700, size=30),
                                ft.Text("Sentimetrika Hub", size=20, weight=FontWeight.BOLD, color=Colors.BLUE_GREY_800),
                                ft.Container(expand=True),
                                ft.IconButton(Icons.LOGOUT, tooltip="Cerrar Sesión", icon_color=Colors.RED_400, on_click=lambda e: page.go("/login"))
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            padding=ft.padding.symmetric(horizontal=40, vertical=20)
                        ),

                        # Contenido Central
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text("Selecciona una Fuente de Datos", style=TextThemeStyle.HEADLINE_MEDIUM, weight=FontWeight.BOLD, color=Colors.BLUE_GREY_900),
                                    ft.Text("Analiza sentimientos y tendencias en tiempo real", size=16, color=Colors.BLUE_GREY_400),
                                    
                                    ft.Container(height=40),
                                    
                                    ft.Row(
                                        [
                                            create_hover_card(
                                                "Facebook", 
                                                Icons.FACEBOOK, 
                                                Colors.BLUE_800, 
                                                "facebook",
                                                "Páginas, Comentarios y Reacciones"
                                            ),
                                            create_hover_card(
                                                "Reddit", 
                                                Icons.REDDIT, 
                                                Colors.DEEP_ORANGE_ACCENT_700, 
                                                "reddit",
                                                "Hilos, Discusiones y Karmas"
                                            ),
                                            create_hover_card(
                                                "Mastodon", 
                                                Icons.HUB, 
                                                Colors.PURPLE_500, 
                                                "mastodon",
                                                "Toots, Instancias y Fediverso"
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=30,
                                        wrap=True
                                    ),
                                    
                                    ft.Container(height=40), # Reducido este espacio
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            expand=True,
                            alignment=ft.alignment.center
                        ),
                        
                        # Footer
                        ft.Container(
                            content=ft.Text("© 2025 Sentimetrika Project - Powered by Python & Flet", size=10, color=Colors.GREY_400),
                            padding=20,
                            alignment=ft.alignment.center
                        )
                    ]
                )
            )
        ],
        padding=0
    )