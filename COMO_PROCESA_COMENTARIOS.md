# Cómo Sentimetrika Procesa Comentarios

## Resumen en 30 segundos

1. **Descarga** comentarios de redes sociales (Reddit, Facebook, Mastodon)
2. **Traduce** comentarios al inglés (si están en otro idioma)
3. **Analiza** el sentimiento (positivo, negativo, neutral)
4. **Guarda** todo en una base de datos
5. **Muestra** resultados en el dashboard con estadísticas

---

## Flujo Paso a Paso (Visual)

```
┌─────────────────────────┐
│  USUARIO HACE CLIC EN   │
│  "EJECUTAR SCRAPER"     │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│  PASO 1: DESCARGAR COMENTARIOS              │
│  ─────────────────────────────────────────  │
│  • Se conecta a Reddit/Facebook/Mastodon    │
│  • Obtiene posts y sus comentarios          │
│  • Ejemplo: 5 posts × 3 comentarios = 15    │
│  • Se verifica si ya existen (sin duplicar) │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│  PASO 2: TRADUCIR (si es necesario)         │
│  ─────────────────────────────────────────  │
│  Comentario en ESPAÑOL:                     │
│  "Este producto es excelente, muy bueno"    │
│           ↓↓↓ TRADUCTOR ↓↓↓                 │
│  Comentario en INGLÉS:                      │
│  "This product is excellent, very good"     │
│                                             │
│  (Si ya está en inglés, se deja igual)      │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│  PASO 3: ANALIZAR SENTIMIENTO               │
│  ─────────────────────────────────────────  │
│  Texto EN INGLÉS:                           │
│  "This product is excellent, very good"     │
│           ↓↓↓ MODELO IA ↓↓↓                 │
│  RESULTADO:                                 │
│  • Etiqueta: POSITIVE                       │
│  • Confianza: 95%                           │
│                                             │
│  El modelo nota: "excellent" + "good"       │
│  = palabras positivas → POSITIVE             │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│  PASO 4: GUARDAR EN BASE DE DATOS           │
│  ─────────────────────────────────────────  │
│  Se guarda:                                 │
│  • Texto original (español)                 │
│  • Texto traducido (inglés)                 │
│  • Sentimiento (positive/negative/neutral)  │
│  • Confianza (0.95 = 95%)                   │
│  • Autor y fecha                            │
│                                             │
│  ✅ Guardado en base de datos local         │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│  PASO 5: MOSTRAR EN DASHBOARD               │
│  ─────────────────────────────────────────  │
│  Dashboard muestra:                         │
│  ✓ Total comentarios: 15                    │
│  ✓ Positivos: 8                             │
│  ✓ Negativos: 3                             │
│  ✓ Neutrales: 4                             │
│                                             │
│  Usuario puede ver cada comentario          │
│  con su sentimiento y textos original/trad. │
└─────────────────────────────────────────────┘
```

---

## Ejemplo Real Paso a Paso

### **Escenario: Usuario analiza subreddit r/mexico con 2 comentarios**

#### **COMENTARIO 1**

**Descarga:**
```
Autor: juan_perez
Texto: "Me encanta este producto, funciona perfecto"
```

**Traducción:**
```
Texto inglés: "I love this product, it works perfectly"
```

**Análisis de Sentimiento:**
```
Palabras detectadas: "love" (positivo) + "perfectly" (positivo)
Resultado: POSITIVE (98% confianza)
```

**Guardado:**
```
├─ Texto original: "Me encanta este producto, funciona perfecto"
├─ Texto traducido: "I love this product, it works perfectly"
├─ Sentimiento: positive
└─ Confianza: 0.98
```

---

#### **COMENTARIO 2**

**Descarga:**
```
Autor: maria_lopez
Texto: "Terrible, no funciona bien, pésimo"
```

**Traducción:**
```
Texto inglés: "Terrible, it doesn't work well, awful"
```

**Análisis de Sentimiento:**
```
Palabras detectadas: "Terrible" (negativo) + "awful" (negativo)
Resultado: NEGATIVE (96% confianza)
```

**Guardado:**
```
├─ Texto original: "Terrible, no funciona bien, pésimo"
├─ Texto traducido: "Terrible, it doesn't work well, awful"
├─ Sentimiento: negative
└─ Confianza: 0.96
```

---

### **Dashboard Resultado**

```
┌─────────────────────────────────┐
│ Dashboard r/mexico              │
├─────────────────────────────────┤
│ Total comentarios: 2             │
│ ✓ Positivos: 1                   │
│ ✗ Negativos: 1                   │
│ • Neutrales: 0                   │
├─────────────────────────────────┤
│ COMENTARIO 1 (POSITIVE)         │
│ Autor: juan_perez               │
│ Texto: Me encanta este...       │
│ Sentimiento: ✓ Positivo (98%)   │
│                                 │
│ COMENTARIO 2 (NEGATIVE)         │
│ Autor: maria_lopez              │
│ Texto: Terrible, no funciona... │
│ Sentimiento: ✗ Negativo (96%)   │
└─────────────────────────────────┘
```

---

## ¿Qué sucede en cada Paso? (Más Detallado)

### **PASO 1: DESCARGA (Scraping)**

**¿Qué hace?**
- Se conecta a una red social usando credenciales (API keys)
- Obtiene los últimos posts/comentarios
- Verifica que no sean duplicados (compara autor + texto)

**¿Cómo lo hace Sentimetrika?**
```python
# Pseudocódigo simplificado
Para cada red social (Reddit, Facebook, Mastodon):
    1. Conectar con credenciales
    2. Obtener N posts (limit: 1-30 según usuario)
    3. Para cada post, obtener sus comentarios
    4. Guardar temporalmente en memoria
    5. Verificar si ya existen en BD
    6. Guardar solo nuevos
```

**Ejemplo con Reddit:**
```
Subreddit: r/mexico
Posts solicitados: 5
Comentarios por post: 3
Total a procesar: 5 × 3 = 15 comentarios
```

---

### **PASO 2: TRADUCCIÓN**

**¿Por qué es necesario?**
- El modelo de sentimiento está entrenado en inglés
- Si el comentario está en español, da resultados malos
- Solución: traducir todo a inglés primero

**¿Cómo traduce?**
- Usa modelo `Helsinki-NLP/opus-mt-es-en`
- Procesa 16 comentarios a la vez (batch processing)
- Mantiene el original y guarda la traducción

**Ejemplo:**
```
ORIGINAL (Español):  "No me gustó nada, muy malo"
TRADUCIDO (Inglés):  "I didn't like it at all, very bad"
```

---

### **PASO 3: ANÁLISIS DE SENTIMIENTO**

**¿Qué hace el modelo?**
- Lee el texto en inglés
- Identifica palabras positivas/negativas
- Asigna una etiqueta (positive/negative/neutral)
- Da un porcentaje de confianza

**¿Cómo funciona internamente?**
```
Texto: "I love this product, it works perfectly"

Detecta:
  • "love" → +0.25 (muy positivo)
  • "perfectly" → +0.20 (muy positivo)
  • "product" → 0.00 (neutro)

Suma: +0.45 = POSITIVE (95% confianza)
```

**Los tres tipos de sentimiento:**
- **POSITIVO** 😊: Palabras como "love", "excellent", "great"
- **NEGATIVO** 😞: Palabras como "hate", "terrible", "awful"
- **NEUTRAL** 😐: Sin opinión clara o palabras mixtas

---

### **PASO 4: GUARDADO EN BASE DE DATOS**

**¿Qué se guarda?**
```
COMENTARIO {
  id: 1234
  publication_id: "reddit_post_abc123"
  author: "juan_perez"
  text_original: "Me encanta este producto"
  text_translated: "I love this product"
  sentiment_label: "positive"
  sentiment_score: "0.95"
  fecha: "2025-12-11 14:30:00"
}
```

**¿Dónde se guarda?**
- **Desarrollo:** SQLite (archivo local `sentimetrika.db`)
- **Producción:** PostgreSQL (servidor remoto)

---

### **PASO 5: VISUALIZACIÓN**

**El dashboard muestra:**
1. **Estadísticas totales:** Cuántos positivos, negativos, neutrales
2. **Lista de comentarios:** Cada uno con su texto y sentimiento
3. **Opción de exportar:** PDF con el análisis completo

**Usuario puede:**
- ✓ Ver texto original y traducción
- ✓ Filtrar por sentimiento
- ✓ Generar reportes PDF
- ✓ Ejecutar nuevos análisis

---

## ¿Qué pasa si hay MUCHOS COMENTARIOS NEUTRALES?

**Problema:** Si la mayoría salen como "neutral", el análisis es poco útil

**Causas posibles:**
1. Comentarios muy cortos sin palabras clave ("ok", "gracias")
2. Texto con sentimientos mixtos ("me gusta pero es caro")
3. Texto en idioma no detectado correctamente
4. El modelo tiene baja confianza

**Solución aplicada en Sentimetrika:**
```
Si confianza < 35%:
  → Marcar como NEUTRAL (sin forzar una etiqueta)
Si confianza ≥ 35%:
  → Usar la etiqueta detectada (positive/negative)
```

Esto reduce falsos positivos pero puede dejar algunos textos sin clasificar.

---

## Flujo Completo de Datos

```
USUARIO
  │
  ├─→ Dashboard Reddit
  │     └─→ Configuración
  │         ├─ Subreddit: mexico
  │         ├─ Posts: 5
  │         └─ Comentarios: 3
  │            │
  │            ▼
  │        [SCRAPER REDDIT]
  │            │
  │            ├─ Conecta a Reddit
  │            ├─ Obtiene 5 posts
  │            ├─ Obtiene 15 comentarios
  │            └─ Deduplica
  │               │
  │               ▼
  │           [TRADUCTOR]
  │            │
  │            ├─ Detecta si es español
  │            ├─ Traduce a inglés
  │            └─ Guarda ambas versiones
  │               │
  │               ▼
  │           [SENTIMIENTO]
  │            │
  │            ├─ Lee texto en inglés
  │            ├─ Identifica palabras clave
  │            └─ Asigna etiqueta + confianza
  │               │
  │               ▼
  │           [BASE DE DATOS]
  │            │
  │            └─ Guarda en SQLite/PostgreSQL
  │               │
  │               ▼
  │           [DASHBOARD]
  │            │
  │            ├─ Muestra gráficos
  │            ├─ Lista comentarios
  │            └─ Permite exportar PDF
  │
  └─→ Usuario ve resultados
```

---

## Timepo y Performance

**¿Cuánto tarda el análisis?**

Para **15 comentarios** (5 posts × 3 comentarios):

| Paso | Tiempo | Qué sucede |
|------|--------|-----------|
| **Descarga** | 2-3 seg | Conecta a Reddit y obtiene datos |
| **Traducción** | 3-5 seg | Traduce 15 comentarios en batch |
| **Sentimiento** | 2-3 seg | Analiza 15 comentarios |
| **Guardado BD** | <1 seg | Inserta en base de datos |
| **TOTAL** | ~8-12 seg | Desde click hasta resultados |

**Nota:** La primera ejecución es más lenta porque carga modelos de IA (~2GB). Las siguientes son más rápidas.

---

## Casos de Uso Reales

### **Caso 1: Análisis de Reputación de Marca**

```
Empresa quiere saber qué opinan de ellos en Reddit

1. Usuario pone subreddit: "mexico"
2. Descarga 30 posts + comentarios
3. Traduce (muchos en español)
4. Analiza sentimientos
5. Dashboard muestra:
   ✓ 70% positivos: "Excelente servicio"
   ✓ 20% negativos: "Pésima atención"
   • 10% neutrales: "Es caro pero bueno"

RESULTADO: Marca tiene buena reputación pero hay quejas de precio
```

### **Caso 2: Feedback de Producto**

```
Startup lanza app y quiere feedback

1. Analiza comentarios en r/peru (en español)
2. Traduce automáticamente
3. Identifica problemas:
   ✗ "App muy lenta" (negativo)
   ✗ "No funciona en Android" (negativo)
   ✓ "UI muy bonita" (positivo)

RESULTADO: Priorizar fixes de velocidad y Android
```

### **Caso 3: Monitoreo de Eventos**

```
Durante evento en vivo (transmisión/juego)

1. Analiza comentarios cada 5 minutos
2. Sentimientos en tiempo real:
   
   Momento 1 (acción emocionante): 85% positivos
   Momento 2 (error técnico): 60% negativos
   Momento 3 (arreglo): 70% positivos

RESULTADO: Identificar momentos críticos en vivo
```

---

## Limitaciones Actuales

1. **Idiomas:** Solo traduce español ↔ inglés (extensible a más)
2. **Contexto:** No entiende sarcasmo ("¡Qué excelente!" dicho irónicamente)
3. **Emojis:** Los ignora (podrían dar pistas del sentimiento)
4. **Conjugaciones:** Algunas formas verbales raras podrían confundir
5. **Neutrales:** Muchos comentarios quedan como neutral (se está mejorando)

---

## Mejoras Futuras Posibles

- [ ] Detectar idioma automáticamente (no solo español)
- [ ] Análisis de emojis
- [ ] Detectar sarcasmo
- [ ] Análisis de tópicos (¿de qué habla cada comentario?)
- [ ] Visualización de tendencias en tiempo real
- [ ] Exportar a Google Sheets/Excel automáticamente

---

**Última actualización:** 11 de Diciembre, 2025
**Audiencia:** Personas sin experiencia técnica que quieren entender el flujo
