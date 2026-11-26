from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from utilidades import entero_positivo, texto_no_vacio, texto_opcional


class ParadaItinerario:
    def __init__(
        self,
        destino_id: int,
        orden: int,
        notas: str = "",
        id: int | None = None,
        paquete_id: int | None = None,
        destino_nombre: str = "",
        destino_pais: str = "",
        destino_costo_base: Decimal = Decimal("0.00"),
        destino_activo: bool = True,
    ):
        self.id = id
        self.paquete_id = paquete_id
        self.destino_id = entero_positivo(destino_id, "El ID del destino")
        self.orden = entero_positivo(orden, "El orden de visita")
        self.notas = notas
        self.destino_nombre = destino_nombre
        self.destino_pais = destino_pais
        self.destino_costo_base = Decimal(str(destino_costo_base))
        self.destino_activo = bool(destino_activo)

    @property
    def notas(self) -> str:
        return self._notas

    @notas.setter
    def notas(self, valor: str):
        self._notas = texto_opcional(valor, "Las notas de la parada", maximo=255)

    def cambiar_orden(self, nuevo_orden: int):
        self.orden = entero_positivo(nuevo_orden, "El nuevo orden de visita")

    def __str__(self) -> str:
        etiqueta_destino = (
            f"{self.destino_nombre} ({self.destino_pais})"
            if self.destino_nombre
            else f"Destino ID {self.destino_id}"
        )
        estado = "" if self.destino_activo else " [DESTINO RETIRADO]"
        detalle_notas = f" — Nota: {self.notas}" if self.notas else ""
        return (
            f"  Paso {self.orden}: {etiqueta_destino} "
            f"(Costo base: ${self.destino_costo_base:,.2f}){estado}{detalle_notas}"
        )


class SalidaPaquete:
    ESTADOS_VALIDOS = ("abierta", "cerrada", "cancelada")

    def __init__(
        self,
        paquete_id: int,
        fecha_inicio: date | str,
        fecha_fin: date | str,
        precio_por_persona: Decimal | float | int | str,
        cupos_totales: int,
        cupos_disponibles: int | None = None,
        estado: str = "abierta",
        id: int | None = None,
        paquete_titulo: str = "",
    ):
        self.id = id
        self.paquete_id = entero_positivo(paquete_id, "El ID del paquete")
        self.paquete_titulo = paquete_titulo
        self.fecha_inicio = self.validar_fecha(fecha_inicio, "La fecha de inicio")
        self.fecha_fin = self.validar_fecha(fecha_fin, "La fecha de término")
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de término no puede ser anterior a la fecha de inicio.")

        self.precio_por_persona = self.validar_precio(precio_por_persona)
        self.cupos_totales = entero_positivo(cupos_totales, "Los cupos totales")

        if cupos_disponibles is None:
            self.cupos_disponibles = self.cupos_totales
        else:
            if isinstance(cupos_disponibles, bool) or not isinstance(cupos_disponibles, int):
                raise ValueError("Los cupos disponibles deben ser un número entero.")
            if cupos_disponibles < 0 or cupos_disponibles > self.cupos_totales:
                raise ValueError("Los cupos disponibles deben estar entre 0 y los cupos totales.")
            self.cupos_disponibles = cupos_disponibles

        self.estado = self.validar_estado(estado)

    @staticmethod
    def validar_fecha(valor: date | str, campo: str = "La fecha") -> date:
        if isinstance(valor, date):
            return valor
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f"{campo} es obligatoria (formato YYYY-MM-DD).")
        try:
            return date.fromisoformat(valor.strip())
        except ValueError:
            raise ValueError(f"{campo} debe tener formato válido YYYY-MM-DD.") from None

    @staticmethod
    def validar_precio(valor) -> Decimal:
        if isinstance(valor, bool):
            raise ValueError("El precio por persona debe ser un monto numérico.")
        try:
            monto = Decimal(str(valor).strip().replace(",", "."))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError("El precio por persona debe ser un monto numérico válido.") from None
        if not monto.is_finite() or monto < Decimal("0"):
            raise ValueError("El precio por persona no puede ser negativo.")
        return monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def validar_estado(cls, estado: str) -> str:
        if not isinstance(estado, str):
            raise ValueError("El estado de la salida no es válido.")
        limpio = estado.strip().lower()
        if limpio not in cls.ESTADOS_VALIDOS:
            raise ValueError(f"Estado inválido. Opciones permitidas: {', '.join(cls.ESTADOS_VALIDOS)}.")
        return limpio

    def hay_cupos(self, cantidad: int) -> bool:
        cantidad_ok = entero_positivo(cantidad, "La cantidad de pasajeros")
        return self.estado == "abierta" and self.cupos_disponibles >= cantidad_ok

    def descontar_cupos(self, cantidad: int):
        cantidad_ok = entero_positivo(cantidad, "La cantidad de pasajeros")
        if self.estado != "abierta":
            raise ValueError("La salida no se encuentra abierta para reservas.")
        if self.cupos_disponibles < cantidad_ok:
            raise ValueError(
                f"Cupos insuficientes: solicitó {cantidad_ok} y solo quedan {self.cupos_disponibles}."
            )
        self.cupos_disponibles -= cantidad_ok
        if self.cupos_disponibles == 0:
            self.estado = "cerrada"

    def liberar_cupos(self, cantidad: int):
        cantidad_ok = entero_positivo(cantidad, "La cantidad de pasajeros")
        if self.cupos_disponibles + cantidad_ok > self.cupos_totales:
            raise ValueError("No se pueden liberar más cupos que el total configurado.")
        self.cupos_disponibles += cantidad_ok
        if self.estado == "cerrada" and self.cupos_disponibles > 0:
            self.estado = "abierta"

    def __str__(self) -> str:
        prefijo = f"{self.paquete_titulo} | " if self.paquete_titulo else ""
        return (
            f"[Salida #{self.id}] {prefijo}{self.fecha_inicio} al {self.fecha_fin} | "
            f"Precio/persona: ${self.precio_por_persona:,.2f} | "
            f"Cupos: {self.cupos_disponibles}/{self.cupos_totales} | Estado: {self.estado}"
        )


class PaqueteTuristico:
    def __init__(
        self,
        titulo: str,
        descripcion: str = "",
        activo: bool = True,
        id: int | None = None,
        itinerario: list[ParadaItinerario] | None = None,
        salidas: list[SalidaPaquete] | None = None,
    ):
        self.id = id
        self.titulo = titulo
        self.descripcion = descripcion
        self.activo = bool(activo)
        self.itinerario: list[ParadaItinerario] = list(itinerario) if itinerario else []
        self.salidas: list[SalidaPaquete] = list(salidas) if salidas else []

    @property
    def titulo(self) -> str:
        return self._titulo

    @titulo.setter
    def titulo(self, valor: str):
        self._titulo = texto_no_vacio(valor, "El título del paquete", maximo=150)

    @property
    def descripcion(self) -> str:
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor: str):
        self._descripcion = texto_opcional(valor, "La descripción del paquete", maximo=1000)

    def agregar_parada(self, parada: ParadaItinerario):
        if any(p.orden == parada.orden for p in self.itinerario):
            raise ValueError(f"Ya existe una parada asignada al orden {parada.orden}.")
        self.itinerario.append(parada)
        self.itinerario.sort(key=lambda p: p.orden)

    def obtener_itinerario(self) -> list[ParadaItinerario]:
        return sorted(self.itinerario, key=lambda p: p.orden)

    def calcular_costo_base_total(self) -> Decimal:
        total = sum((p.destino_costo_base for p in self.itinerario), Decimal("0.00"))
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def validar_itinerario(self):
        """Exige al menos 2 destinos con orden correlativo (1, 2, ..., N)."""
        paradas = self.obtener_itinerario()
        if len(paradas) < 2:
            raise ValueError("Un paquete turístico debe incluir al menos 2 destinos en su itinerario.")

        ordenes = [p.orden for p in paradas]
        esperados = list(range(1, len(paradas) + 1))
        if ordenes != esperados:
            raise ValueError(
                f"El orden de visita debe ser correlativo {esperados}, pero se recibió {ordenes}."
            )

    def __str__(self) -> str:
        estado = "Activo" if self.activo else "Inactivo"
        costo_ref = self.calcular_costo_base_total()
        return (
            f"[Paquete #{self.id}] {self.titulo} | Destinos: {len(self.itinerario)} | "
            f"Costo base ref.: ${costo_ref:,.2f} | Salidas: {len(self.salidas)} | Estado: {estado}"
        )