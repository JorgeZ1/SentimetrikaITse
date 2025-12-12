# Cómo RoBERTa Discrimina Sentimientos en Comentarios

## ¿Qué es RoBERTa?

**RoBERTa** = "**Ro**bustly **Optim**ized **BERT** **Pre**-training **A**pproach"

Es un modelo de **Inteligencia Artificial entrenado previamente** que puede entender el significado de las palabras en contexto y clasificar sentimientos. Lo usa Sentimetrika bajo el nombre `cardiffnlp/twitter-roberta-base-sentiment-latest`.

---

## Analogía Simple: El Experto en Emociones

Imagina que tienes un **experto en análisis de emociones humanas** que:

1. **Leyó millones de comentarios** en Twitter (antes de entrenar)
2. **Aprendió patrones** de qué palabras/frases significan qué
3. **Puede leer un comentario nuevo** y decir: "Esto es positivo porque..."

RoBERTa funciona así, pero es una red neuronal (máquina matemática) en lugar de una persona.

---

## El Proceso Interno Paso a Paso

### **Paso 1: TOKENIZACIÓN (Convertir texto en números)**

El modelo no entiende palabras como tú. Convierte cada comentario en **tokens** (pedazos pequeños):

```
COMENTARIO ORIGINAL:
"I love this product, it's amazing!"

TOKENIZACIÓN (en palabras/partes):
[101]  [1045]  [2572]  [2023]  [3231]  [1010]  [2009]  [1005]  [1055]  [6429]  [999]  [102]
START  I       love    this   product ,      it     's     amaz   -ing   !      END

NÚMEROS (embeddings):
Cada número representa una palabra en el "diccionario" del modelo (30,522 palabras)
```

---

### **Paso 2: EMBEDDING (Dar significado a los números)**

Cada número se convierte en un **vector** (lista de números) que representa su significado:

```
Palabra: "love"
Significado matemático (vector de 768 números):
[0.234, -0.891, 0.123, ..., 0.456]  ← estos números codifican la idea de "amor/positivo"

Palabra: "hate"
Significado matemático:
[-0.567, 0.234, -0.891, ..., -0.234]  ← estos números codifican la idea de "odio/negativo"

Palabra: "the" (artículo neutro)
Significado matemático:
[0.001, 0.005, -0.003, ..., 0.002]  ← casi ceros porque es una palabra "sin sentimiento"
```

**Idea clave:** Palabras con sentimiento similar tienen **vectores parecidos**. El modelo "sabe" que "love" y "adore" están cercanos.

---

### **Paso 3: TRANSFORMER (El cerebro del modelo)**

Este es lo más sofisticado. El Transformer **entiende el contexto** y **relaciona palabras entre sí**:

```
COMENTARIO: "The service was terrible but the food is amazing"

Sin contexto, cada palabra:
- "terrible" → sentimiento negativo
- "amazing" → sentimiento positivo
- Resultado: NEUTRAL (se cancelan)

CON CONTEXTO (lo que hace RoBERTa):
- "terrible" se RELACIONA con "service"
  → Critica el servicio (malo, pero...)
  
- "amazing" se RELACIONA con "food"
  → Alaba la comida (bueno)

- Conecta: "but" = contraste importante
  → No es neutral, hay dos sentimientos, pero el "but" sugiere
     que "amazing" es más relevante

RESULTADO: MIXED SENTIMENT (o POSITIVE si predomina "amazing")
```

**¿Cómo lo hace?**

Usa **capas de atención** (attention layers) que calculan:

```
Para cada palabra, ¿cuáles otras palabras son importantes para entenderla?

En "The service was terrible but the food is amazing":

"terrible" se enfoca en:
  - "service" (100%) ← es sobre QUÉ es terrible
  - "The" (5%)
  - "but" (20%) ← el "pero" sugiere salvedad

"amazing" se enfoca en:
  - "food" (100%) ← es sobre QUÉ es amazing
  - "but" (25%) ← el "pero" lo hace más relevante
  - "The" (5%)

El modelo aprende a pesar estas importancias automáticamente
```

---

### **Paso 4: CLASIFICACIÓN FINAL (Predicción)**

Después de procesar todo con Transformer, el modelo pasa el resultado final a una **capa clasificadora** que devuelve 3 números (probabilidades):

```
ENTRADA FINAL DEL MODELO:
Resumen procesado del comentario
  ↓
TRES NODOS DE SALIDA:
├─ LABEL_0 (Negativo): 0.05 (5%)
├─ LABEL_1 (Neutral):  0.10 (10%)
└─ LABEL_2 (Positivo): 0.85 (85%)

DECISIÓN: POSITIVO (con 85% de confianza)
```

---

## Ejemplo Completo: "I love this product, it's amazing!"

```
┌─────────────────────────────────────────────────────────────┐
│ ENTRADA: "I love this product, it's amazing!"              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ TOKENIZACIÓN                                                 │
│ [I] [love] [this] [product] [,] [it] ['s] [amazing] [!]    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ EMBEDDING (cada palabra → vector)                           │
│ [0.2, -0.5, 0.8] [0.9, 0.1, -0.3] ... [0.7, 0.6, 0.4]    │
│  I                love                   amazing             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ TRANSFORMER - CAPAS DE ATENCIÓN                             │
│                                                              │
│ Capa 1: "love" ve que está conectado a "I" y "this"        │
│ Capa 2: "amazing" ve que está conectado a "product" e "I"  │
│ Capa 3: El modelo NOTA dos palabras positivas juntas        │
│ Capa 4: Patrón reconocido: SENTIMIENTO MUY POSITIVO        │
│ ... (12 capas en total, cada vez más sofisticado) ...      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ CLASIFICADOR FINAL                                           │
│                                                              │
│ Negativo (LABEL_0):  2% ▓░░░░░░░░░                         │
│ Neutral  (LABEL_1):  3% ▓░░░░░░░░░                         │
│ Positivo (LABEL_2): 95% ████████████████████████           │
│                                                              │
│ RESULTADO: POSITIVE (confianza: 0.95)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## ¿Cómo Aprendió RoBERTa a Hacer Esto?

### **Fase 1: Pre-entrenamiento General (Millones de comentarios)**

RoBERTa fue entrenado con **55 millones de tweets** para aprender:

- Qué significa cada palabra
- Cómo se relacionan palabras entre sí
- Patrones de lenguaje natural

```
Ejemplos de aprendizaje:

Vio 1,000,000 de veces: "love" + "amazing" + "great" juntas
→ Aprendió: Estas palabras suelen indicar POSITIVO

Vio 1,000,000 de veces: "hate" + "terrible" + "awful" juntas
→ Aprendió: Estas palabras suelen indicar NEGATIVO

Vio 1,000,000 de veces: "it's" + "ok" + "fine" juntas
→ Aprendió: Estos patrones suelen ser NEUTRAL
```

### **Fase 2: Fine-tuning para Sentimientos**

Se reentrenó específicamente con comentarios etiquetados manualmente:

```
Ejemplo de datos de entrenamiento:

"Excellent service, highly recommend!" → POSITIVO
"Rude staff, never coming back" → NEGATIVO
"It's okay, nothing special" → NEUTRAL
"Best product ever!" → POSITIVO
"Waste of money" → NEGATIVO
... (miles de ejemplos más)
```

RoBERTa aprendió a **pesar las características importantes** para el sentimiento.

---

## ¿Qué Hace Especial a RoBERTa?

### **1. Entiende Contexto (No Solo Palabras)**

```
TEXTO: "The new interface is not good"

MÉTODO SIMPLE (solo cuenta palabras):
  "good" → POSITIVO ❌ RESULTADO INCORRECTO

ROBERTA (entiende contexto):
  "not good" → Ve que "not" NIEGA "good"
  → NEGATIVO ✓ RESULTADO CORRECTO
```

### **2. Bidireccional (Lee izquierda Y derecha)**

```
TEXTO: "The bank is closing soon"

UNIDIRECCIONAL (como algunos modelos viejos):
  "bank" podría ser:
  - Institución financiera (lee hacia la derecha)
  - Orilla del río (lee hacia la derecha)
  Ambiguo ❌

BIDIRECCIONAL (RoBERTa):
  Lee: "The bank is CLOSING soon"
  → Entiende que "bank" = institución financiera
  → "closing" = cierre de sucursal
  Claro ✓
```

### **3. 12 Capas de Procesamiento (Muy Profundo)**

```
Capa 1: Detecta palabras individuales y su polaridad
        "love" → [positivo], "hate" → [negativo]

Capa 2: Detecta relaciones simples
        "love" + "this" → el "love" describe "this"

Capa 3: Detecta intensidad
        "really love" → más intenso que "like"

...

Capa 12: Síntesis final de todo el sentimiento del texto
         Integra toda la información para decisión final
```

Cada capa **añade sofisticación** al análisis.

---

## Ejemplos de Discriminación en Acción

### **Ejemplo 1: Sarcasmo (el punto débil)**

```
TEXTO: "Oh great, another waiting list!"

RoBERTa interno:
- Ve "great" → POSITIVO (70% inicial)
- Ve contexto: "waiting list" → NEGATIVO
- Ve puntuación exclamativa → podrría ser sarcasmo
- Conflicto: ¿Es positivo o irónico?

RESULTADO: Probablemente NEUTRAL o NEGATIVO
(Pero RoBERTa a veces falla en sarcasmo porque es sutil)
```

### **Ejemplo 2: Palabras Raras o Jerga**

```
TEXTO: "This product slaps! Fire energy fr fr"

RoBERTa interno:
- "slaps" → Fue entrenado con Twitter, conoce jerga moderna
- "Fire" → En contexto con "energy", es POSITIVO (no literal)
- "fr fr" = "for real for real" → énfasis positivo

RESULTADO: POSITIVO (85%)
```

### **Ejemplo 3: Opinión Negativa Educada**

```
TEXTO: "While the interface is intuitive, 
        the performance leaves much to be desired"

RoBERTa interno:
- "intuitive" → POSITIVO
- "But" implícito en "While"
- "leaves much to be desired" → NEGATIVO educado
- Patrón: "A es bueno PERO B es malo"

RESULTADO: NEGATIVO (porque enfatiza el problema)
```

---

## La Arquitectura Visual de RoBERTa

```
ENTRADA: Comentario en texto
    │
    ▼
┌──────────────────────┐
│ TOKENIZER            │  Convierte texto → números
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│ EMBEDDING LAYER                          │  Números → vectores con significado
│ (Cada palabra tiene 768 dimensiones)     │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│ TRANSFORMER ENCODER (12 capas)           │  Procesa relaciones contextuales
│                                          │  - Capa 1 a 4: Análisis básico
│  ┌──────────────────────────────────┐   │  - Capa 5 a 8: Patrones medios
│  │ Multi-Head Self-Attention        │   │  - Capa 9 a 12: Síntesis final
│  │ Feed-Forward Networks            │   │
│  │ Layer Normalization              │   │
│  └──────────────────────────────────┘   │
│          (se repite 12 veces)           │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ CLASSIFICATION HEAD              │  3 nodos de salida
│ [CLS] token → Dense Layer        │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ SOFTMAX (Convierte a probabilidades)
│                                  │
│ LABEL_0 (Neg): 0.05 (5%)        │
│ LABEL_1 (Neu): 0.10 (10%)       │
│ LABEL_2 (Pos): 0.85 (85%)       │
└──────────┬───────────────────────┘
           │
           ▼
SALIDA: POSITIVO (confianza 0.85)
```

---

## ¿Por Qué RoBERTa es Mejor que Métodos Simples?

### **Método 1: Diccionario de Palabras (Antiguo)**

```
Diccionario:
{
  "love": +1,
  "hate": -1,
  "good": +1,
  "bad": -1,
  ...
}

Algoritmo: Suma todos los puntos

PROBLEMA: "The food is not good"
Suma: good(+1) = POSITIVO ❌
INCORRECTO: Es negativo, pero el método vio "good"
```

### **Método 2: RoBERTa (Moderno)**

```
Red neuronal con 125 millones de parámetros aprendidos

VENTAJA: Entiende que "not good" = negativo ✓
VENTAJA: Entiende contexto y sarcasmo (a veces)
VENTAJA: Maneja idioma natural complejo
LIMITACIÓN: Requiere más poder computacional
```

---

## Parámetros Importantes de RoBERTa

| Parámetro | Valor | Significado |
|-----------|-------|-------------|
| **Capas (Layers)** | 12 | Profundidad del procesamiento |
| **Cabezas de Atención** | 12 | Diferentes "perspectivas" de análisis |
| **Dimensión Oculta** | 768 | Tamaño de los vectores internos |
| **Vocabulario** | 50,265 | Palabras que conoce |
| **Parámetros Totales** | 125M | Números que aprendió |
| **Idioma** | Inglés | No es multilingüe nativo |
| **Entrenamiento** | Twitter | Optimizado para redes sociales |

---

## Limitaciones Conocidas de RoBERTa

### **1. Sarcasmo e Ironía**

```
"Oh sure, because that makes TOTAL sense!" 
→ RoBERTa lo ve como positivo (por "TOTAL")
→ Pero es sarcasmo negativo ❌
```

### **2. Contexto Muy Largo**

```
RoBERTa recibe máximo 512 tokens (palabras)
Si el comentario es muy largo, lo trunca
Puede perder información importante
```

### **3. Idiomas Mixtos**

```
"Excelente! Great! Amazing!"
Español + inglés → puede confundirse
(Aunque lo maneja mejor que muchos)
```

### **4. Jerga Muy Nueva**

```
"No cap, slaps different fr"
Si la jerga no estaba en el entrenamiento (2019-2021)
Puede fallar en nuevas palabras
```

### **5. Contexto Histórico**

```
"Literally dying!" (de risa)
RoBERTa no sabe que "dying" aquí es positivo
Necesita contexto cultural
```

---

## ¿Cómo Sentimetrika Usa RoBERTa?

```
EN SENTIMETRIKA:

1. Modelo descargado de HuggingFace
   cardiffnlp/twitter-roberta-base-sentiment-latest
   
2. Ejecutado en CPU (sin GPU requerida)

3. Aplicado en LOTE (batch) para eficiencia
   - 16 comentarios a la vez
   - ~3-5 segundos para 100 comentarios

4. UMBRAL DE CONFIANZA aplicado
   - Si confianza < 35% → marcar como NEUTRAL
   - Si confianza ≥ 35% → usar la etiqueta
   - Reduce falsos positivos
```

---

## Comparación con Otros Modelos

| Modelo | Ventajas | Desventajas | Ideal para |
|--------|----------|-------------|-----------|
| **RoBERTa** (Sentimetrika) | Multilingüe-ready, rápido, Twitter-trained | Sarcasmo, contexto muy largo | Redes sociales, tweets |
| **BERT** | Estable, muchos fine-tunes disponibles | Más lento | Académico |
| **DistilBERT** | Ultra rápido, menor memory | Menos preciso | Dispositivos móviles |
| **GPT-3** | Muy sofisticado, entiende contexto | Caro, lento, overkill | Análisis complejo |
| **Diccionario simple** | Muy rápido, interpretable | Casi inútil en práctica | Prototipo educativo |

---

## Resumen: Por Qué RoBERTa Discrimina Mejor

```
┌─────────────────────────────────────────────────────────────┐
│ RoBERTa = 125 millones de parámetros aprendidos            │
│                                                             │
│ Aprende:                                                    │
│ ✓ Significado profundo de palabras                         │
│ ✓ Relaciones entre palabras (atención)                     │
│ ✓ Patrones de sentimientos complejos                       │
│ ✓ Contexto (qué rodea cada palabra)                        │
│ ✓ Intensidad (adverbios que amplifican)                    │
│ ✓ Negaciones ("not good" ≠ "good")                         │
│                                                             │
│ NO aprende:                                                │
│ ✗ Sarcasmo (muy sutil)                                     │
│ ✗ Nuevas palabras del futuro                               │
│ ✗ Contexto histórico/cultural                              │
│ ✗ Cambio de significado radical (idiomas)                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Para Ir Más Profundo

**Artículos académicos:**
- "RoBERTa: A Robustly Optimized BERT Pretraining Approach" (Facebook Research, 2019)
- "Attention is All You Need" (Google, 2017) - Base de Transformers

**Código en Sentimetrika:**
```python
# En main.py:
sentiment_model = pipeline(
    "text-classification", 
    model="cardiffnlp/twitter-roberta-base-sentiment-latest"
)

# En reddit_scraper.py:
results = sentiment_analyzer(texts_for_sentiment, batch_size=16, truncation=True)
# Para cada texto, devuelve:
# {'label': 'LABEL_2', 'score': 0.95}
```

---

**Última actualización:** 11 de Diciembre, 2025
**Audiencia:** Personas interesadas en entender IA/NLP
