import os
from pathlib import Path
from sqlalchemy import create_engine, Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

# --- Cargar variables de entorno desde el archivo .env ---
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# --- 1. CONFIGURACIÓN DE CONEXIÓN --- 
# Usamos la contraseña simple que configuraste: admin123
DB_USER: str = os.getenv("POSTGRES_USER")
DB_PASS: str = os.getenv("POSTGRES_PASSWORD")
DB_HOST: str = os.getenv("POSTGRES_SERVER")
DB_PORT: str = os.getenv("POSTGRES_PORT")
# Asegúrate de que este nombre coincida con el que ves en pgAdmin (a veces es sensible a mayúsculas)
DB_NAME: str = os.getenv("POSTGRES_DB") 

# URL de conexión
DATABASE_URL: str = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"🔌 Conectando a: {DATABASE_URL} ...")

try:
    # --- AQUÍ ESTÁ EL ARREGLO (connect_args) ---
    # Forzamos a PostgreSQL a usar UTF-8 para el cliente, ignorando la configuración de Windows
    engine: Engine = create_engine(
    DATABASE_URL, 
    connect_args={"options": "-c client_encoding=utf8"}
    )
    
    SessionLocal: sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
import os
from pathlib import Path
from sqlalchemy import create_engine, Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

# --- Cargar variables de entorno desde el archivo .env ---
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# --- 1. CONFIGURACIÓN DE CONEXIÓN --- 
# Usamos la contraseña simple que configuraste: admin123
DB_USER: str = os.getenv("POSTGRES_USER")
DB_PASS: str = os.getenv("POSTGRES_PASSWORD")
DB_HOST: str = os.getenv("POSTGRES_SERVER")
DB_PORT: str = os.getenv("POSTGRES_PORT")
# Asegúrate de que este nombre coincida con el que ves en pgAdmin (a veces es sensible a mayúsculas)
DB_NAME: str = os.getenv("POSTGRES_DB") 

# URL de conexión
DATABASE_URL: str = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"🔌 Conectando a: {DATABASE_URL} ...")

try:
    # --- AQUÍ ESTÁ EL ARREGLO (connect_args) ---
    # Forzamos a PostgreSQL a usar UTF-8 para el cliente, ignorando la configuración de Windows
    engine: Engine = create_engine(
    DATABASE_URL, 
    connect_args={"options": "-c client_encoding=utf8"}
    )
    
    SessionLocal: sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# --- INICIALIZACIÓN ---

def init_db():
    """Crea las tablas en la base de datos si no existen."""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas verificadas en PostgreSQL.")
    except Exception as e:
        print(f"❌ Error al inicializar tablas: {e}")

# --- FUNCIONES DE ELIMINACIÓN ---

def delete_publication_by_id(publication_id: str) -> bool:
    """Elimina una publicación y sus comentarios asociados por ID."""
    session = SessionLocal()
    try:
        publication = session.query(Publication).filter(Publication.id == publication_id).first()
        if publication:
            session.delete(publication)
            session.commit()
            return True
        return False
    except Exception as e:
        print(f"❌ Error eliminando publicación {publication_id}: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def delete_publications_by_network(network_name: str) -> int:
    """Elimina todas las publicaciones de una red social específica. Retorna el número de eliminados."""
    session = SessionLocal()
    try:
        # SQLAlchemy maneja el borrado en cascada de comentarios si está configurado en el modelo,
        # pero aquí lo hacemos explícito borrando las publicaciones.
        deleted_count = session.query(Publication).filter(Publication.red_social == network_name).delete()
        session.commit()
        return deleted_count
    except Exception as e:
        print(f"❌ Error vaciando red social {network_name}: {e}")
        session.rollback()
        return 0
    finally:
        session.close()

if __name__ == "__main__":
    init_db()