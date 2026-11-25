import re
import bcrypt

from utilidades import correo_valido, texto_no_vacio


class Usuario:
    MIN_CLAVE = 6
    MAX_BYTES_BCRYPT = 72
    ROLES = ("admin", "cliente")
    _PATRON_HASH_BCRYPT = re.compile(
        r"^\$2[aby]\$(0[4-9]|[12][0-9]|3[01])\$[./A-Za-z0-9]{53}$"
    )

    def __init__(
        self,
        full_name: str,
        email: str,
        password_hash: str,
        role: str = "cliente",
        id: int | None = None,
        created_at=None,
    ):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at

    @classmethod
    def encriptar_clave(cls, clave: str) -> str:
        """Valida la contraseña y genera un hash seguro utilizando bcrypt."""
        clave = cls.validar_clave(clave)
        clave_bytes = clave.encode("utf-8")
        return bcrypt.hashpw(clave_bytes, bcrypt.gensalt()).decode("utf-8")

    @classmethod
    def validar_clave(cls, clave: str) -> str:
        if not isinstance(clave, str):
            raise TypeError("La contraseña debe ser texto.")
        if len(clave) < cls.MIN_CLAVE:
            raise ValueError(f"La contraseña debe tener al menos {cls.MIN_CLAVE} caracteres.")
        if len(clave.encode("utf-8")) > cls.MAX_BYTES_BCRYPT:
            raise ValueError(
                f"La contraseña no puede superar los {cls.MAX_BYTES_BCRYPT} bytes UTF-8."
            )
        return clave

    @classmethod
    def validar_rol(cls, role: str) -> str:
        if not isinstance(role, str):
            raise ValueError("El rol debe ser texto.")
        rol_limpio = role.strip().lower()
        if rol_limpio not in cls.ROLES:
            raise ValueError(f"Rol no permitido. Debe ser uno de: {', '.join(cls.ROLES)}.")
        return rol_limpio

    @classmethod
    def es_hash_bcrypt(cls, valor: str) -> bool:
        return isinstance(valor, str) and cls._PATRON_HASH_BCRYPT.fullmatch(valor) is not None

    @property
    def full_name(self) -> str:
        return self._full_name

    @full_name.setter
    def full_name(self, valor: str):
        self._full_name = texto_no_vacio(valor, "El nombre completo", maximo=120)

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, valor: str):
        self._email = correo_valido(valor)

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @password_hash.setter
    def password_hash(self, valor: str):
        self._password_hash = texto_no_vacio(valor, "El hash de contraseña", maximo=255)

    @property
    def role(self) -> str:
        return self._role

    @role.setter
    def role(self, valor: str):
        self._role = self.validar_rol(valor)

    def verificar_password(self, clave_ingresada: str) -> bool:
        """Verifica la contraseña ingresada contra el hash bcrypt almacenado."""
        if not isinstance(clave_ingresada, str):
            return False
        clave_bytes = clave_ingresada.encode("utf-8")
        if not clave_bytes or len(clave_bytes) > self.MAX_BYTES_BCRYPT:
            return False
        if not self.es_hash_bcrypt(self.password_hash):
            return False
        return bcrypt.checkpw(clave_bytes, self.password_hash.encode("utf-8"))

    def mostrar_datos(self) -> str:
        return f"[{self.id}] {self.full_name} <{self.email}> (Rol: {self.role})"

    def __str__(self) -> str:
        return self.mostrar_datos()