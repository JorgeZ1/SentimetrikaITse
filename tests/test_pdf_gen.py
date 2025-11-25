from Api.report_generator import PDFReportGenerator
from Api.database import Publication, Comment
import os

def test_pdf_generation():
    print("Testing PDF Generation...")
    
    # Mock data
    pub1 = Publication(id="1", red_social="TestNet", title_original="Original Title", title_translated="Translated Title")
    comment1 = Comment(author="user1", text_translated="Good post", sentiment_label="positive")
    comment2 = Comment(author="user2", text_translated="Bad post", sentiment_label="negative")
    
    publications = [pub1]
    comments_map = {"1": [comment1, comment2]}
    
    generator = PDFReportGenerator()
    try:
        file_path = generator.generate_report("TestNet", publications, comments_map)
        print(f"✅ PDF Generated successfully at: {file_path}")
        
        if os.path.exists(file_path):
            print("✅ File exists on disk.")
        else:
            print("❌ File not found on disk.")
            
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")

if __name__ == "__main__":
    test_pdf_generation()
