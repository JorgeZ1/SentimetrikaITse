import flet as ft
# Hacemos referencia a la carpeta 'mi_dashboard' para encontrar 'utils'
from utils import procesar_y_agrupar_publicaciones, get_impact_icon

# Usamos ft.Colors con C mayúscula como indicaste
TEXT_DARK = ft.Colors.BLACK

def create_comments_view(page: ft.Page, pub_id: str):
    
    todas_las_publicaciones = procesar_y_agrupar_publicaciones()
    # Buscamos la publicación específica que coincide con el ID de la URL
    publicacion_actual = next((p for p in todas_las_publicaciones if p['id'] == pub_id), None)

    if not publicacion_actual:
        return ft.View(
            f"/comments/{pub_id}",
            [
                ft.Text("Publicación no encontrada.", size=20, text_align=ft.TextAlign.CENTER),
                ft.ElevatedButton("Volver al Dashboard", on_click=lambda _: page.go("/dashboard"))
            ],
            vertical_alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    # Creamos las tarjetas para cada comentario de esta publicación
    lista_tarjetas_comentarios = []
    for comentario in publicacion_actual.get("comentarios", []):
        sentimiento_info = comentario.get("analisis_sentimiento", {})
        etiqueta = sentimiento_info.get("etiqueta", "UNKNOWN").lower()
        
        card = ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLUE_GREY_400),
                        ft.Text(f"{comentario.get('autor', 'Anónimo')}", weight="bold"),
                    ]),
                    ft.Text(f"\"{comentario.get('texto_original', '')}\""),
                    ft.Divider(color=ft.Colors.GREY_300),
                    ft.Row(
                        [
                            ft.Text("Impacto:", weight="bold"),
                            ft.Row([get_impact_icon(etiqueta), ft.Text(etiqueta.capitalize())]),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                ])
            )
        )
        lista_tarjetas_comentarios.append(card)

    return ft.View(
        f"/comments/{pub_id}",
        scroll=ft.ScrollMode.ADAPTIVE,
        controls=[
            ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    on_click=lambda _: page.go("/dashboard"),
                    tooltip="Volver al Dashboard"
                ),
                ft.Text(publicacion_actual["titulo"], size=22, weight="bold", expand=True),
            ]),
            ft.Text(f"Mostrando {len(lista_tarjetas_comentarios)} comentarios:", size=16, color="gray"),
            ft.Column(lista_tarjetas_comentarios, spacing=15)
        ]
    )