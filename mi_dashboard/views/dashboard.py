# views/dashboard.py
import flet as ft
from data import posts
from utils import get_impact_icon
from theme import TEXT_DARK


def create_dashboard_view(page: ft.Page):
    return ft.View(
        "/dashboard",
        controls=[
            ft.Column(
                [
                    ft.Text(
                        "Dashboard de Publicaciones",
                        size=24,
                        weight="bold",
                        color=TEXT_DARK,
                    ),
                    ft.ResponsiveRow(
                        [
                            ft.Card(
                                content=ft.Container(
                                    padding=15,
                                    width=300,
                                    on_click=lambda e, id=post["id"]: page.go(f"/comments/{id}"),
                                    content=ft.Column(
                                        [
                                            # Imagen de la publicación
                                            ft.Image(
                                                src=post.get("image", "assets/default_post.png"),
                                                height=150,
                                                fit=ft.ImageFit.COVER,
                                            ),
                                            # Título
                                            ft.Text(
                                                post["title"],
                                                size=16,
                                                weight="bold",
                                                color=TEXT_DARK,
                                            ),
                                            # Estado con icono
                                            ft.Row(
                                                [
                                                    ft.Text("Impacto:"),
                                                    get_impact_icon(post["impact"]),
                                                ],
                                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                            ),
                                        ],
                                        spacing=10,
                                    ),
                                ),
                                col={"xs": 12, "sm": 6, "md": 4},
                            )
                            for post in posts
                        ],
                        spacing=20,
                        run_spacing=20,
                    ),
                ],
                spacing=20,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        vertical_alignment=ft.MainAxisAlignment.START,
    )
