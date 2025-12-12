from backend.sentiment_utils import _mapear_sentimiento, analizar_sentimiento_con_umbral

# Heurístico sencillo: conteo de palabras positivas/negativas
POS_WORDS = {'good','great','excellent','love','liked','awesome','nice','happy','fantastic','amazing'}
NEG_WORDS = {'bad','terrible','awful','hate','horrible','worst','angry','sad','disappointing','dislike'}


def heuristic_analyzer(texts, batch_size=16, truncation=True):
    results = []
    for t in texts:
        txt = t.lower()
        pos = sum(1 for w in POS_WORDS if w in txt)
        neg = sum(1 for w in NEG_WORDS if w in txt)
        score = 0.5 + (pos - neg) * 0.15  # baseline 0.5
        # clamp
        if score > 0.99: score = 0.99
        if score < 0.01: score = 0.01
        if pos > neg:
            label = 'LABEL_2'  # positive
        elif neg > pos:
            label = 'LABEL_0'  # negative
        else:
            label = 'LABEL_1'  # neutral
        results.append({'label': label, 'score': score})
    return results


sample_texts = [
    "I love this library, it's awesome and very useful!",
    "This is the worst update. I hate the new layout.",
    "Meh, it's okay. Nothing special but not bad.",
    "Amazing work, fantastic results, great accuracy!",
    "I'm disappointed, the feature broke after update.",
    "I like it, but could be better.",
    "No opinion.",
    "This is bad and horrible experience.",
    "Pretty nice and helpful.",
    "I don't know what to say, it's fine."
]

print('Simulación de análisis (heurístico) con umbral=0.35:\n')
res = heuristic_analyzer(sample_texts)
for text, r in zip(sample_texts, res):
    mapped, used_score = analizar_sentimiento_con_umbral(r['label'], r['score'], umbral_confianza=0.35)
    print(f"- Texto: {text}\n  -> raw: {r}\n  -> mapeado+umbral: ({mapped}, {used_score:.3f})\n")

print('Resumen:')
labels = [analizar_sentimiento_con_umbral(r['label'], r['score'], umbral_confianza=0.35)[0] for r in res]
from collections import Counter
print(Counter(labels))
