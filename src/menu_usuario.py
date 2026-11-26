import logging
from getpass import getpass

from dominio.usuario import Usuario
from entradas import pedir_dato
from persistencia.conexion import ERRORES_BD, ErrorConfiguracion
from servicios.autenticacion import autenticar, registrar_usuario
from utilidades import correo_valido, texto_no_vacio

_registro = logging.getLogger("viajes_aventura")


def solicitar_registro_cliente():
    try:
        full_name = pedir_dato(
            "Nombre completo: ",
            lambda v: texto_no_vacio(v, "El nombre completo", 120),
        )
        email = pedir_dato("Correo electrónico: ", correo_valido)
        clave = pedir_dato(
            "Contraseña (mín. 6 caracteres): ", Usuario.validar_clave, getpass
        )

        if clave != getpass("Repita la contraseña: "):
            print("Las contraseñas no coinciden.")
            return None

        usuario_id = registrar_usuario(full_name, email, clave, role="cliente")
        print(
            f"Cuenta de cliente creada correctamente (ID: {usuario_id}). "
            "Ahora puede iniciar sesión."
        )
        return usuario_id
    except ErrorConfiguracion as error:
        _registro.exception("Configuración incorrecta durante el registro")
        print(f"Error de configuración: {error}")
    except ERRORES_BD:
        _registro.exception("Error de BD durante el registro")
        print("No fue posible completar el registro por un problema con la base de datos.")
    except (TypeError, ValueError) as error:
        print(f"Error: {error}")
    return None


def solicitar_login():
    email = input("Correo electrónico: ").strip()
    clave = getpass("Contraseña: ")
    try:
        usuario = autenticar(email, clave)
    except ErrorConfiguracion as error:
        _registro.exception("Configuración incorrecta durante el inicio de sesión")
        print(f"Error de configuración: {error}")
        return None
    except ERRORES_BD:
        _registro.exception("Error de BD durante el inicio de sesión")
        print("No fue posible iniciar sesión por un problema con la base de datos.")
        return None

    if usuario is None:
        print("Correo o contraseña incorrectos.")
    return usuario