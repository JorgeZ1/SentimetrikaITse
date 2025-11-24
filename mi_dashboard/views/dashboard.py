import flet as ft
from mi_dashboard.utils import procesar_y_agrupar_publicaciones, get_impact_icon
from flet import Icons, Colors
import threading
from typing import List, Dict, Any

# --- PALETA DE COLORES ---
BACKGROUND_COLOR: str = "#1f2630"
CARD_COLOR: str = "#2c3440"
PRIMARY_TEXT_COLOR: str = Colors.WHITE
SECONDARY_TEXT_COLOR: str = Colors.GREY_400
ACCENT_COLOR: str = "#3399ff"

def get_social_icon(red_social: str) -> str:
    """Devuelve un icono basado en el nombre de la red social."""
    if red_social.lower() == "mastodon":
        return Icons.HIDE_SOURCE
    if red_social.lower() == "reddit":
        return Icons.REDDIT
    if red_social.lower() == "discord":
        return Icons.DISCORD
    return Icons.COMMENT

def create_dashboard_view(page: ft.Page) -> ft.View:
    page.bgcolor = BACKGROUND_COLOR

    # Contenedor principal que se actualizará
    main_content: ft.Column = ft.Column(
        [ft.ProgressRing(width=32, height=32)],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
    )

    def load_data_in_background() -> None:
        """Función que carga los datos y actualiza la UI."""
        datos_publicaciones: List[Dict[str, Any]] = procesar_y_agrupar_publicaciones()
        
        # Limpiar el indicador de carga
        main_content.controls.clear()

        if not datos_publicaciones:
            main_content.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No se encontraron publicaciones. Ejecuta un pipeline de recolección.", 
                        style=ft.TextStyle(color=Colors.GREY_500)
                    ),
                    alignment=ft.alignment.center,
                    padding=50
                )
            )
        else:
            redes_encontradas: List[str] = sorted(list(set(pub["red_social"] for pub in datos_publicaciones)))
            lista_de_tabs: List[ft.Tab] = []

            for red in redes_encontradas:
                publicaciones_de_la_red: List[Dict[str, Any]] = [
                    pub for pub in datos_publicaciones if pub.get("red_social") == red
                ]
                
                lista_de_tarjetas: List[ft.Card] = []
                for publicacion in publicaciones_de_la_red:
                    card = ft.Card(
                        content=ft.Container(
                            padding=20,
                            content=ft.Column(
                                [
                                    ft.Text(
                                        publicacion["titulo"], 
                                        style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD, color=PRIMARY_TEXT_COLOR)
                                    ),
                                    ft.Divider(height=10, color=ACCENT_COLOR, thickness=1),
                                    ft.Row(
                                        [
                                            ft.Text(
                                                "Impacto General:", 
                                                style=ft.TextStyle(size=16, color=SECONDARY_TEXT_COLOR)
                                            ),
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

                contenido_del_tab: ft.Container = ft.Container(
                    content=ft.ResponsiveRow(
                        lista_de_tarjetas, 
                        spacing=20, 
                        run_spacing=20
                    ),
                    padding=ft.padding.only(top=20)
                )
                
                lista_de_tabs.append(
                    ft.Tab(
                        text=red,
                        icon=get_social_icon(red),
                        content=contenido_del_tab,
                    )
                )
            
            tabs_control: ft.Tabs = ft.Tabs(
                selected_index=0,
                animation_duration=300,
                tabs=lista_de_tabs,
                expand=1,
                label_color=ACCENT_COLOR,
                unselected_label_color=SECONDARY_TEXT_COLOR,
                indicator_color=ACCENT_COLOR,
            )
            main_content.controls.append(tabs_control)
        
        page.update()

    # Iniciar la carga de datos en un hilo separado
    threading.Thread(target=load_data_in_background, daemon=True).start()

    return ft.View(
        "/dashboard",
        scroll=ft.ScrollMode.ADAPTIVE,
        controls=[
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=Icons.ARROW_BACK,
                                icon_color=Colors.WHITE,
                                on_click=lambda e: page.go("/social_select")
                            ),
                            ft.Text(
                                "Dashboard de Impacto",
                                style=ft.TextStyle(size=24, weight=ft.FontWeight.BOLD, color=PRIMARY_TEXT_COLOR)
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    main_content,
                ],
                spacing=25,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ],
        bgcolor=BACKGROUND_COLOR,
    )
