import flet as ft
from utils import procesar_y_agrupar_publicaciones, get_impact_icon

# Corregido a ft.Colors con 'C' mayúscula.
TEXT_DARK = ft.Colors.BLACK

def create_dashboard_view(page: ft.Page):
    
    datos_publicaciones = procesar_y_agrupar_publicaciones()
    
    lista_de_tarjetas = []
    if not datos_publicaciones:
        mensaje_ayuda = ft.Container(
            content=ft.Text(
                "No se encontraron datos. Asegúrate de haber ejecutado 'reddit_scraper.py' y 'analizador_local.py' con éxito.",
                size=16, color=ft.Colors.GREY_600 # Corregido
            ),
            alignment=ft.alignment.center, col=12, padding=50
        )
        lista_de_tarjetas.append(mensaje_ayuda)
    else:
        for publicacion in datos_publicaciones:
            card = ft.Card(
                content=ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.Text(publicacion["titulo"], size=18, weight="bold", color=TEXT_DARK),
                        ft.Divider(height=10, color=ft.Colors.GREY_300), # Corregido
                        ft.Row(
                            [
                                ft.Text("Impacto General:", size=16),
                                get_impact_icon(publicacion["impacto_general"]),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                    ]),
                    on_click=lambda e, pub_id=publicacion["id"]: page.go(f"/comments/{pub_id}"),
                    border_radius=10,
                    ink=True,
                ),
                col={"xs": 12, "sm": 6, "md": 4},
            )
            lista_de_tarjetas.append(card)

    return ft.View(
        "/dashboard",
        scroll=ft.ScrollMode.ADAPTIVE,
        controls=[
            ft.Column(
                [
                    ft.Text(
                        "Dashboard de Impacto de Publicaciones",
                        size=24, weight="bold", color=TEXT_DARK
                    ),
                    ft.ResponsiveRow(lista_de_tarjetas, spacing=20, run_spacing=20),
                ],
                spacing=20,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ],
    )