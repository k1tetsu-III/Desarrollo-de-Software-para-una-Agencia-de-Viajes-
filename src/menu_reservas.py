from dominio.paquete import SalidaPaquete
from dominio.reserva import AvanceEtapa, Pasajero
from menu_comun import operacion_segura, pedir, solicitar_opcion
from servicios.gestion_paquetes import listar_salidas_disponibles
from servicios.gestion_reservas import (
    cancelar_reserva,
    consultar_pasajeros_reporte,
    crear_reserva,
    listar_mis_reservas,
    listar_todas_las_reservas,
    obtener_detalle_reserva,
    registrar_avance_etapa,
)
from utilidades import entero_positivo, texto_no_vacio, texto_opcional


def _imprimir_reserva_completa(reserva):
    print("\n ", reserva)
    for pasajero in reserva.pasajeros:
        print("  ", pasajero)
        for avance in pasajero.avances:
            print("  ", avance)


@operacion_segura
def _accion_reservar(usuario_actual):
    salidas = listar_salidas_disponibles(usuario_actual)
    if not salidas:
        print("  No hay salidas disponibles con cupos abiertos en este momento.")
        return

    print("\n  Salidas abiertas disponibles:")
    for s in salidas:
        print("   ", s)

    salida_id = pedir("ID de la salida a reservar: ", entero_positivo, "El ID de la salida")
    cantidad = pedir("Cantidad de pasajeros: ", entero_positivo, "La cantidad de pasajeros")

    datos_pasajeros: list[dict] = []
    for idx in range(1, cantidad + 1):
        print(f"\n  --- Datos del Pasajero {idx} de {cantidad} ---")
        doc = pedir(
            "  Documento de identidad (RUT/DNI/Pasaporte): ",
            Pasajero.validar_documento,
        )
        nombre = pedir(
            "  Nombre completo: ",
            texto_no_vacio,
            "El nombre completo",
            120,
        )
        fecha_nac = pedir(
            "  Fecha de nacimiento (YYYY-MM-DD, opcional): ",
            Pasajero.validar_fecha_nacimiento,
            vacio_ok=True,
        )
        telefono = pedir(
            "  Teléfono de contacto (opcional): ",
            Pasajero.validar_telefono,
        )
        datos_pasajeros.append(
            {
                "documento_identidad": doc,
                "nombre_completo": nombre,
                "fecha_nacimiento": fecha_nac,
                "telefono": telefono,
            }
        )

    reserva = crear_reserva(usuario_actual, salida_id, datos_pasajeros)
    print("\n  ¡Reserva confirmada con éxito! Comprobante:")
    _imprimir_reserva_completa(reserva)


@operacion_segura
def _accion_mis_reservas(usuario_actual):
    reservas = listar_mis_reservas(usuario_actual)
    if not reservas:
        print("  Aún no tienes reservas registradas.")
        return
    for r in reservas:
        _imprimir_reserva_completa(r)


@operacion_segura
def _accion_todas_reservas(usuario_actual):
    reservas = listar_todas_las_reservas(usuario_actual)
    if not reservas:
        print("  No existen reservas en el sistema.")
        return
    for r in reservas:
        _imprimir_reserva_completa(r)


@operacion_segura
def _accion_detalle_reserva(usuario_actual):
    reserva_id = pedir("ID de la reserva: ", entero_positivo, "El ID de la reserva")
    reserva = obtener_detalle_reserva(usuario_actual, reserva_id)
    _imprimir_reserva_completa(reserva)


@operacion_segura
def _accion_cancelar_reserva(usuario_actual):
    reserva_id = pedir("ID de la reserva a cancelar: ", entero_positivo, "El ID de la reserva")
    reserva = cancelar_reserva(usuario_actual, reserva_id)
    print(f"  Reserva #{reserva.id} cancelada correctamente. Cupos liberados.")


@operacion_segura
def _accion_registrar_avance(usuario_actual):
    reserva_id = pedir("ID de la reserva a gestionar: ", entero_positivo, "El ID de la reserva")
    reserva = obtener_detalle_reserva(usuario_actual, reserva_id)
    _imprimir_reserva_completa(reserva)

    if reserva.estado == "cancelada":
        print("  Esta reserva está cancelada y no admite cambios de etapa.")
        return

    pasajero_id = pedir("ID del pasajero: ", entero_positivo, "El ID del pasajero")
    orden_visita = pedir(
        "Número de etapa (orden de visita 1, 2, ...): ",
        entero_positivo,
        "El número de etapa",
    )
    nuevo_estado = pedir(
        "Nuevo estado (pendiente / en_curso / completada): ",
        AvanceEtapa.validar_estado,
    )
    observacion = pedir(
        "Observación o bitácora (opcional): ",
        texto_opcional,
        "La observación",
        255,
    )

    avances = registrar_avance_etapa(
        usuario_actual, pasajero_id, orden_visita, nuevo_estado, observacion
    )
    print("\n  Avance actualizado. Estado actual de etapas del pasajero:")
    for av in avances:
        print("  ", av)


@operacion_segura
def _accion_reporte_pasajeros(usuario_actual):
    print("  (Presione Enter para omitir cualquier filtro)")
    paquete_id = pedir(
        "Filtrar por ID de paquete: ",
        entero_positivo,
        "El ID del paquete",
        vacio_ok=True,
    )
    fecha_desde = pedir(
        "Fecha de salida desde (YYYY-MM-DD): ",
        SalidaPaquete.validar_fecha,
        "La fecha desde",
        vacio_ok=True,
    )
    fecha_hasta = pedir(
        "Fecha de salida hasta (YYYY-MM-DD): ",
        SalidaPaquete.validar_fecha,
        "La fecha hasta",
        vacio_ok=True,
    )
    estado = input("Estado del viaje (pendiente / viajando / finalizado): ").strip()

    registros = consultar_pasajeros_reporte(
        usuario_actual,
        paquete_id=paquete_id,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        estado_viaje=estado or None,
    )

    if not registros:
        print("  No se encontraron pasajeros con esos criterios.")
        return

    resumen = {"pendiente": 0, "viajando": 0, "finalizado": 0}
    print(f"\n  Total de pasajeros encontrados: {len(registros)}")
    for item in registros:
        est = item["estado_viaje"]
        resumen[est] = resumen.get(est, 0) + 1
        pas = item["pasajero"]
        print(
            f"  - {pas.nombre_completo} (Doc.: {pas.documento_identidad}) | "
            f"Paquete: {item['paquete_titulo']} ({item['fecha_inicio']} al {item['fecha_fin']}) | "
            f"Estado: {est.upper()} | Titular: {item['titular_reserva']}"
        )

    print(
        f"\n  Resumen por estado -> Pendientes: {resumen['pendiente']} | "
        f"Viajando: {resumen['viajando']} | Finalizados: {resumen['finalizado']}"
    )


def menu_reservas_cliente(usuario_actual):
    acciones = {
        1: lambda: _accion_reservar(usuario_actual),
        2: lambda: _accion_mis_reservas(usuario_actual),
        3: lambda: _accion_detalle_reserva(usuario_actual),
        4: lambda: _accion_cancelar_reserva(usuario_actual),
    }
    while True:
        print("\n--- MIS RESERVAS Y VIAJES (CLIENTE) ---")
        print("1. Reservar una salida disponible")
        print("2. Ver mi historial de reservas y avances")
        print("3. Consultar detalle de una reserva por ID")
        print("4. Cancelar una reserva")
        print("0. Volver")

        opcion = solicitar_opcion(4)
        if opcion == 0:
            return
        acciones[opcion]()


def menu_reservas_admin(usuario_actual):
    acciones = {
        1: lambda: _accion_todas_reservas(usuario_actual),
        2: lambda: _accion_detalle_reserva(usuario_actual),
        3: lambda: _accion_registrar_avance(usuario_actual),
        4: lambda: _accion_reporte_pasajeros(usuario_actual),
        5: lambda: _accion_cancelar_reserva(usuario_actual),
    }
    while True:
        print("\n--- GESTIÓN DE RESERVAS Y SEGUIMIENTO (ADMIN) ---")
        print("1. Listar todas las reservas del sistema")
        print("2. Ver detalle de reserva y etapas por ID")
        print("3. Registrar avance de etapa de viaje (En curso / Completada)")
        print("4. Consultar pasajeros por paquete, período y estado")
        print("5. Cancelar una reserva")
        print("0. Volver")

        opcion = solicitar_opcion(5)
        if opcion == 0:
            return
        acciones[opcion]()