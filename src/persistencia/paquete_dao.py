from datetime import date
from decimal import Decimal
from dominio.paquete import PaqueteTuristico, ParadaItinerario, SalidaPaquete
from persistencia.conexion import conexion_segura, marcador_sql


class PaqueteDAO:
    @staticmethod
    def _mapear_paquete(fila) -> PaqueteTuristico:
        return PaqueteTuristico(
            id=fila[0],
            titulo=fila[1],
            descripcion=fila[2],
            activo=bool(fila[3]),
        )

    @staticmethod
    def _mapear_parada(fila) -> ParadaItinerario:
        return ParadaItinerario(
            id=fila[0],
            paquete_id=fila[1],
            destino_id=fila[2],
            orden=fila[3],
            notas=fila[4],
            destino_nombre=fila[5],
            destino_pais=fila[6],
            destino_costo_base=Decimal(str(fila[7])),
            destino_activo=bool(fila[8]),
        )

    @staticmethod
    def _mapear_salida(fila) -> SalidaPaquete:
        return SalidaPaquete(
            id=fila[0],
            paquete_id=fila[1],
            fecha_inicio=date.fromisoformat(str(fila[2])),
            fecha_fin=date.fromisoformat(str(fila[3])),
            precio_por_persona=Decimal(str(fila[4])),
            cupos_totales=int(fila[5]),
            cupos_disponibles=int(fila[6]),
            estado=fila[7],
            paquete_titulo=fila[8] if len(fila) > 8 else "",
        )

    @classmethod
    def _cargar_itinerario(cls, cursor, paquete_id: int) -> list[ParadaItinerario]:
        p = marcador_sql()
        sql = f"""
            SELECT s.id, s.package_id, s.destination_id, s.visit_order, s.notes,
                   d.name, d.country, d.base_cost, d.is_active
            FROM itinerary_stops s
            INNER JOIN destinations d ON d.id = s.destination_id
            WHERE s.package_id = {p}
            ORDER BY s.visit_order ASC
        """
        cursor.execute(sql, (paquete_id,))
        return [cls._mapear_parada(fila) for fila in cursor.fetchall()]

    @classmethod
    def _cargar_salidas(cls, cursor, paquete_id: int) -> list[SalidaPaquete]:
        p = marcador_sql()
        sql = f"""
            SELECT id, package_id, start_date, end_date, unit_price,
                   total_slots, available_slots, status
            FROM package_departures
            WHERE package_id = {p}
            ORDER BY start_date ASC, id ASC
        """
        cursor.execute(sql, (paquete_id,))
        return [cls._mapear_salida(fila) for fila in cursor.fetchall()]

    @classmethod
    def insertar_paquete(cls, paquete: PaqueteTuristico) -> PaqueteTuristico:
        """Inserta el paquete y todas sus paradas en una única transacción."""
        paquete.validar_itinerario()
        p = marcador_sql()
        sql_paquete = f"""
            INSERT INTO packages (title, description, is_active)
            VALUES ({p}, {p}, {p})
        """
        sql_parada = f"""
            INSERT INTO itinerary_stops (package_id, destination_id, visit_order, notes)
            VALUES ({p}, {p}, {p}, {p})
        """
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(
                    sql_paquete,
                    (paquete.titulo, paquete.descripcion, 1 if paquete.activo else 0),
                )
                paquete.id = cursor.lastrowid

                for parada in paquete.obtener_itinerario():
                    parada.paquete_id = paquete.id
                    cursor.execute(
                        sql_parada,
                        (paquete.id, parada.destino_id, parada.orden, parada.notas),
                    )
                    parada.id = cursor.lastrowid

                paquete.itinerario = cls._cargar_itinerario(cursor, paquete.id)
                return paquete
            finally:
                cursor.close()

    @classmethod
    def listar_paquetes(cls, solo_activos: bool = False) -> list[PaqueteTuristico]:
        sql = "SELECT id, title, description, is_active FROM packages"
        if solo_activos:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY id ASC"

        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql)
                paquetes = [cls._mapear_paquete(fila) for fila in cursor.fetchall()]
                for paquete in paquetes:
                    paquete.itinerario = cls._cargar_itinerario(cursor, paquete.id)
                    paquete.salidas = cls._cargar_salidas(cursor, paquete.id)
                return paquetes
            finally:
                cursor.close()

    @classmethod
    def buscar_paquete_por_id(cls, paquete_id: int) -> PaqueteTuristico | None:
        p = marcador_sql()
        sql = f"SELECT id, title, description, is_active FROM packages WHERE id = {p}"
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, (paquete_id,))
                fila = cursor.fetchone()
                if not fila:
                    return None
                paquete = cls._mapear_paquete(fila)
                paquete.itinerario = cls._cargar_itinerario(cursor, paquete.id)
                paquete.salidas = cls._cargar_salidas(cursor, paquete.id)
                return paquete
            finally:
                cursor.close()

    @classmethod
    def actualizar_paquete(
        cls, paquete: PaqueteTuristico, reemplazar_itinerario: bool = False
    ) -> PaqueteTuristico:
        paquete.validar_itinerario()
        p = marcador_sql()
        sql_update = f"""
            UPDATE packages
            SET title = {p}, description = {p}, is_active = {p}
            WHERE id = {p}
        """
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(
                    sql_update,
                    (
                        paquete.titulo,
                        paquete.descripcion,
                        1 if paquete.activo else 0,
                        paquete.id,
                    ),
                )
                if reemplazar_itinerario:
                    cursor.execute(
                        f"DELETE FROM itinerary_stops WHERE package_id = {p}",
                        (paquete.id,),
                    )
                    sql_parada = f"""
                        INSERT INTO itinerary_stops (package_id, destination_id, visit_order, notes)
                        VALUES ({p}, {p}, {p}, {p})
                    """
                    for parada in paquete.obtener_itinerario():
                        parada.paquete_id = paquete.id
                        cursor.execute(
                            sql_parada,
                            (paquete.id, parada.destino_id, parada.orden, parada.notas),
                        )
                        parada.id = cursor.lastrowid

                paquete.itinerario = cls._cargar_itinerario(cursor, paquete.id)
                paquete.salidas = cls._cargar_salidas(cursor, paquete.id)
                return paquete
            finally:
                cursor.close()

    @classmethod
    def contar_reservas_paquete(cls, paquete_id: int) -> int:
        p = marcador_sql()
        sql = f"""
            SELECT COUNT(*)
            FROM bookings b
            INNER JOIN package_departures d ON d.id = b.departure_id
            WHERE d.package_id = {p}
        """
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, (paquete_id,))
                fila = cursor.fetchone()
                return int(fila[0]) if fila else 0
            finally:
                cursor.close()

    @classmethod
    def desactivar_paquete(cls, paquete_id: int) -> bool:
        p = marcador_sql()
        sql = f"UPDATE packages SET is_active = 0 WHERE id = {p}"
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, (paquete_id,))
                return cursor.rowcount > 0
            finally:
                cursor.close()

    @classmethod
    def eliminar_paquete_fisico(cls, paquete_id: int) -> bool:
        p = marcador_sql()
        sql = f"DELETE FROM packages WHERE id = {p}"
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, (paquete_id,))
                return cursor.rowcount > 0
            finally:
                cursor.close()

    # --- Operaciones de Salidas (package_departures) ---

    @classmethod
    def insertar_salida(cls, salida: SalidaPaquete) -> SalidaPaquete:
        p = marcador_sql()
        sql = f"""
            INSERT INTO package_departures
                (package_id, start_date, end_date, unit_price, total_slots, available_slots, status)
            VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p})
        """
        parametros = (
            salida.paquete_id,
            salida.fecha_inicio.isoformat(),
            salida.fecha_fin.isoformat(),
            float(salida.precio_por_persona),
            salida.cupos_totales,
            salida.cupos_disponibles,
            salida.estado,
        )
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, parametros)
                salida.id = cursor.lastrowid
                return salida
            finally:
                cursor.close()

    @classmethod
    def buscar_salida_por_id(cls, salida_id: int) -> SalidaPaquete | None:
        p = marcador_sql()
        sql = f"""
            SELECT d.id, d.package_id, d.start_date, d.end_date, d.unit_price,
                   d.total_slots, d.available_slots, d.status, pkg.title
            FROM package_departures d
            INNER JOIN packages pkg ON pkg.id = d.package_id
            WHERE d.id = {p}
        """
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, (salida_id,))
                fila = cursor.fetchone()
                return cls._mapear_salida(fila) if fila else None
            finally:
                cursor.close()

    @classmethod
    def listar_salidas_disponibles(cls, paquete_id: int | None = None) -> list[SalidaPaquete]:
        p = marcador_sql()
        sql = """
            SELECT d.id, d.package_id, d.start_date, d.end_date, d.unit_price,
                   d.total_slots, d.available_slots, d.status, pkg.title
            FROM package_departures d
            INNER JOIN packages pkg ON pkg.id = d.package_id
            WHERE pkg.is_active = 1 AND d.status = 'abierta' AND d.available_slots > 0
        """
        parametros = []
        if paquete_id is not None:
            sql += f" AND d.package_id = {p}"
            parametros.append(paquete_id)
        sql += " ORDER BY d.start_date ASC, d.id ASC"

        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, tuple(parametros))
                return [cls._mapear_salida(fila) for fila in cursor.fetchall()]
            finally:
                cursor.close()

    @classmethod
    def actualizar_salida(cls, salida: SalidaPaquete) -> bool:
        p = marcador_sql()
        sql = f"""
            UPDATE package_departures
            SET start_date = {p}, end_date = {p}, unit_price = {p},
                total_slots = {p}, available_slots = {p}, status = {p}
            WHERE id = {p}
        """
        parametros = (
            salida.fecha_inicio.isoformat(),
            salida.fecha_fin.isoformat(),
            float(salida.precio_por_persona),
            salida.cupos_totales,
            salida.cupos_disponibles,
            salida.estado,
            salida.id,
        )
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, parametros)
                return cursor.rowcount > 0
            finally:
                cursor.close()