def _mapear_sentimiento(label_original: str) -> str:
    """Normaliza las etiquetas del modelo de forma más concisa.
    
    El modelo cardiffnlp/twitter-roberta-base-sentiment devuelve:
    - LABEL_0: Negative
    - LABEL_1: Neutral  
    - LABEL_2: Positive
    """
    label_upper = str(label_original).upper().strip()
    
    # Mapeo para diferentes variantes de etiquetas
    mapping = {
        # Variantes positivas
        'POSITIVE': 'positive', 
        'LABEL_2': 'positive', 
        'POS': 'positive',
        '2': 'positive',
        
        # Variantes negativas
        'NEGATIVE': 'negative', 
        'LABEL_0': 'negative', 
        'NEG': 'negative',
        '0': 'negative',
        
        # Variantes neutrales
        'NEUTRAL': 'neutral',
        'LABEL_1': 'neutral',
        '1': 'neutral'
    }
    
    return mapping.get(label_upper, 'neutral')


def analizar_sentimiento_con_umbral(label: str, score: float, umbral_confianza: float = 0.5) -> tuple:
    """
    Analiza sentimiento con umbral de confianza.
    
    Si el score está por debajo del umbral, marca como neutral.
    
    Args:
        label: Etiqueta del modelo (LABEL_0, LABEL_1, LABEL_2, etc)
        score: Score de confianza (0.0 - 1.0)
        umbral_confianza: Umbral mínimo (default 0.5 = 50%)
    
    Returns:
        (sentiment_label, sentiment_score)
    """
    sentiment_mapped = _mapear_sentimiento(label)
    
    # Si el score es muy bajo, marcar como neutral (inseguro)
    if score < umbral_confianza:
        return ('neutral', score)
    
    return (sentiment_mapped, score)
