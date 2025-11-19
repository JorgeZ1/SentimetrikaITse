import flet as ft
from mi_dashboard.utils import procesar_y_agrupar_publicaciones, get_impact_icon
# Importamos con mayúsculas, como tu versión de Flet
from flet import Icons, Colors 

# --- PALETA DE COLORES ---
BACKGROUND_COLOR = "#1f2630"
CARD_COLOR = "#2c3440"
PRIMARY_TEXT_COLOR = Colors.WHITE
SECONDARY_TEXT_COLOR = Colors.GREY_400
ACCENT_COLOR = "#3399ff"

# --- Función Helper (usa Icons) ---
def get_social_icon(red_social):
    """Devuelve un icono basado en el nombre de la red social."""
    if red_social.lower() == "mastodon":
        return Icons.HIDE_SOURCE 
    if red_social.lower() == "reddit":
        return Icons.REDDIT
    if red_social.lower() == "discord":
        return Icons.DISCORD
    return Icons.COMMENT

def create_dashboard_view(page: ft.Page):
    page.bgcolor = BACKGROUND_COLOR
    page.update()

    # --- 1. OBTENER DATOS ---
    datos_publicaciones = procesar_y_agrupar_publicaciones()
    
    # --- 2. DEFINIR LAS REDES SOCIALES ---
    redes_encontradas = sorted(list(set(pub["red_social"] for pub in datos_publicaciones)))
    
    lista_de_tabs = []

    if not datos_publicaciones:
        # (Aquí puedes poner un mensaje si no hay datos)
        lista_de_tabs.append(
            ft.Tab(
                text="Vacío",
                icon=Icons.INFO,
                content=ft.Container(
                    content=ft.Text("No se encontraron publicaciones. Ejecuta un pipeline de recolección.", color=Colors.GREY_500),
                    alignment=ft.alignment.center,
                    padding=50
                )
            )
        )
    else:
        # --- 3. CREAR UNA PESTAÑA (TAB) POR CADA RED SOCIAL ---
        for red in redes_encontradas:
            
            publicaciones_de_la_red = [
                pub for pub in datos_publicaciones if pub.get("red_social") == red
            ]
            
            lista_de_tarjetas = []
            for publicacion in publicaciones_de_la_red:
                card = ft.Card(
                    content=ft.Container(
                        padding=20,
                        content=ft.Column(
                            [
                                ft.Text(publicacion["titulo"], size=18, weight=ft.FontWeight.BOLD, color=PRIMARY_TEXT_COLOR),
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

            contenido_del_tab = ft.Container(
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
                    icon=get_social_icon(red), # Pasa el *nombre* del icono
                    content=contenido_del_tab,
                )
            )

    # --- 4. CREAR EL CONTROL DE TABS ---
    tabs_control = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=lista_de_tabs,
        expand=1,
        label_color=ACCENT_COLOR,
        unselected_label_color=SECONDARY_TEXT_COLOR,
        indicator_color=ACCENT_COLOR,
    )

    # --- 5. DEVOLVER LA VISTA PRINCIPAL ---
    return ft.View(
        "/dashboard",
        scroll=ft.ScrollMode.ADAPTIVE,
        controls=[
            ft.Column(
                [
                    # --- ¡AQUÍ ESTÁ EL CAMBIO! ---
                    ft.Row(
                        [
                            # 1. El nuevo botón de retroceso
                            ft.IconButton(
                                icon=Icons.ARROW_BACK, # Nombre del icono
                                icon_color=Colors.WHITE,
                                on_click=lambda e: page.go("/social_select")
                            ),
                            # 2. El título (un poco más corto)
                            ft.Text(
                                "Dashboard de Impacto",
                                size=24, weight=ft.FontWeight.BOLD, color=PRIMARY_TEXT_COLOR
                            ),
                        ],
                        # Alinea el botón y el texto
                        vertical_alignment=ft.CrossAxisAlignment.CENTER 
                    ),
                    # --- FIN DEL CAMBIO ---
                    
                    tabs_control, 
                ],
                spacing=25,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ],
        bgcolor=BACKGROUND_COLOR,
    )