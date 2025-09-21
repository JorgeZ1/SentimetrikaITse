# views/login.py
import flet as ft
from auth import authenticate
from theme import PRIMARY_COLOR, ACCENT_MAGENTA, TEXT_DARK

def create_login_view(page: ft.Page):
    email = ft.TextField(
        label="Correo electrónico",
        border_radius=8,
        border_color=PRIMARY_COLOR,
        width=320,
        filled=True,
        fill_color=ft.Colors.GREY_100,
        color=ft.Colors.BLACK # 👈 Color del texto que se escribe
    )
    password = ft.TextField(
        label="Contraseña",
        password=True,
        can_reveal_password=True,
        border_radius=8,
        border_color=PRIMARY_COLOR,
        width=320,
        filled=True,
        fill_color=ft.Colors.GREY_100,
        color=ft.Colors.BLACK  # 👈 Color del texto que se escribe
    )
    remember_me = ft.Checkbox(
        label="Recordar contraseña",
        fill_color=ACCENT_MAGENTA,
        label_style=ft.TextStyle(color=TEXT_DARK, size=16),
        value=False,
    )
    error_text = ft.Text("", color=ACCENT_MAGENTA)

    def login_action(e):
        if authenticate(email.value, password.value):
            page.go("/dashboard")
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
                                ft.Text("¡Bienvenido de nuevo!", size=24, weight="bold", color=TEXT_DARK),
                                email,
                                password,
                                remember_me,
                                error_text,
                                ft.ElevatedButton(
                                    "Iniciar sesión",
                                    bgcolor=PRIMARY_COLOR,
                                    color="white",
                                    height=45,
                                    width=320,
                                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                                    on_click=login_action,
                                ),
                                ft.TextButton(
                                    "¿Todavía no tienes cuenta? Regístrate",
                                    on_click=lambda _: page.go("/register"),
                                    style=ft.ButtonStyle(color=ACCENT_MAGENTA)
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