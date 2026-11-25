import os
from contextlib import contextmanager
import pymysql
from dotenv import load_dotenv

load_dotenv()


class ErrorConfiguracion(Exception):
    """Error de configuración de variables de entorno o motor de base de datos."""


class ErrorBaseDatos(RuntimeError):
    """Error de conexión expuesto de forma segura a la aplicación."""


ERRORES_BD = (pymysql.MySQLError, ErrorBaseDatos)
ERRORES_INTEGRIDAD = (pymysql.err.IntegrityError,)


def obtener_motor() -> str:
    motor = os.getenv("DB_ENGINE", "mysql").strip().lower()
    if motor != "mysql":
        raise ErrorConfiguracion(
            f"Motor no soportado: '{motor}'. Este sistema opera exclusivamente con MySQL."
        )
    return motor


def _obtener_puerto_mysql() -> int:
    try:
        puerto = int(os.getenv("DB_PORT", "3306"))
    except ValueError:
        raise ErrorConfiguracion("DB_PORT debe ser un número entero.") from None
    if not 1 <= puerto <= 65535:
        raise ErrorConfiguracion("DB_PORT debe estar entre 1 y 65535.")
    return puerto


def _validar_parametros_mysql() -> dict:
    obtener_motor()
    host = os.getenv("DB_HOST", "localhost").strip()
    user = os.getenv("DB_USER", "").strip()
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "").strip()

    if not user or not database:
        raise ErrorConfiguracion(
            "Faltan variables obligatorias en .env (DB_USER o DB_NAME)."
        )

    return {
        "host": host,
        "port": _obtener_puerto_mysql(),
        "user": user,
        "password": password,
        "database": database,
        "charset": "utf8mb4",
    }


def abrir_conexion():
    parametros = _validar_parametros_mysql()
    try:
        return pymysql.connect(**parametros)
    except pymysql.MySQLError as e:
        raise ErrorBaseDatos("Error al conectar con la base de datos MySQL.") from e


def marcador_sql() -> str:
    return "%s"


@contextmanager
def conexion_segura():
    """Abre una conexión MySQL y garantiza commit, rollback y cierre."""
    conexion = None
    try:
        conexion = abrir_conexion()
        yield conexion
        conexion.commit()
    except Exception:
        if conexion is not None:
            conexion.rollback()
        raise
    finally:
        if conexion is not None:
            conexion.close()