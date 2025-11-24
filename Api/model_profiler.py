import time
from transformers import pipeline

def profile_models():
    """Profiles the translation and sentiment analysis models."""
    
    print("Cargando modelos...")
    try:
        translator = pipeline("translation", model="Helsinki-NLP/opus-mt-es-en")
        sentiment_analyzer = pipeline("text-classification", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
        print("✅ Modelos cargados.")
    except Exception as e:
        print(f"❌ Error cargando modelos: {e}")
        return

    sample_texts = [
        "Este es un día maravilloso y estoy muy feliz.",
        "Odio el tráfico de la mañana, siempre llego tarde.",
        "El servicio al cliente fue simplemente normal, ni bueno ni malo.",
        "¡Acabo de recibir una oferta de trabajo! Estoy muy emocionado.",
        "La película fue aburrida y predecible. No la recomiendo.",
        "El clima de hoy es perfecto para un paseo por el parque.",
        "Mi pedido llegó dañado, estoy muy decepcionado.",
        "El nuevo álbum de mi artista favorito es increíble.",
        "No tengo una opinión fuerte sobre este asunto.",
        "¡Gané el primer premio en el concurso de fotografía!",
        "La comida en ese restaurante es consistentemente deliciosa.",
        "Perdí mi billetera y ahora tengo que cancelar todas mis tarjetas.",
        "El libro que estoy leyendo es muy interesante y no puedo dejarlo.",
        "La conexión a internet ha estado muy lenta todo el día.",
        "Hoy es un día como cualquier otro, nada especial.",
    ] * 10 # 150 sentences

    print(f"\nProfiling con {len(sample_texts)} frases...")

    # --- Profile Translation ---
    start_time = time.time()
    translation_result = translator(sample_texts, batch_size=16)
    translated_texts = [t['translation_text'] for t in translation_result]
    end_time = time.time()
    translation_time = end_time - start_time
    print(f"\n--- Traducción ---")
    print(f"Tiempo total: {translation_time:.4f} segundos")
    print(f"Frases por segundo: {len(sample_texts) / translation_time:.2f}")

    # --- Profile Sentiment Analysis ---
    start_time = time.time()
    sentiments = sentiment_analyzer(translated_texts, batch_size=16, truncation=True)
    end_time = time.time()
    sentiment_time = end_time - start_time
    print(f"\n--- Análisis de Sentimiento ---")
    print(f"Tiempo total: {sentiment_time:.4f} segundos")
    print(f"Frases por segundo: {len(sample_texts) / sentiment_time:.2f}")

if __name__ == "__main__":
    profile_models()
