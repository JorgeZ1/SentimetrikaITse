import flet as ft
from sqlalchemy import func
from collections import Counter
from flet import Icons, Colors
from Api.database import SessionLocal, Publication, Comment

def get_impact_icon(impact: str):
    """
    Devuelve un icono de Flet basado en la cadena de impacto.
    Adaptado para la versión de Flet del usuario.
    """
    icons = {
        "positive": ft.Icon(name=Icons.SENTIMENT_SATISFIED, color=Colors.GREEN),
        "negative": ft.Icon(name=Icons.SENTIMENT_DISSATISFIED, color=Colors.RED),
        "neutral": ft.Icon(name=Icons.SENTIMENT_NEUTRAL, color=Colors.GREY),
    }
    return icons.get(impact.lower(), ft.Icon(name=Icons.HELP))

def procesar_y_agrupar_publicaciones():
    """
    Obtiene TODAS las publicaciones desde PostgreSQL y calcula el impacto
    de forma eficiente usando una única consulta.
    """
    session = SessionLocal()
    lista_procesada = []

    try:
        # Subconsulta para contar los sentimientos por publicación
        subquery = (
            session.query(
                Comment.publication_id,
                Comment.sentiment_label,
                func.count(Comment.id).label("sentiment_count"),
                func.row_number()
                .over(
                    partition_by=Comment.publication_id,
                    order_by=func.count(Comment.id).desc(),
                )
                .label("rn"),
            )
            .group_by(Comment.publication_id, Comment.sentiment_label)
            .subquery()
        )

        # Consulta principal que une Publicaciones con la subconsulta de impacto
        query = (
            session.query(
                Publication.id,
                Publication.title_translated,
                Publication.title_original,
                Publication.red_social,
                subquery.c.sentiment_label.label("impacto_general"),
            )
            .outerjoin(subquery, Publication.id == subquery.c.publication_id)
            .filter(subquery.c.rn == 1) # Solo el sentimiento más común
        )
        
        results = query.all()

        for pub in results:
            lista_procesada.append({
                "id": pub.id,
                "titulo": pub.title_translated or pub.title_original or "Título Desconocido",
                "impacto_general": pub.impacto_general or "neutral",
                "red_social": pub.red_social or "Desconocida",
            })

    except Exception as e:
        print(f"❌ ERROR al procesar publicaciones: {e}")
    finally:
        session.close()

    return lista_procesada