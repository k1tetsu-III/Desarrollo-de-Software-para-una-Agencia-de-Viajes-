from decimal import Decimal
from dominio.destino import Destino
from persistencia.conexion import conexion_segura, marcador_sql


class DestinoDAO:
    @staticmethod
    def _mapear_fila(fila) -> Destino:
        return Destino(
            id=fila[0],
            nombre=fila[1],
            pais=fila[2],
            descripcion=fila[3],
            actividades=fila[4],
            costo_base=Decimal(str(fila[5])),
            activo=bool(fila[6]),
        )

    @classmethod
    def insertar(cls, destino: Destino) -> Destino:
        p = marcador_sql()
        sql = f"""
            INSERT INTO destinations (name, country, description, activities, base_cost, is_active)
            VALUES ({p}, {p}, {p}, {p}, {p}, {p})
        """
        parametros = (
            destino.nombre,
            destino.pais,
            destino.descripcion,
            destino.actividades,
            float(destino.costo_base),
            1 if destino.activo else 0,
        )
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, parametros)
                destino.id = cursor.lastrowid
                return destino
            finally:
                cursor.close()

    @classmethod
    def listar(cls, solo_activos: bool = False) -> list[Destino]:
        sql = """
            SELECT id, name, country, description, activities, base_cost, is_active
            FROM destinations
        """
        if solo_activos:
            sql += " WHERE is_active = 1"
        sql += " ORDER BY id ASC"

        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql)
                return [cls._mapear_fila(fila) for fila in cursor.fetchall()]
            finally:
                cursor.close()

    @classmethod
    def buscar_por_id(cls, destino_id: int) -> Destino | None:
        p = marcador_sql()
        sql = f"""
            SELECT id, name, country, description, activities, base_cost, is_active
            FROM destinations
            WHERE id = {p}
        """
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, (destino_id,))
                fila = cursor.fetchone()
                return cls._mapear_fila(fila) if fila else None
            finally:
                cursor.close()

    @classmethod
    def buscar_por_nombre_y_pais(cls, nombre: str, pais: str) -> Destino | None:
        p = marcador_sql()
        sql = f"""
            SELECT id, name, country, description, activities, base_cost, is_active
            FROM destinations
            WHERE LOWER(name) = LOWER({p}) AND LOWER(country) = LOWER({p})
        """
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, (nombre.strip(), pais.strip()))
                fila = cursor.fetchone()
                return cls._mapear_fila(fila) if fila else None
            finally:
                cursor.close()

    @classmethod
    def actualizar(cls, destino: Destino) -> bool:
        p = marcador_sql()
        sql = f"""
            UPDATE destinations
            SET name = {p}, country = {p}, description = {p},
                activities = {p}, base_cost = {p}, is_active = {p}
            WHERE id = {p}
        """
        parametros = (
            destino.nombre,
            destino.pais,
            destino.descripcion,
            destino.actividades,
            float(destino.costo_base),
            1 if destino.activo else 0,
            destino.id,
        )
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, parametros)
                return cursor.rowcount > 0
            finally:
                cursor.close()

    @classmethod
    def contar_paquetes_asociados(cls, destino_id: int) -> int:
        """Verifica cuántos paquetes utilizan este destino en su itinerario."""
        p = marcador_sql()
        sql = f"SELECT COUNT(*) FROM itinerary_stops WHERE destination_id = {p}"
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, (destino_id,))
                fila = cursor.fetchone()
                return int(fila[0]) if fila else 0
            finally:
                cursor.close()

    @classmethod
    def retirar(cls, destino_id: int) -> bool:
        """Retiro lógico: marca is_active = 0 conservando historial."""
        p = marcador_sql()
        sql = f"UPDATE destinations SET is_active = 0 WHERE id = {p} AND is_active = 1"
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, (destino_id,))
                return cursor.rowcount > 0
            finally:
                cursor.close()

    @classmethod
    def eliminar_fisico(cls, destino_id: int) -> bool:
        """Eliminación física permitida solo cuando el destino no participa en ningún paquete."""
        p = marcador_sql()
        sql = f"DELETE FROM destinations WHERE id = {p}"
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            try:
                cursor.execute(sql, (destino_id,))
                return cursor.rowcount > 0
            finally:
                cursor.close()