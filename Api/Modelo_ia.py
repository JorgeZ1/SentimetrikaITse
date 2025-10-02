from transformers import pipeline
import json
import pathlib

def ejecutar_analisis_local():
    """
    Función principal que carga las publicaciones con sus comentarios,
    traduce los textos de inglés a español, analiza el sentimiento de cada comentario
    y guarda los resultados manteniendo la estructura.
    """
    # --- 1. Inicialización de los modelos de IA ---
    print("Cargando modelos de IA (esto puede tardar la primera vez)...")
    try:
        print(" > Cargando modelo de análisis de sentimientos...")
        sentiment_analyzer = pipeline("sentiment-analysis")
        print(" > Cargando modelo de traducción (Inglés a Español)...")
        # Este modelo es especializado en traducción de inglés a español.
        translator = pipeline("translation_en_to_es", model="Helsinki-NLP/opus-mt-en-es")
        print("✅ Modelos cargados exitosamente.")
    except Exception as e:
        print(f"❌ Error al cargar los modelos: {e}")
        print("💡 Consejo: Asegúrate de tener 'torch' y 'sentencepiece' instalados (`pip install torch sentencepiece`).")
        return

    # --- 2. Construcción de las rutas a los archivos ---
    try:
        ruta_script_actual = pathlib.Path(__file__).parent.resolve()
        ruta_json_entrada = ruta_script_actual.parent.parent / "comentarios_estructurados.json"
        ruta_json_salida = ruta_script_actual.parent.parent / "resultados_analisis.json"
        print(f"➡️  Archivo de entrada: {ruta_json_entrada}")
        print(f"⬅️  Archivo de salida: {ruta_json_salida}")
    except Exception as e:
        print(f"❌ Error al construir las rutas de archivo: {e}")
        return

    # --- 3. Lectura del archivo de publicaciones ---
    if not ruta_json_entrada.is_file():
        print(f"❌ ERROR: Archivo de entrada no encontrado. Asegúrate de que '{ruta_json_entrada}' exista.")
        return
        
    try:
        with open(ruta_json_entrada, 'r', encoding='utf-8') as f:
            publicaciones_originales = json.load(f)
        print(f"✅ Se cargaron {len(publicaciones_originales)} publicaciones para procesar.")
    except Exception as e:
        print(f"❌ Error al leer el archivo JSON de entrada: {e}")
        return

    # --- 4. Traducción y Análisis ---
    publicaciones_procesadas = []
    print("\nIniciando traducción y análisis de sentimientos...")

    for pub in publicaciones_originales:
        publicacion_con_analisis = pub.copy()
        
        # Traducimos el título de la publicación
        try:
            titulo_original = pub.get('titulo_publicacion', '')
            if titulo_original.strip():
                publicacion_con_analisis['titulo_traducido'] = translator(titulo_original, max_length=512)[0]['translation_text']
            else:
                publicacion_con_analisis['titulo_traducido'] = ''
        except Exception as e:
            print(f"\n⚠️  Error traduciendo el título de la publicación: {e}")
            publicacion_con_analisis['titulo_traducido'] = "[Error de traducción]"

        publicacion_con_analisis["comentarios"] = []
        
        # Iteramos sobre los comentarios de esta publicación
        for comentario in pub.get("comentarios", []):
            comentario_procesado = comentario.copy()
            texto_a_procesar = comentario.get("texto", "")
            
            if not texto_a_procesar.strip():
                continue
            
            # --- Tarea de Traducción ---
            try:
                comentario_procesado['texto_traducido'] = translator(texto_a_procesar, max_length=512)[0]['translation_text']
            except Exception as e:
                print(f"\n⚠️  Error traduciendo el comentario ID {comentario.get('id_comentario')}: {e}")
                comentario_procesado['texto_traducido'] = "[Error de traducción]"

            # --- Tarea de Análisis de Sentimiento (sobre el texto original) ---
            try:
                resultado_sentimiento = sentiment_analyzer(texto_a_procesar)
                comentario_procesado["analisis_sentimiento"] = {
                    "etiqueta": resultado_sentimiento[0]['label'],
                    "confianza": resultado_sentimiento[0]['score']
                }
            except Exception as e:
                 print(f"\n⚠️  Error analizando el comentario ID {comentario.get('id_comentario')}: {e}")
                 comentario_procesado["analisis_sentimiento"] = {"etiqueta": "ERROR", "confianza": 0.0}

            publicacion_con_analisis["comentarios"].append(comentario_procesado)

        publicaciones_procesadas.append(publicacion_con_analisis)
        print(f"  > Publicación '{pub.get('titulo_publicacion', 'N/A')[:30]}...' procesada.")

    # --- 5. Guardado de los resultados ---
    try:
        with open(ruta_json_salida, 'w', encoding='utf-8') as f:
            json.dump(publicaciones_procesadas, f, ensure_ascii=False, indent=4)
        print("\n\n✅ ¡Proceso completado!")
        print(f"Los resultados (con traducciones y análisis) han sido guardados en '{ruta_json_salida}'.")
    except Exception as e:
        print(f"\n❌ Error al guardar el archivo de resultados: {e}")


# --- Punto de entrada para ejecutar el script ---
if __name__ == "__main__":
    ejecutar_analisis_local()