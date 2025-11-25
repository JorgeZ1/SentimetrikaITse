def _mapear_sentimiento(label_original: str) -> str:
    """Normaliza las etiquetas del modelo de forma más concisa."""
    mapping = {
        'POSITIVE': 'positive', 'LABEL_2': 'positive', 'POS': 'positive',
        'NEGATIVE': 'negative', 'LABEL_0': 'negative', 'NEG': 'negative'
    }
    return mapping.get(label_original.upper(), 'neutral')