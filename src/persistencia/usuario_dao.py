from dominio.usuario import Usuario
from persistencia.conexion import conexion_segura, marcador_sql

_COLUMNAS = "id, full_name, email, password_hash, role, created_at"


class UsuarioDAO:
    @staticmethod
    def _mapear_fila(fila) -> Usuario:
        return Usuario(
            id=fila[0],
            full_name=fila[1],
            email=fila[2],
            password_hash=fila[3],
            role=fila[4],
            created_at=fila[5],
        )

    @classmethod
    def insertar(cls, usuario: Usuario) -> Usuario:
        if not Usuario.es_hash_bcrypt(usuario.password_hash):
            raise ValueError("Solo se pueden guardar contraseñas con hash bcrypt.")
        p = marcador_sql()
        sql = f"""
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES ({p}, {p}, {p}, {p})
        """
        parametros = (
            usuario.full_name,
            usuario.email,
            usuario.password_hash,
            usuario.role,
        )
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, parametros)
                usuario.id = cursor.lastrowid
                return usuario
            finally:
                cursor.close()

    @classmethod
    def buscar_por_email(cls, email: str) -> Usuario | None:
        p = marcador_sql()
        sql = f"SELECT {_COLUMNAS} FROM users WHERE email = {p}"
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, (email.strip().lower(),))
                fila = cursor.fetchone()
                return cls._mapear_fila(fila) if fila else None
            finally:
                cursor.close()

    @classmethod
    def buscar_por_id(cls, usuario_id: int) -> Usuario | None:
        p = marcador_sql()
        sql = f"SELECT {_COLUMNAS} FROM users WHERE id = {p}"
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, (usuario_id,))
                fila = cursor.fetchone()
                return cls._mapear_fila(fila) if fila else None
            finally:
                cursor.close()

    @classmethod
    def listar(cls) -> list[Usuario]:
        sql = f"SELECT {_COLUMNAS} FROM users ORDER BY id ASC"
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql)
                return [cls._mapear_fila(fila) for fila in cursor.fetchall()]
            finally:
                cursor.close()

    @classmethod
    def actualizar_password_hash(cls, usuario_id: int, hash_actual: str, hash_nuevo: str) -> bool:
        if not Usuario.es_hash_bcrypt(hash_nuevo):
            raise ValueError("La nueva contraseña debe tener un hash bcrypt válido.")
        p = marcador_sql()
        sql = f"""
            UPDATE users
            SET password_hash = {p}
            WHERE id = {p} AND password_hash = {p}
        """
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, (hash_nuevo, usuario_id, hash_actual))
                return cursor.rowcount > 0
            finally:
                cursor.close()