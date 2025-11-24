# views/register.py
import flet as ft
import re
from mi_dashboard.auth import register_user
from mi_dashboard.theme import TEXT_DARK, PRIMARY_COLOR, ACCENT_MAGENTA

def create_register_view(page: ft.Page):
    """
    Crea la vista de registro, centrada y con confirmación de contraseña, 
    utilizando un diseño de tarjeta (card).
    """
    
    # Controles de la interfaz de usuario con colores claros
    email = ft.TextField(
        label="Correo electrónico",
        width=300,
        border_radius=8,
        border_color=PRIMARY_COLOR,
        bgcolor=ft.Colors.WHITE,
        color=ft.Colors.BLACK,  # 👈 Color del texto que se escribe
    )
    password = ft.TextField(
        label="Contraseña",
        password=True,
        can_reveal_password=True,
        width=300,
        border_radius=8,
        border_color=PRIMARY_COLOR,
        bgcolor=ft.Colors.WHITE,
        color=ft.Colors.BLACK,  # 👈 Color del texto que se escribe
    )
    confirm_password = ft.TextField(
        label="Confirmar contraseña",
        password=True,
        can_reveal_password=True,
        width=300,
        border_radius=8,
        border_color=PRIMARY_COLOR,
        bgcolor=ft.Colors.WHITE,
        color=ft.Colors.BLACK,  # 👈 Color del texto que se escribe
    )
    error_text = ft.Text("", style=ft.TextStyle(color=ACCENT_MAGENTA))
    
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
            error_text.value = "⚠️ Todos los campos son obligatorios"
        elif not is_valid_email(email.value):
            error_text.value = "⚠️ Correo electrónico no válido"
        elif not is_valid_password(password.value):
            error_text.value = "⚠️ La contraseña debe tener al menos 8 caracteres, incluir letras y números"
        elif password.value != confirm_password.value:
            error_text.value = "⚠️ Las contraseñas no coinciden"
        elif register_user(email.value, password.value):
            page.go("/login")
        else:
            error_text.value = "⚠️ El usuario ya existe"
        page.update()

    # ---------- Estructura de la Vista con la tarjeta ----------
    return ft.View(
        "/register",
        bgcolor=ft.Colors.WHITE,
        controls=[
            # Contenedor para centrar el formulario
            ft.Container(
                alignment=ft.alignment.center,
                expand=True,
                # El formulario como una tarjeta
                content=ft.Container(
                    width=400,
                    height=550,
                    padding=40,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=20,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=15,
                        color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                        offset=ft.Offset(0, 0),
                    ),
                    # El contenido dentro de la tarjeta
                    content=ft.Column(
                        [
                            ft.Text(
                                "Crea tu cuenta",
                                style=ft.TextStyle(size=28, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                            ),
                            email,
                            password,
                            confirm_password,
                            error_text,
                            ft.ElevatedButton(
                                "Registrarme",
                                on_click=register_action,
                                bgcolor=PRIMARY_COLOR,
                                color=ft.Colors.WHITE,
                                height=45,
                                width=300,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12)
                                ),
                            ),
                            ft.TextButton(
                                "Ya tengo cuenta, iniciar sesión",
                                on_click=lambda _: page.go("/login"),
                                style=ft.ButtonStyle(color=PRIMARY_COLOR)
                            ),
                        ],
                        spacing=20,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ),
            )
        ],
    )