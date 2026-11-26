from datetime import date
from dominio.paquete import SalidaPaquete
from dominio.reserva import AvanceEtapa, Pasajero, Reserva
from persistencia.paquete_dao import PaqueteDAO
from persistencia.reserva_dao import ReservaDAO
from servicios.permisos import exigir_admin, exigir_propietario_o_admin, exigir_sesion


def crear_reserva(
    sesion: dict | None,
    salida_id: int,
    datos_pasajeros: list[dict],
) -> Reserva:
    exigir_sesion(sesion)
    if not datos_pasajeros:
        raise ValueError("Debe ingresar los datos de al menos un pasajero.")

    salida = PaqueteDAO.buscar_salida_por_id(salida_id)
    if salida is None:
        raise ValueError("La salida seleccionada no existe.")

    paquete = PaqueteDAO.buscar_paquete_por_id(salida.paquete_id)
    if paquete is None or not paquete.activo:
        raise ValueError("El paquete asociado a esta salida no se encuentra activo.")

    paquete.validar_itinerario()

    if not salida.hay_cupos(len(datos_pasajeros)):
        raise ValueError(
            f"Cupos insuficientes para la salida #{salida.id} "
            f"(disponibles: {salida.cupos_disponibles}, solicitados: {len(datos_pasajeros)})."
        )

    pasajeros_objs: list[Pasajero] = []
    documentos_vistos: set[str] = set()
    for item in datos_pasajeros:
        pasajero = Pasajero(
            documento_identidad=item.get("documento_identidad", ""),
            nombre_completo=item.get("nombre_completo", ""),
            fecha_nacimiento=item.get("fecha_nacimiento"),
            telefono=item.get("telefono", ""),
        )
        if pasajero.documento_identidad in documentos_vistos:
            raise ValueError(
                f"El documento '{pasajero.documento_identidad}' está duplicado en la misma reserva."
            )
        documentos_vistos.add(pasajero.documento_identidad)
        pasajeros_objs.append(pasajero)

    reserva = Reserva(
        usuario_id=sesion["id"],
        salida_id=salida.id,
        precio_unitario_congelado=salida.precio_por_persona,
        pasajeros=pasajeros_objs,
        estado="confirmada",
    )
    paradas_ids = [parada.id for parada in paquete.obtener_itinerario()]
    creada = ReservaDAO.crear_reserva_atomica(reserva, paradas_ids)
    return ReservaDAO.buscar_reserva_por_id(creada.id) or creada


def listar_mis_reservas(sesion: dict | None) -> list[Reserva]:
    exigir_sesion(sesion)
    return ReservaDAO.listar_reservas(usuario_id=sesion["id"])


def listar_todas_las_reservas(sesion: dict | None) -> list[Reserva]:
    exigir_admin(sesion)
    return ReservaDAO.listar_reservas(usuario_id=None)


def obtener_detalle_reserva(sesion: dict | None, reserva_id: int) -> Reserva:
    exigir_sesion(sesion)
    reserva = ReservaDAO.buscar_reserva_por_id(reserva_id)
    if reserva is None:
        raise ValueError("Reserva no encontrada.")
    exigir_propietario_o_admin(sesion, reserva.usuario_id)
    return reserva


def cancelar_reserva(sesion: dict | None, reserva_id: int) -> Reserva:
    exigir_sesion(sesion)
    reserva = ReservaDAO.buscar_reserva_por_id(reserva_id)
    if reserva is None:
        raise ValueError("Reserva no encontrada.")
    exigir_propietario_o_admin(sesion, reserva.usuario_id)
    return ReservaDAO.cancelar_reserva_atomica(reserva)


def registrar_avance_etapa(
    sesion: dict | None,
    pasajero_id: int,
    orden_visita: int,
    nuevo_estado: str,
    observacion: str = "",
) -> list[AvanceEtapa]:
    exigir_admin(sesion)
    return ReservaDAO.actualizar_avance_etapa(
        pasajero_id=pasajero_id,
        orden_visita=orden_visita,
        nuevo_estado=nuevo_estado,
        observacion=observacion,
    )


def consultar_pasajeros_reporte(
    sesion: dict | None,
    paquete_id: int | None = None,
    fecha_desde: date | str | None = None,
    fecha_hasta: date | str | None = None,
    estado_viaje: str | None = None,
) -> list[dict]:
    exigir_admin(sesion)

    f_desde = (
        SalidaPaquete.validar_fecha(fecha_desde, "La fecha desde")
        if fecha_desde
        else None
    )
    f_hasta = (
        SalidaPaquete.validar_fecha(fecha_hasta, "La fecha hasta")
        if fecha_hasta
        else None
    )
    if f_desde and f_hasta and f_hasta < f_desde:
        raise ValueError("La fecha 'hasta' no puede ser anterior a la fecha 'desde'.")

    estado_filtro = estado_viaje.strip().lower() if estado_viaje else None
    if estado_filtro and estado_filtro not in ("pendiente", "viajando", "finalizado"):
        raise ValueError(
            "Filtro de estado inválido. Use: pendiente, viajando o finalizado."
        )

    registros = ReservaDAO.consultar_pasajeros_filtrados(
        paquete_id=paquete_id,
        fecha_desde=f_desde,
        fecha_hasta=f_hasta,
    )
    if estado_filtro:
        registros = [r for r in registros if r["estado_viaje"] == estado_filtro]
    return registros