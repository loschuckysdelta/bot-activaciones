"""Comprobación segura de usuarios: evita ModuleNotFoundError: bot.auth."""
import requests

API_USER = "https://activaciones.vercel.app/api/user"


def esta_registrado(usuario_id):
    """Devuelve True solo si la API confirma un usuario válido."""
    try:
        respuesta = requests.get(
            API_USER, params={"id": str(usuario_id)}, timeout=8
        )
        if respuesta.status_code == 404:
            return False
        respuesta.raise_for_status()
        datos = respuesta.json()
        return isinstance(datos, dict) and isinstance(datos.get("user"), dict) and bool(datos["user"])
    except (requests.RequestException, ValueError, TypeError):
        return False
