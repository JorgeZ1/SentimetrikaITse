# views/comments.py
import flet as ft
from data import comments
from theme import TEXT_DARK, ACCENT_MAGENTA


def create_comments_view(page: ft.Page, post_id: int):
    post_comments = comments.get(post_id, [])

    def get_comment_color(c: str):
        c_lower = c.lower()
        if "bueno" in c_lower or "excelente" in c_lower or "positivo" in c_lower:
            return "#D4F8E8"  # verde suave
        elif "malo" in c_lower or "terrible" in c_lower or "negativo" in c_lower:
            return "#FDDDDD"  # rojo suave
        else:
            return "#F0F0F0"  # neutro (gris claro)

    return ft.View(
        f"/comments/{post_id}",
        padding=20,
        controls=[
            ft.Column(
                [
                    # Header
                    ft.Row(
                        [
                            ft.Text(
                                "💬 Comentarios",
                                size=24,
                                weight="bold",
                                color=TEXT_DARK,
                            ),
                            ft.ElevatedButton(
                                "Volver",
                                bgcolor=ACCENT_MAGENTA,
                                color="white",
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12)
                                ),
                                on_click=lambda _: page.go("/dashboard"),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    # Lista de comentarios
                    ft.Column(
                        [
                            ft.Container(
                                padding=15,
                                border_radius=12,
                                bgcolor=get_comment_color(c),
                                shadow=ft.BoxShadow(
                                    spread_radius=1,
                                    blur_radius=6,
                                    color="#aaa",
                                    offset=ft.Offset(2, 2),
                                ),
                                content=ft.Text(c, color=TEXT_DARK, size=14),
                            )
                            for c in post_comments
                        ],
                        spacing=15,
                        expand=True,
                        scroll="auto",
                    ),
                ],
                spacing=20,
                expand=True,
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.START,
    )
