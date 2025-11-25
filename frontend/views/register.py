# views/register.py
import flet as ft
import re
from frontend.auth import register_user
from frontend.theme import TEXT_PRIMARY, PRIMARY, ACCENT, TEXT_ON_PRIMARY, BG_CARD, BG_DARK

def create_register_view(page: ft.Page):
    """
    Crea la vista de registro con imagen de fondo y formulario centrado.
    """
    
    # Controles de la interfaz de usuario
    email = ft.TextField(
        label="Correo electrónico",
        width=300,
        border_radius=8,
        border_color=PRIMARY,
        bgcolor=BG_DARK,
        color=TEXT_PRIMARY,
    )
    password = ft.TextField(
        label="Contraseña",
        password=True,
        can_reveal_password=True,
        width=300,
        border_radius=8,
        border_color=PRIMARY,
        bgcolor=BG_DARK,
        color=TEXT_PRIMARY,
    )
    confirm_password = ft.TextField(
        label="Confirmar contraseña",
        password=True,
        can_reveal_password=True,
        width=300,
        border_radius=8,
        border_color=PRIMARY,
        bgcolor=BG_DARK,
        color=TEXT_PRIMARY,
    )
    error_text = ft.Text("", style=ft.TextStyle(color=ACCENT))
    
    # ---------- Validaciones y Lógica ----------
    def is_valid_email(email_value: str) -> bool:
        return re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email_value) is not None

    def is_valid_password(password_value: str) -> bool:
        if len(password_value) < 8:
            return False
        has_letter = any(c.isalpha() for c in password_value)
        has_digit = any(c.isdigit() for c in password_value)
        return has_letter and has_digit

    def register_action(e):
        if not email.value or not password.value or not confirm_password.value:
            error_text.value = "Todos los campos son obligatorios"
        elif not is_valid_email(email.value):
            error_text.value = "Correo electrónico no válido"
        elif not is_valid_password(password.value):
            error_text.value = "La contraseña debe tener al menos 8 caracteres, incluir letras y números"
        elif password.value != confirm_password.value:
            error_text.value = "Las contraseñas no coinciden"
        elif register_user(email.value, password.value):
            page.go("/login")
        else:
            error_text.value = "El usuario ya existe"
        page.update()

    # ---------- Estructura de la Vista con imagen de fondo ----------
    return ft.View(
        "/register",
        controls=[
            # Container con imagen de fondo
            ft.Container(
                image=ft.DecorationImage(
                    src="/register.jpg",
                    fit=ft.ImageFit.COVER,
                    opacity=0.4  # Opacidad para que se vea mejor el formulario
                ),
                expand=True,
                alignment=ft.alignment.center,
                # Formulario centrado como tarjeta
                content=ft.Container(
                    width=400,
                    padding=40,
                    bgcolor=BG_CARD,
                    border_radius=20,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=15,
                        color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK),
                        offset=ft.Offset(0, 0),
                    ),
                    content=ft.Column(
                        [
                            ft.Image(src="/Sentimetrika.png", width=120),
                            ft.Text(
                                "Crea tu cuenta",
                                style=ft.TextStyle(size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ),
                            email,
                            password,
                            confirm_password,
                            error_text,
                            ft.ElevatedButton(
                                "Registrarme",
                                on_click=register_action,
                                bgcolor=PRIMARY,
                                color=TEXT_ON_PRIMARY,
                                height=45,
                                width=300,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12)
                                ),
                            ),
                            ft.TextButton(
                                "Ya tengo cuenta, iniciar sesión",
                                on_click=lambda _: page.go("/login"),
                                style=ft.ButtonStyle(color=PRIMARY)
                            ),
                        ],
                        spacing=20,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ),
            )
        ],
        padding=0
    )