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

# --- 1. CONFIGURACION DE CONEXION --- 
DB_TYPE: str = os.getenv("DB_TYPE", "sqlite")

if DB_TYPE == "postgresql":
    DB_USER: str = os.getenv("POSTGRES_USER")
    DB_PASS: str = os.getenv("POSTGRES_PASSWORD")
    DB_HOST: str = os.getenv("POSTGRES_SERVER")
    DB_PORT: str = os.getenv("POSTGRES_PORT")
    DB_NAME: str = os.getenv("POSTGRES_DB")
    DATABASE_URL: str = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    print(f"[CONEXION] Conectando a: {DATABASE_URL} ...")
    try:
        engine: Engine = create_engine(
            DATABASE_URL, 
            connect_args={"options": "-c client_encoding=utf8"}
        )
    except Exception as e:
        print(f"[ERROR] Error creando el motor de base de datos: {e}")
        raise e
else:  # SQLite por defecto
    db_path = Path(__file__).resolve().parent.parent / "sentimetrika.db"
    DATABASE_URL: str = f"sqlite:///{db_path}"
    print(f"[CONEXION] Conectando a: {DATABASE_URL} ...")
    try:
        engine: Engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False}
        )
    except Exception as e:
        print(f"[ERROR] Error creando el motor de base de datos: {e}")
        raise e

SessionLocal: sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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

# --- INICIALIZACION ---

def init_db():
    """Crea las tablas en la base de datos si no existen."""
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Tablas verificadas en base de datos.")
    except Exception as e:
        print(f"[ERROR] Error al inicializar tablas: {e}")

# --- FUNCIONES DE ELIMINACION ---

def delete_publication_by_id(publication_id: str) -> bool:
    """Elimina una publicacion y sus comentarios asociados por ID."""
    session = SessionLocal()
    try:
        publication = session.query(Publication).filter(Publication.id == publication_id).first()
        if publication:
            session.delete(publication)
            session.commit()
            return True
        return False
    except Exception as e:
        print(f"[ERROR] Error eliminando publicacion {publication_id}: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def delete_publications_by_network(network_name: str) -> int:
    """Elimina todas las publicaciones de una red social especifica. Retorna el numero de eliminados."""
    session = SessionLocal()
    try:
        # Usar eliminación a través del ORM para respetar cascade="all, delete-orphan"
        pubs = session.query(Publication).filter(Publication.red_social == network_name).all()
        deleted_count = len(pubs)
        for p in pubs:
            session.delete(p)
        session.commit()
        return deleted_count
    except Exception as e:
        print(f"[ERROR] Error vaciando red social {network_name}: {e}")
        session.rollback()
        return 0
    finally:
        session.close()

if __name__ == "__main__":
    init_db()