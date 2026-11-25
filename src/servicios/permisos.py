# servicios/permisos.py
# Control de acceso y verificación de roles para las funciones del sistema.


def exigir_sesion(sesion: dict | None):
    """Verifica que la sesión sea válida y corresponda a un usuario autenticado."""
    if not isinstance(sesion, dict):
        raise PermissionError("Debe iniciar sesión para realizar esta acción.")

    if sesion.get("role") not in ("admin", "cliente"):
        raise PermissionError("Acceso no permitido.")

    user_id = sesion.get("id")
    if type(user_id) is not int or user_id <= 0:
        raise PermissionError("La sesión actual no es válida.")


def exigir_admin(sesion: dict | None):
    """Verifica que el usuario de la sesión tenga permisos de administrador."""
    exigir_sesion(sesion)
    if sesion.get("role") != "admin":
        raise PermissionError("Acción restringida únicamente para administradores.")


def exigir_propietario_o_admin(sesion: dict | None, user_id_objetivo: int):
    """Permite el acceso solo al dueño del recurso o a un administrador (mitiga IDOR)."""
    exigir_sesion(sesion)
    if sesion.get("role") == "admin":
        return
    if sesion.get("id") != user_id_objetivo:
        raise PermissionError("No tiene permisos para acceder a los registros de otro usuario.")