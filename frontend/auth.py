# auth.py
import hashlib
from backend.database import SessionLocal, User

def hash_password(password: str) -> str:
    """Hashea una contraseña usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(email: str, password: str) -> bool:
    """Valida si el usuario existe y la contraseña coincide"""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()
        if user and user.hashed_password == hash_password(password):
            return True
        return False
    except Exception as e:
        print(f"Error en autenticación: {e}")
        return False
    finally:
        session.close()

def register_user(email: str, password: str) -> bool:
    """Registra un nuevo usuario, retorna False si ya existe"""
    session = SessionLocal()
    try:
        # Verificar si el usuario ya existe
        existing_user = session.query(User).filter(User.email == email).first()
        if existing_user:
            return False
        
        # Crear nuevo usuario
        new_user = User(
            email=email,
            hashed_password=hash_password(password)
        )
        session.add(new_user)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error registrando usuario: {e}")
        return False
    finally:
        session.close()
