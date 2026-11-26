from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from utilidades import texto_no_vacio, texto_opcional


class Destino:
    def __init__(
        self,
        nombre: str,
        pais: str = "Chile",
        costo_base: Decimal | float | int | str = Decimal("0.00"),
        descripcion: str = "",
        actividades: str = "",
        activo: bool = True,
        id: int | None = None,
    ):
        self.id = id
        self.nombre = nombre
        self.pais = pais
        self.descripcion = descripcion
        self.actividades = actividades
        self.costo_base = costo_base
        self.activo = bool(activo)

    @staticmethod
    def validar_costo(valor) -> Decimal:
        if isinstance(valor, bool):
            raise ValueError("El costo base debe ser un monto numérico.")
        try:
            texto = str(valor).strip().replace(",", ".")
            monto = Decimal(texto)
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError("El costo base debe ser un monto numérico válido.") from None

        if not monto.is_finite() or monto < Decimal("0"):
            raise ValueError("El costo base no puede ser negativo.")
        return monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def nombre(self) -> str:
        return self._nombre

    @nombre.setter
    def nombre(self, valor: str):
        self._nombre = texto_no_vacio(valor, "El nombre del destino", maximo=120)

    @property
    def pais(self) -> str:
        return self._pais

    @pais.setter
    def pais(self, valor: str):
        self._pais = texto_no_vacio(valor, "El país", maximo=100)

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor: str):
        self._descripcion = texto_opcional(valor, "La descripción", maximo=500)

    @property
    def actividades(self) -> str:
        return self._actividades

    @actividades.setter
    def actividades(self, valor: str):
        self._actividades = texto_opcional(valor, "Las actividades", maximo=500)

    @property
    def costo_base(self) -> Decimal:
        return self._costo_base

    @costo_base.setter
    def costo_base(self, valor):
        self._costo_base = self.validar_costo(valor)

    def validar(self):
        """Revalida todas las invariantes de negocio del destino."""
        self.nombre = self._nombre
        self.pais = self._pais
        self.costo_base = self._costo_base

    def retirar(self):
        """Aplica retiro lógico para conservar el historial de paquetes y viajes."""
        self.activo = False

    def reactivar(self):
        """Habilita nuevamente un destino retirado para futuros paquetes."""
        self.activo = True

    def mostrar_datos(self) -> str:
        estado = "Activo" if self.activo else "Retirado"
        return (
            f"[{self.id}] {self.nombre} ({self.pais}) | "
            f"Costo base: ${self.costo_base:,.2f} | Estado: {estado}"
        )

    def __str__(self) -> str:
        return self.mostrar_datos()