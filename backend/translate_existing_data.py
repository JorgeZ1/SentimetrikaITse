"""
Script simple para traducir datos existentes
"""
import os
import sys

# Agregar el directorio raíz al path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def main():
    print("🌐 Iniciando traducción...")
    
    # Importar después de agregar al path
    from backend.database import SessionLocal, Publication, Comment
    
    try:
        from transformers import pipeline
        print("✅ Transformers cargado")
    except ImportError:
        print("❌ Error: No se puede importar transformers")
        print("Ejecuta: pip install transformers")
        return
    
    print("⏳ Cargando modelo de traducción...")
    try:
        translator = pipeline("translation_en_to_es", model="Helsinki-NLP/opus-mt-en-es")
        print("✅ Modelo cargado\n")
    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")
        return
    
    session = SessionLocal()
    
    try:
        # Traducir comentarios
        print("� Buscando comentarios para traducir...")
        comments = session.query(Comment).all()
        
        to_translate = []
        for c in comments:
            if not c.text_translated or c.text_translated == c.text_original:
                if c.text_original:
                    to_translate.append(c)
        
        print(f"Encontrados: {len(to_translate)} comentarios\n")
        
        if len(to_translate) == 0:
            print("✅ No hay comentarios para traducir")
        else:
            count = 0
            batch_size = 8
            
            for i in range(0, len(to_translate), batch_size):
                batch = to_translate[i:i+batch_size]
                texts = [c.text_original[:512] for c in batch]
                
                try:
                    results = translator(texts, max_length=512, batch_size=len(texts), truncation=True)
                    
                    for comment, result in zip(batch, results):
                        comment.text_translated = result['translation_text']
                        count += 1
                    
                    session.commit()
                    print(f"✓ {count}/{len(to_translate)}")
                    
                except Exception as e:
                    print(f"✗ Error: {e}")
                    session.rollback()
            
            print(f"\n🎉 {count} comentarios traducidos!")
        
        # Traducir publicaciones
        print("\n� Buscando publicaciones para traducir...")
        publications = session.query(Publication).all()
        
        pub_to_translate = []
        for p in publications:
            if not p.title_translated or p.title_translated == p.title_original:
                if p.title_original:
                    pub_to_translate.append(p)
        
        print(f"Encontradas: {len(pub_to_translate)} publicaciones")
        
        if len(pub_to_translate) == 0:
            print("✅ No hay publicaciones para traducir")
        else:
            pub_count = 0
            for pub in pub_to_translate:
                try:
                    result = translator(pub.title_original[:512], max_length=512)
                    pub.title_translated = result[0]['translation_text']
                    pub_count += 1
                except:
                    pass
            
            session.commit()
            print(f"🎉 {pub_count} publicaciones traducidas!\n")
        
        print("=" * 50)
        print("✅ TRADUCCIÓN COMPLETADA")
        print("💡 Reinicia la app para ver los cambios")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()
