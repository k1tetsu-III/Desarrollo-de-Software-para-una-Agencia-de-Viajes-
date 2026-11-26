from dominio.paquete import PaqueteTuristico, ParadaItinerario, SalidaPaquete
from persistencia.destino_dao import DestinoDAO
from persistencia.paquete_dao import PaqueteDAO
from servicios.permisos import exigir_admin, exigir_sesion


def _construir_paradas_validadas(
    paradas_input: list[tuple[int, int, str]],
) -> list[ParadaItinerario]:
    """
    Valida que cada destino exista y esté activo (regla del BPMN 2:
    un destino retirado no puede incluirse en nuevos paquetes).
    paradas_input: lista de tuplas (destino_id, orden, notas)
    """
    if not paradas_input or len(paradas_input) < 2:
        raise ValueError("Debe ingresar al menos 2 destinos para armar el paquete.")

    paradas_construidas: list[ParadaItinerario] = []
    for destino_id, orden, notas in paradas_input:
        destino = DestinoDAO.buscar_por_id(destino_id)
        if destino is None:
            raise ValueError(f"El destino con ID {destino_id} no existe.")
        if not destino.activo:
            raise ValueError(
                f"El destino '{destino.nombre}' está retirado y no puede agregarse a nuevos paquetes."
            )

        parada = ParadaItinerario(
            destino_id=destino.id,
            orden=orden,
            notas=notas,
            destino_nombre=destino.nombre,
            destino_pais=destino.pais,
            destino_costo_base=destino.costo_base,
            destino_activo=destino.activo,
        )
        paradas_construidas.append(parada)

    return paradas_construidas


def crear_paquete(
    sesion: dict | None,
    titulo: str,
    descripcion: str,
    paradas_input: list[tuple[int, int, str]],
) -> PaqueteTuristico:
    exigir_admin(sesion)
    paradas = _construir_paradas_validadas(paradas_input)

    paquete = PaqueteTuristico(titulo=titulo, descripcion=descripcion, activo=True)
    for parada in paradas:
        paquete.agregar_parada(parada)

    paquete.validar_itinerario()
    return PaqueteDAO.insertar_paquete(paquete)


def listar_paquetes(
    sesion: dict | None, solo_activos: bool = True
) -> list[PaqueteTuristico]:
    exigir_sesion(sesion)
    return PaqueteDAO.listar_paquetes(solo_activos=solo_activos)


def obtener_paquete(sesion: dict | None, paquete_id: int) -> PaqueteTuristico:
    exigir_sesion(sesion)
    paquete = PaqueteDAO.buscar_paquete_por_id(paquete_id)
    if paquete is None:
        raise ValueError("Paquete turístico no encontrado.")
    return paquete


def actualizar_paquete(
    sesion: dict | None,
    paquete_id: int,
    titulo: str | None = None,
    descripcion: str | None = None,
    nuevas_paradas_input: list[tuple[int, int, str]] | None = None,
) -> PaqueteTuristico:
    exigir_admin(sesion)
    paquete = PaqueteDAO.buscar_paquete_por_id(paquete_id)
    if paquete is None:
        raise ValueError("Paquete turístico no encontrado.")

    if titulo is not None:
        paquete.titulo = titulo
    if descripcion is not None:
        paquete.descripcion = descripcion

    reemplazar_itinerario = False
    if nuevas_paradas_input is not None:
        if PaqueteDAO.contar_reservas_paquete(paquete_id) > 0:
            raise ValueError(
                "No se puede modificar el itinerario porque el paquete ya tiene reservas registradas."
            )
        paradas = _construir_paradas_validadas(nuevas_paradas_input)
        paquete.itinerario = []
        for parada in paradas:
            paquete.agregar_parada(parada)
        reemplazar_itinerario = True

    paquete.validar_itinerario()
    return PaqueteDAO.actualizar_paquete(
        paquete, reemplazar_itinerario=reemplazar_itinerario
    )


def retirar_o_eliminar_paquete(
    sesion: dict | None, paquete_id: int
) -> tuple[str, PaqueteTuristico]:
    exigir_admin(sesion)
    paquete = PaqueteDAO.buscar_paquete_por_id(paquete_id)
    if paquete is None:
        raise ValueError("Paquete turístico no encontrado.")

    reservas_asociadas = PaqueteDAO.contar_reservas_paquete(paquete_id)
    if reservas_asociadas > 0 or len(paquete.salidas) > 0:
        if not paquete.activo:
            raise ValueError("El paquete ya se encuentra desactivado.")
        paquete.activo = False
        PaqueteDAO.desactivar_paquete(paquete.id)
        return "desactivado", paquete

    PaqueteDAO.eliminar_paquete_fisico(paquete.id)
    return "eliminado", paquete


def programar_salida(
    sesion: dict | None,
    paquete_id: int,
    fecha_inicio,
    fecha_fin,
    precio_por_persona,
    cupos_totales: int,
) -> SalidaPaquete:
    exigir_admin(sesion)
    paquete = PaqueteDAO.buscar_paquete_por_id(paquete_id)
    if paquete is None:
        raise ValueError("Paquete turístico no encontrado.")
    if not paquete.activo:
        raise ValueError("No se pueden programar salidas para un paquete inactivo.")

    paquete.validar_itinerario()
    salida = SalidaPaquete(
        paquete_id=paquete.id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        precio_por_persona=precio_por_persona,
        cupos_totales=cupos_totales,
        cupos_disponibles=cupos_totales,
        estado="abierta",
        paquete_titulo=paquete.titulo,
    )
    return PaqueteDAO.insertar_salida(salida)


def listar_salidas_disponibles(
    sesion: dict | None, paquete_id: int | None = None
) -> list[SalidaPaquete]:
    exigir_sesion(sesion)
    return PaqueteDAO.listar_salidas_disponibles(paquete_id=paquete_id)


def cancelar_salida(sesion: dict | None, salida_id: int) -> SalidaPaquete:
    exigir_admin(sesion)
    salida = PaqueteDAO.buscar_salida_por_id(salida_id)
    if salida is None:
        raise ValueError("Salida no encontrada.")
    if salida.estado == "cancelada":
        raise ValueError("La salida ya se encuentra cancelada.")

    salida.estado = "cancelada"
    PaqueteDAO.actualizar_salida(salida)
    return salida