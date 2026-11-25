from dominio.usuario import Usuario
from persistencia.usuario_dao import UsuarioDAO
from servicios.permisos import exigir_admin
from utilidades import correo_valido


def crear_hash(clave: str) -> str:
    return Usuario.encriptar_clave(clave)


def registrar_usuario(
    full_name: str,
    email: str,
    clave: str,
    role: str = "cliente",
    sesion: dict | None = None,
) -> int:
    """
    Registra un nuevo usuario.
    - Si role == 'cliente': permite autorregistro público (sesion puede ser None).
    - Si role == 'admin': exige que la operación la ejecute un administrador autenticado.
    """
    rol_validado = Usuario.validar_rol(role)
    if rol_validado != "cliente":
        exigir_admin(sesion)

    email_normalizado = correo_valido(email)
    if UsuarioDAO.buscar_por_email(email_normalizado) is not None:
        raise ValueError("No es posible completar el registro con el correo ingresado.")

    hash_guardado = crear_hash(clave)
    usuario = Usuario(
        full_name=full_name,
        email=email_normalizado,
        password_hash=hash_guardado,
        role=rol_validado,
    )
    usuario_creado = UsuarioDAO.insertar(usuario)
    return usuario_creado.id


def autenticar(email: str, clave: str) -> dict | None:
    """Valida credenciales por correo y contraseña, devolviendo el diccionario de sesión."""
    if not isinstance(email, str) or not isinstance(clave, str):
        return None

    try:
        email_normalizado = correo_valido(email)
        Usuario.validar_clave(clave)
    except (TypeError, ValueError):
        return None

    cuenta = UsuarioDAO.buscar_por_email(email_normalizado)
    if cuenta is None:
        return None

    if not cuenta.verificar_password(clave):
        return None

    return {
        "id": cuenta.id,
        "full_name": cuenta.full_name,
        "email": cuenta.email,
        "role": cuenta.role,
    }