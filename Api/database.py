import os
from sqlalchemy import create_engine, Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv
# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- 1. CONFIGURACIÓN DE CONEXIÓN --- 
# Usamos la contraseña simple que configuraste: admin123
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_SERVER")
DB_PORT = os.getenv("POSTGRES_PORT")
# Asegúrate de que este nombre coincida con el que ves en pgAdmin (a veces es sensible a mayúsculas)
DB_NAME = os.getenv("POSTGRES_DB") 

# URL de conexión
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"🔌 Conectando a: {DATABASE_URL} ...")

try:
    # --- AQUÍ ESTÁ EL ARREGLO (connect_args) ---
    # Forzamos a PostgreSQL a usar UTF-8 para el cliente, ignorando la configuración de Windows
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"options": "-c client_encoding=utf8"}
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    print(f"❌ Error fatal creando el motor de base de datos: {e}")
    raise e

# --- MODELOS ---

class Publication(Base):
    __tablename__ = "publications"

    id = Column(String, primary_key=True, index=True)
    red_social = Column(String, index=True)
    title_original = Column(Text)
    title_translated = Column(Text)
    
    comments = relationship("Comment", back_populates="publication", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    publication_id = Column(String, ForeignKey("publications.id"))
    author = Column(String)
    text_original = Column(Text)
    text_translated = Column(Text)
    sentiment_label = Column(String)
    sentiment_score = Column(String, nullable=True)

    publication = relationship("Publication", back_populates="comments")

# --- INICIALIZACIÓN ---

def init_db():
    """Crea las tablas en la base de datos si no existen."""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas verificadas en PostgreSQL.")
    except Exception as e:
        print(f"❌ Error al inicializar tablas: {e}")

if __name__ == "__main__":
    init_db()