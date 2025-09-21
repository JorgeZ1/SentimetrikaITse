# utils.py
import flet as ft
from theme import ACCENT_MAGENTA

def get_impact_icon(impact: str):
    """Devuelve un ícono según el tipo de impacto"""
    icons = {
        "positivo": ft.Icon(ft.Icons.SENTIMENT_SATISFIED, color="green"),
        "negativo": ft.Icon(ft.Icons.SENTIMENT_DISSATISFIED, color="red"),
        "neutral": ft.Icon(ft.Icons.SENTIMENT_NEUTRAL, color="gray"),
    }
    return icons.get(impact, ft.Icon(ft.Icons.HELP, color=ACCENT_MAGENTA))
