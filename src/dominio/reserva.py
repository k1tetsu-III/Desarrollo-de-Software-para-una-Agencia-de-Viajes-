from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from utilidades import entero_positivo, texto_no_vacio, texto_opcional


class AvanceEtapa:
    ESTADOS_VALIDOS = ("pendiente", "en_curso", "completada")

    def __init__(
        self,
        pasajero_id: int | None,
        parada_itinerario_id: int,
        estado_etapa: str = "pendiente",
        fecha_actualizacion: datetime | str | None = None,
        observacion: str = "",
        id: int | None = None,
        orden_visita: int = 0,
        destino_nombre: str = "",
        destino_pais: str = "",
    ):
        self.id = id
        self.pasajero_id = pasajero_id
        self.parada_itinerario_id = entero_positivo(
            parada_itinerario_id, "El ID de la parada del itinerario"
        )
        self.estado_etapa = self.validar_estado(estado_etapa)
        self.fecha_actualizacion = fecha_actualizacion or datetime.now()
        self.observacion = observacion
        self.orden_visita = orden_visita
        self.destino_nombre = destino_nombre
        self.destino_pais = destino_pais

    @classmethod
    def validar_estado(cls, estado: str) -> str:
        if not isinstance(estado, str):
            raise ValueError("El estado de la etapa no es válido.")
        limpio = estado.strip().lower()
        if limpio not in cls.ESTADOS_VALIDOS:
            raise ValueError(
                f"Estado de etapa inválido. Use: {', '.join(cls.ESTADOS_VALIDOS)}."
            )
        return limpio

    @property
    def observacion(self) -> str:
        return self._observacion

    @observacion.setter
    def observacion(self, valor: str):
        self._observacion = texto_opcional(valor, "La observación", maximo=255)

    def marcar_en_curso(self, observacion: str = ""):
        self.estado_etapa = "en_curso"
        self.fecha_actualizacion = datetime.now()
        if observacion:
            self.observacion = observacion

    def marcar_completada(self, observacion: str = ""):
        self.estado_etapa = "completada"
        self.fecha_actualizacion = datetime.now()
        if observacion:
            self.observacion = observacion

    def __str__(self) -> str:
        etiqueta = (
            f"{self.destino_nombre} ({self.destino_pais})"
            if self.destino_nombre
            else f"Parada #{self.parada_itinerario_id}"
        )
        paso = f"Etapa {self.orden_visita}" if self.orden_visita else f"ID {self.id}"
        nota = f" | Obs.: {self.observacion}" if self.observacion else ""
        return (
            f"    - [{paso}] {etiqueta}: {self.estado_etapa.upper()} "
            f"(Act.: {self.fecha_actualizacion}){nota}"
        )


class Pasajero:
    def __init__(
        self,
        documento_identidad: str,
        nombre_completo: str,
        fecha_nacimiento: date | str | None = None,
        telefono: str = "",
        id: int | None = None,
        reserva_id: int | None = None,
        avances: list[AvanceEtapa] | None = None,
    ):
        self.id = id
        self.reserva_id = reserva_id
        self.documento_identidad = documento_identidad
        self.nombre_completo = nombre_completo
        self.fecha_nacimiento = self.validar_fecha_nacimiento(fecha_nacimiento)
        self.telefono = telefono
        self.avances: list[AvanceEtapa] = list(avances) if avances else []

    @staticmethod
    def validar_documento(valor: str) -> str:
        doc = texto_no_vacio(valor, "El documento de identidad", maximo=30)
        normalizado = doc.replace(".", "").replace(" ", "").upper()
        if len(normalizado) < 5:
            raise ValueError("El documento de identidad debe tener al menos 5 caracteres.")
        return normalizado

    @staticmethod
    def validar_fecha_nacimiento(valor: date | str | None) -> date | None:
        if valor is None:
            return None
        if isinstance(valor, date):
            fecha = valor
        elif isinstance(valor, str):
            limpio = valor.strip()
            if not limpio:
                return None
            try:
                fecha = date.fromisoformat(limpio)
            except ValueError:
                raise ValueError(
                    "La fecha de nacimiento debe tener formato YYYY-MM-DD."
                ) from None
        else:
            raise ValueError("Formato de fecha de nacimiento inválido.")

        if fecha > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura.")
        return fecha

    @staticmethod
    def validar_telefono(valor: str) -> str:
        tel = texto_opcional(valor, "El teléfono", maximo=30)
        if tel and sum(c.isdigit() for c in tel) < 7:
            raise ValueError("El teléfono debe contener al menos 7 dígitos.")
        return tel

    @property
    def documento_identidad(self) -> str:
        return self._documento_identidad

    @documento_identidad.setter
    def documento_identidad(self, valor: str):
        self._documento_identidad = self.validar_documento(valor)

    @property
    def nombre_completo(self) -> str:
        return self._nombre_completo

    @nombre_completo.setter
    def nombre_completo(self, valor: str):
        self._nombre_completo = texto_no_vacio(
            valor, "El nombre completo del pasajero", maximo=120
        )

    @property
    def telefono(self) -> str:
        return self._telefono

    @telefono.setter
    def telefono(self, valor: str):
        self._telefono = self.validar_telefono(valor)

    def estado_viaje_agregado(self) -> str:
        """
        Determina el estado global del pasajero según sus etapas:
        - 'pendiente': todas las etapas en pendiente
        - 'finalizado': todas las etapas completadas
        - 'viajando': al menos una etapa en curso o avance parcial
        """
        if not self.avances:
            return "pendiente"
        estados = {a.estado_etapa for a in self.avances}
        if estados == {"pendiente"}:
            return "pendiente"
        if estados == {"completada"}:
            return "finalizado"
        return "viajando"

    def __str__(self) -> str:
        nac = f" | Nac.: {self.fecha_nacimiento}" if self.fecha_nacimiento else ""
        tel = f" | Tel.: {self.telefono}" if self.telefono else ""
        return (
            f"  [Pasajero #{self.id}] {self.nombre_completo} (Doc.: {self.documento_identidad})"
            f"{nac}{tel} | Estado viaje: {self.estado_viaje_agregado().upper()}"
        )


class Reserva:
    ESTADOS_VALIDOS = ("pendiente", "confirmada", "cancelada")

    def __init__(
        self,
        usuario_id: int,
        salida_id: int,
        precio_unitario_congelado: Decimal | float | int | str,
        pasajeros: list[Pasajero] | None = None,
        total_price: Decimal | float | int | str | None = None,
        estado: str = "confirmada",
        fecha_reserva: datetime | str | None = None,
        id: int | None = None,
        cliente_nombre: str = "",
        paquete_titulo: str = "",
        fecha_inicio: date | str | None = None,
        fecha_fin: date | str | None = None,
    ):
        self.id = id
        self.usuario_id = entero_positivo(usuario_id, "El ID del usuario")
        self.salida_id = entero_positivo(salida_id, "El ID de la salida")
        self.precio_unitario_congelado = self._validar_monto(
            precio_unitario_congelado, "El precio unitario congelado"
        )
        self.pasajeros: list[Pasajero] = list(pasajeros) if pasajeros else []
        self.estado = self.validar_estado(estado)
        self.fecha_reserva = fecha_reserva or datetime.now()
        self.cliente_nombre = cliente_nombre
        self.paquete_titulo = paquete_titulo
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin

        if total_price is not None:
            self.precio_total = self._validar_monto(total_price, "El precio total")
        else:
            self.precio_total = self.calcular_total()

    @staticmethod
    def _validar_monto(valor, campo: str) -> Decimal:
        if isinstance(valor, bool):
            raise ValueError(f"{campo} debe ser un monto numérico.")
        try:
            monto = Decimal(str(valor).strip().replace(",", "."))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError(f"{campo} debe ser un monto numérico válido.") from None
        if not monto.is_finite() or monto < Decimal("0"):
            raise ValueError(f"{campo} no puede ser negativo.")
        return monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def validar_estado(cls, estado: str) -> str:
        if not isinstance(estado, str):
            raise ValueError("El estado de la reserva no es válido.")
        limpio = estado.strip().lower()
        if limpio not in cls.ESTADOS_VALIDOS:
            raise ValueError(
                f"Estado inválido. Opciones: {', '.join(cls.ESTADOS_VALIDOS)}."
            )
        return limpio

    def calcular_total(self) -> Decimal:
        cantidad = len(self.pasajeros)
        total = self.precio_unitario_congelado * Decimal(cantidad)
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def confirmar(self):
        if not self.pasajeros:
            raise ValueError("No se puede confirmar una reserva sin pasajeros.")
        self.precio_total = self.calcular_total()
        self.estado = "confirmada"

    def cancelar(self):
        if self.estado == "cancelada":
            raise ValueError("La reserva ya se encuentra cancelada.")
        for p in self.pasajeros:
            if p.estado_viaje_agregado() != "pendiente":
                raise ValueError(
                    "No se puede cancelar una reserva cuyo viaje ya inició o finalizó."
                )
        self.estado = "cancelada"

    def __str__(self) -> str:
        tour = f"{self.paquete_titulo} " if self.paquete_titulo else f"Salida #{self.salida_id} "
        fechas = (
            f"({self.fecha_inicio} al {self.fecha_fin}) "
            if self.fecha_inicio and self.fecha_fin
            else ""
        )
        titular = f" | Titular: {self.cliente_nombre}" if self.cliente_nombre else ""
        return (
            f"[Reserva #{self.id}] {tour}{fechas}| Pasajeros: {len(self.pasajeros)} | "
            f"Tarifa unit.: ${self.precio_unitario_congelado:,.2f} | "
            f"Total: ${self.precio_total:,.2f} | Estado: {self.estado.upper()}{titular}"
        )