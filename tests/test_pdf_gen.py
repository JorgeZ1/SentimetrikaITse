from backend.report_generator import PDFReportGenerator
from backend.database import Publication, Comment
import os

def test_pdf_generation():
    print("Testing PDF Generation...")
    
    # Mock data for generate_report
    pub1 = Publication(id="1", red_social="Facebook", title_original="Título Original con ñáéíóúü", title_translated="Translated Title with ñáéíóúü")
    comment1 = Comment(author="Usuario1", text_translated="¡Qué buen post!", sentiment_label="positive")
    comment2 = Comment(author="Crítico", text_translated="Esto es pésimo.", sentiment_label="negative")
    comment3 = Comment(author="Neutral", text_translated="Interesante punto de vista.", sentiment_label="neutral")
    
    pub2 = Publication(id="2", red_social="Mastodon", title_original="Otro Post con caracteres especiales çàè", title_translated="Another Post with special chars çàè")
    comment4 = Comment(author="Amigo", text_translated="Me encantó este análisis.", sentiment_label="positive")
    comment5 = Comment(author="Detractor", text_translated="No estoy de acuerdo con nada.", sentiment_label="negative")

    publications = [pub1, pub2]
    comments_map = {
        "1": [comment1, comment2, comment3],
        "2": [comment4, comment5]
    }
    
    generator = PDFReportGenerator()
    try:
        # Test generate_report
        generator_general = PDFReportGenerator()
        file_path_general = generator_general.generate_report("RedSocialGeneral", publications, comments_map)
        print(f"✅ PDF General Generated successfully at: {file_path_general}")
        if os.path.exists(file_path_general):
            print("✅ General PDF file exists on disk.")
        else:
            print("❌ General PDF file not found on disk.")
            
        # Test generate_single_publication_report
        # Using pub1 and its comments
        generator_single = PDFReportGenerator()
        file_path_single = generator_single.generate_single_publication_report(pub1, comments_map["1"])
        print(f"✅ PDF Single Publication Generated successfully at: {file_path_single}")
        if os.path.exists(file_path_single):
            print("✅ Single Publication PDF file exists on disk.")
        else:
            print("❌ Single Publication PDF file not found on disk.")
            
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")

if __name__ == "__main__":
    test_pdf_generation()
