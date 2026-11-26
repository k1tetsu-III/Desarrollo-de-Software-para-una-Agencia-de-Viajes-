from datetime import date, datetime
from decimal import Decimal
from dominio.reserva import AvanceEtapa, Pasajero, Reserva
from persistencia.conexion import conexion_segura, marcador_sql


class ReservaDAO:
    @staticmethod
    def _mapear_avance(fila) -> AvanceEtapa:
        return AvanceEtapa(
            id=fila[0],
            pasajero_id=fila[1],
            parada_itinerario_id=fila[2],
            estado_etapa=fila[3],
            fecha_actualizacion=fila[4],
            observacion=fila[5],
            orden_visita=int(fila[6]),
            destino_nombre=fila[7],
            destino_pais=fila[8],
        )

    @staticmethod
    def _mapear_pasajero(fila) -> Pasajero:
        fecha_nac = date.fromisoformat(str(fila[4])) if fila[4] else None
        return Pasajero(
            id=fila[0],
            reserva_id=fila[1],
            documento_identidad=fila[2],
            nombre_completo=fila[3],
            fecha_nacimiento=fecha_nac,
            telefono=fila[5] or "",
        )

    @staticmethod
    def _mapear_reserva(fila) -> Reserva:
        return Reserva(
            id=fila[0],
            usuario_id=int(fila[1]),
            salida_id=int(fila[2]),
            fecha_reserva=fila[3],
            precio_unitario_congelado=Decimal(str(fila[4])),
            total_price=Decimal(str(fila[5])),
            estado=fila[6],
            cliente_nombre=fila[7],
            paquete_titulo=fila[8],
            fecha_inicio=date.fromisoformat(str(fila[9])),
            fecha_fin=date.fromisoformat(str(fila[10])),
        )

    @classmethod
    def _cargar_avances_pasajero(cls, cursor, pasajero_id: int) -> list[AvanceEtapa]:
        p = marcador_sql()
        sql = f"""
            SELECT sp.id, sp.passenger_id, sp.itinerary_stop_id, sp.stage_status,
                   sp.updated_at, sp.notes, st.visit_order, d.name, d.country
            FROM stage_progress sp
            INNER JOIN itinerary_stops st ON st.id = sp.itinerary_stop_id
            INNER JOIN destinations d ON d.id = st.destination_id
            WHERE sp.passenger_id = {p}
            ORDER BY st.visit_order ASC
        """
        cursor.execute(sql, (pasajero_id,))
        return [cls._mapear_avance(fila) for fila in cursor.fetchall()]

    @classmethod
    def _cargar_pasajeros_reserva(cls, cursor, reserva_id: int) -> list[Pasajero]:
        p = marcador_sql()
        sql = f"""
            SELECT id, booking_id, document_id, full_name, birth_date, phone
            FROM passengers
            WHERE booking_id = {p}
            ORDER BY id ASC
        """
        cursor.execute(sql, (reserva_id,))
        pasajeros = [cls._mapear_pasajero(fila) for fila in cursor.fetchall()]
        for pasajero in pasajeros:
            pasajero.avances = cls._cargar_avances_pasajero(cursor, pasajero.id)
        return pasajeros

    @classmethod
    def crear_reserva_atomica(
        cls,
        reserva: Reserva,
        paradas_itinerario_ids: list[int],
    ) -> Reserva:
        """
        Transacción ACID (BPMN 3):
        1. Descuenta cupos atómicamente solo si la salida está 'abierta' y tiene cupos suficientes.
        2. Inserta la reserva con tarifa congelada.
        3. Inserta cada pasajero nominal.
        4. Inicializa todas las etapas de avance en estado 'pendiente'.
        """
        cantidad = len(reserva.pasajeros)
        if cantidad == 0:
            raise ValueError("Debe registrar al menos un pasajero.")

        reserva.confirmar()
        p = marcador_sql()

        sql_descontar_cupos = f"""
            UPDATE package_departures
            SET available_slots = available_slots - {p},
                status = CASE WHEN available_slots - {p} = 0 THEN 'cerrada' ELSE status END
            WHERE id = {p} AND status = 'abierta' AND available_slots >= {p}
        """
        sql_insert_reserva = f"""
            INSERT INTO bookings (user_id, departure_id, frozen_unit_price, total_price, status)
            VALUES ({p}, {p}, {p}, {p}, {p})
        """
        sql_insert_pasajero = f"""
            INSERT INTO passengers (booking_id, document_id, full_name, birth_date, phone)
            VALUES ({p}, {p}, {p}, {p}, {p})
        """
        sql_insert_avance = f"""
            INSERT INTO stage_progress (passenger_id, itinerary_stop_id, stage_status, notes)
            VALUES ({p}, {p}, 'pendiente', '')
        """

        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(
                    sql_descontar_cupos,
                    (cantidad, cantidad, reserva.salida_id, cantidad),
                )
                if cursor.rowcount == 0:
                    raise ValueError(
                        "No fue posible confirmar la reserva: cupos insuficientes o salida cerrada."
                    )

                cursor.execute(
                    sql_insert_reserva,
                    (
                        reserva.usuario_id,
                        reserva.salida_id,
                        float(reserva.precio_unitario_congelado),
                        float(reserva.precio_total),
                        reserva.estado,
                    ),
                )
                reserva.id = cursor.lastrowid

                for pasajero in reserva.pasajeros:
                    pasajero.reserva_id = reserva.id
                    fecha_nac_sql = (
                        pasajero.fecha_nacimiento.isoformat()
                        if pasajero.fecha_nacimiento
                        else None
                    )
                    cursor.execute(
                        sql_insert_pasajero,
                        (
                            reserva.id,
                            pasajero.documento_identidad,
                            pasajero.nombre_completo,
                            fecha_nac_sql,
                            pasajero.telefono,
                        ),
                    )
                    pasajero.id = cursor.lastrowid

                    for stop_id in paradas_itinerario_ids:
                        cursor.execute(sql_insert_avance, (pasajero.id, stop_id))

                reserva.pasajeros = cls._cargar_pasajeros_reserva(cursor, reserva.id)
                return reserva
            finally:
                cursor.close()

    @classmethod
    def buscar_reserva_por_id(cls, reserva_id: int) -> Reserva | None:
        p = marcador_sql()
        sql = f"""
            SELECT b.id, b.user_id, b.departure_id, b.booking_date,
                   b.frozen_unit_price, b.total_price, b.status,
                   u.full_name, pkg.title, d.start_date, d.end_date
            FROM bookings b
            INNER JOIN users u ON u.id = b.user_id
            INNER JOIN package_departures d ON d.id = b.departure_id
            INNER JOIN packages pkg ON pkg.id = d.package_id
            WHERE b.id = {p}
        """
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, (reserva_id,))
                fila = cursor.fetchone()
                if not fila:
                    return None
                reserva = cls._mapear_reserva(fila)
                reserva.pasajeros = cls._cargar_pasajeros_reserva(cursor, reserva.id)
                return reserva
            finally:
                cursor.close()

    @classmethod
    def listar_reservas(cls, usuario_id: int | None = None) -> list[Reserva]:
        p = marcador_sql()
        sql = """
            SELECT b.id, b.user_id, b.departure_id, b.booking_date,
                   b.frozen_unit_price, b.total_price, b.status,
                   u.full_name, pkg.title, d.start_date, d.end_date
            FROM bookings b
            INNER JOIN users u ON u.id = b.user_id
            INNER JOIN package_departures d ON d.id = b.departure_id
            INNER JOIN packages pkg ON pkg.id = d.package_id
        """
        parametros = []
        if usuario_id is not None:
            sql += f" WHERE b.user_id = {p}"
            parametros.append(usuario_id)
        sql += " ORDER BY b.booking_date DESC, b.id DESC"

        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, tuple(parametros))
                reservas = [cls._mapear_reserva(fila) for fila in cursor.fetchall()]
                for r in reservas:
                    r.pasajeros = cls._cargar_pasajeros_reserva(cursor, r.id)
                return reservas
            finally:
                cursor.close()

    @classmethod
    def cancelar_reserva_atomica(cls, reserva: Reserva) -> Reserva:
        reserva.cancelar()
        cantidad = len(reserva.pasajeros)
        p = marcador_sql()

        sql_cancelar = f"UPDATE bookings SET status = 'cancelada' WHERE id = {p} AND status != 'cancelada'"
        sql_liberar = f"""
            UPDATE package_departures
            SET available_slots = available_slots + {p},
                status = CASE WHEN status = 'cerrada' THEN 'abierta' ELSE status END
            WHERE id = {p}
        """
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql_cancelar, (reserva.id,))
                if cursor.rowcount == 0:
                    raise ValueError("No fue posible cancelar la reserva.")
                cursor.execute(sql_liberar, (cantidad, reserva.salida_id))
                return reserva
            finally:
                cursor.close()

    @classmethod
    def actualizar_avance_etapa(
        cls,
        pasajero_id: int,
        orden_visita: int,
        nuevo_estado: str,
        observacion: str = "",
    ) -> list[AvanceEtapa]:
        estado_ok = AvanceEtapa.validar_estado(nuevo_estado)
        p = marcador_sql()

        sql_reserva_estado = f"""
            SELECT b.status
            FROM bookings b
            INNER JOIN passengers pas ON pas.booking_id = b.id
            WHERE pas.id = {p}
        """
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql_reserva_estado, (pasajero_id,))
                fila_res = cursor.fetchone()
                if not fila_res:
                    raise ValueError("Pasajero no encontrado.")
                if fila_res[0] == "cancelada":
                    raise ValueError("No se puede registrar avance sobre una reserva cancelada.")

                avances = cls._cargar_avances_pasajero(cursor, pasajero_id)
                objetivo = next(
                    (a for a in avances if a.orden_visita == orden_visita), None
                )
                if objetivo is None:
                    raise ValueError(
                        f"El pasajero no tiene registrada una etapa con orden {orden_visita}."
                    )

                if orden_visita > 1 and estado_ok in ("en_curso", "completada"):
                    anterior = next(
                        (a for a in avances if a.orden_visita == orden_visita - 1), None
                    )
                    if anterior is not None and anterior.estado_etapa != "completada":
                        raise ValueError(
                            f"Debe completar primero la etapa {orden_visita - 1} "
                            f"({anterior.destino_nombre}) antes de avanzar a la etapa {orden_visita}."
                        )

                ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sql_upd = f"""
                    UPDATE stage_progress
                    SET stage_status = {p}, updated_at = {p}, notes = {p}
                    WHERE id = {p}
                """
                cursor.execute(sql_upd, (estado_ok, ahora, observacion.strip(), objetivo.id))
                return cls._cargar_avances_pasajero(cursor, pasajero_id)
            finally:
                cursor.close()

    @classmethod
    def consultar_pasajeros_filtrados(
        cls,
        paquete_id: int | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> list[dict]:
        """
        Obtiene pasajeros con reservas confirmadas y sus etapas para reportes
        por paquete, rango de fechas y estado agregado del viaje.
        """
        p = marcador_sql()
        sql = """
            SELECT pas.id, pas.booking_id, pas.document_id, pas.full_name,
                   pas.birth_date, pas.phone,
                   pkg.id, pkg.title, dep.start_date, dep.end_date, u.full_name
            FROM passengers pas
            INNER JOIN bookings b ON b.id = pas.booking_id
            INNER JOIN package_departures dep ON dep.id = b.departure_id
            INNER JOIN packages pkg ON pkg.id = dep.package_id
            INNER JOIN users u ON u.id = b.user_id
            WHERE b.status = 'confirmada'
        """
        parametros = []
        if paquete_id is not None:
            sql += f" AND pkg.id = {p}"
            parametros.append(paquete_id)
        if fecha_desde is not None:
            sql += f" AND dep.start_date >= {p}"
            parametros.append(fecha_desde.isoformat())
        if fecha_hasta is not None:
            sql += f" AND dep.start_date <= {p}"
            parametros.append(fecha_hasta.isoformat())

        sql += " ORDER BY dep.start_date ASC, pas.id ASC"

        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, tuple(parametros))
                filas = cursor.fetchall()
                resultados = []
                for f in filas:
                    pasajero = cls._mapear_pasajero(f[:6])
                    pasajero.avances = cls._cargar_avances_pasajero(cursor, pasajero.id)
                    resultados.append(
                        {
                            "pasajero": pasajero,
                            "paquete_id": int(f[6]),
                            "paquete_titulo": f[7],
                            "fecha_inicio": date.fromisoformat(str(f[8])),
                            "fecha_fin": date.fromisoformat(str(f[9])),
                            "titular_reserva": f[10],
                            "estado_viaje": pasajero.estado_viaje_agregado(),
                        }
                    )
                return resultados
            finally:
                cursor.close()