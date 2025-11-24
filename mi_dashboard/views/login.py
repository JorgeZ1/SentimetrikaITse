import flet as ft
from mi_dashboard.auth import authenticate
from mi_dashboard.theme import PRIMARY, ACCENT, TEXT_PRIMARY, TEXT_ON_PRIMARY, BG_DARK
# Se asume que estos módulos (auth.py, theme.py) están definidos en tu proyecto.

def create_login_view(page: ft.Page):
    email = ft.TextField(
        label="Correo electrónico",
        border_radius=8,
        border_color=PRIMARY,
        width=320,
        filled=True,
        fill_color=ft.Colors.GREY_100,
        color=ft.Colors.BLACK
    )
    password = ft.TextField(
        label="Contraseña",
        password=True,
        can_reveal_password=True,
        border_radius=8,
        border_color=PRIMARY,
        width=320,
        filled=True,
        fill_color=ft.Colors.GREY_100,
        color=ft.Colors.BLACK
    )
    remember_me = ft.Checkbox(
        label="Recordar contraseña",
        fill_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_PRIMARY, size=16),
        value=False,
    )
    error_text = ft.Text("", style=ft.TextStyle(color=ACCENT))

    def login_action(e):
        if authenticate(email.value, password.value):
            # --- MODIFICACIÓN CLAVE: Redirigir a la selección de IA ---
            page.go("/social_select") 
            # ---------------------------------------------------------
        else:
            error_text.value = "⚠️ Usuario o contraseña incorrectos"
            page.update()

    return ft.View(
        "/login",
        controls=[
            ft.Row(
                [
                    # Lado izquierdo con imagen
                    ft.Container(
                        expand=True,
                        content=ft.Image(
                            src="login_bg.png",
                            fit=ft.ImageFit.COVER,
                            expand=True
                        ),
                    ),
                    # Lado derecho - Formulario
                    ft.Container(
                        width=450,
                        padding=40,
                        bgcolor="white",
                        content=ft.Column(
                            [
                                ft.Image(src="Sentimetrika.png", width=120),
                                ft.Text(
                                    "¡Bienvenido de nuevo!", 
                                    style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
                                ),
                                email,
                                password,
                                remember_me,
                                error_text,
                                ft.ElevatedButton(
                                    "Iniciar sesión",
                                    bgcolor=PRIMARY,
                                    color=TEXT_ON_PRIMARY,
                                    height=45,
                                    width=320,
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                                    on_click=login_action,
                                ),
                                ft.TextButton(
                                    "¿Todavía no tienes cuenta? Regístrate",
                                    on_click=lambda _: page.go("/register"),
                                    style=ft.ButtonStyle(color=ACCENT)
                                ),
                            ],
                            spacing=20,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        alignment=ft.alignment.center,
                    ),
                ],
                expand=True,
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
    )
