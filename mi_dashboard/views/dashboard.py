import flet as ft
from utils import procesar_y_agrupar_publicaciones, get_impact_icon

# --- PALETA DE COLORES ---
BACKGROUND_COLOR = "#1f2630"
CARD_COLOR = "#2c3440"
PRIMARY_TEXT_COLOR = ft.Colors.WHITE  # CORREGIDO
SECONDARY_TEXT_COLOR = ft.Colors.GREY_400 # CORREGIDO
ACCENT_COLOR = "#3399ff"

def create_dashboard_view(page: ft.Page):
    page.bgcolor = BACKGROUND_COLOR
    page.update()

    datos_publicaciones = procesar_y_agrupar_publicaciones()
    
    lista_de_tarjetas = []
    if not datos_publicaciones:
        # ... (código del mensaje de ayuda sin cambios)
        pass
    else:
        for publicacion in datos_publicaciones:
            card = ft.Card(
                content=ft.Container(
                    padding=20,
                    content=ft.Column(
                        [
                            ft.Text(publicacion["titulo"], size=18, weight="bold", color=PRIMARY_TEXT_COLOR),
                            ft.Divider(height=10, color=ACCENT_COLOR, thickness=1),
                            ft.Row(
                                [
                                    ft.Text("Impacto General:", size=16, color=SECONDARY_TEXT_COLOR),
                                    get_impact_icon(publicacion["impacto_general"]),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                        ],
                        spacing=15
                    ),
                    on_click=lambda e, pub_id=publicacion["id"]: page.go(f"/comments/{pub_id}"),
                    border_radius=10,
                    ink=True,
                ),
                color=CARD_COLOR,
                elevation=4,
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
                        size=24, weight="bold", color=PRIMARY_TEXT_COLOR
                    ),
                    ft.ResponsiveRow(lista_de_tarjetas, spacing=20, run_spacing=20),
                ],
                spacing=25,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ],
        bgcolor=BACKGROUND_COLOR,
    )