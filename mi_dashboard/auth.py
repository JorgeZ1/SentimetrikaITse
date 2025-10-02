# auth.py
users = {
    "demo@correo.com": "12345",   # usuario de prueba
    "a@e.com": "12345"
}

def authenticate(email: str, password: str) -> bool:
    """Valida si el usuario existe y la contraseña coincide"""
    return email in users and users[email] == password

def register_user(email: str, password: str) -> bool:
    """Registra un nuevo usuario, retorna False si ya existe"""
    if email in users:
        return False
    users[email] = password
    return True
