from dominio.paquete import SalidaPaquete
from menu_comun import operacion_segura, pedir, solicitar_opcion
from servicios.gestion_destinos import listar_destinos
from servicios.gestion_paquetes import (
    actualizar_paquete,
    cancelar_salida,
    crear_paquete,
    listar_paquetes,
    listar_salidas_disponibles,
    obtener_paquete,
    programar_salida,
    retirar_o_eliminar_paquete,
)
from utilidades import entero_positivo, texto_no_vacio, texto_opcional


def _pedir_paradas_itinerario(usuario_actual) -> list[tuple[int, int, str]]:
    destinos_activos = listar_destinos(usuario_actual, solo_activos=True)
    if len(destinos_activos) < 2:
        raise ValueError(
            "Se requieren al menos 2 destinos activos registrados antes de crear un paquete."
        )

    print("\n  Destinos activos disponibles:")
    for d in destinos_activos:
        print(f"    {d}")

    print("\n  Ingrese los destinos en su orden de visita (mínimo 2):")
    paradas: list[tuple[int, int, str]] = []
    orden = 1
    while True:
        destino_id = pedir(
            f"  Paso {orden} - ID del destino: ", entero_positivo, "El ID del destino"
        )
        notas = pedir(
            f"  Paso {orden} - Notas o actividades destacadas (opcional): ",
            texto_opcional,
            "Las notas",
            255,
        )
        paradas.append((destino_id, orden, notas))
        orden += 1

        if len(paradas) >= 2:
            continuar = input("  ¿Agregar otro destino al itinerario? (s/n): ").strip().lower()
            if continuar != "s":
                break

    return paradas


def mostrar_menu():
    print("\n--- GESTIÓN DE PAQUETES TURÍSTICOS Y SALIDAS ---")
    print("1. Crear nuevo paquete turístico (con itinerario)")
    print("2. Listar paquetes activos (con itinerario y salidas)")
    print("3. Listar todos los paquetes (incluye inactivos)")
    print("4. Ver detalle de un paquete por ID")
    print("5. Actualizar título/descripción de paquete")
    print("6. Programar nueva salida para un paquete")
    print("7. Consultar salidas abiertas con cupos disponibles")
    print("8. Cancelar una salida")
    print("9. Desactivar / eliminar paquete")
    print("0. Volver")


@operacion_segura
def _accion_crear_paquete(usuario_actual):
    titulo = pedir("Título del paquete: ", texto_no_vacio, "El título", 150)
    descripcion = pedir(
        "Descripción general (opcional): ", texto_opcional, "La descripción", 1000
    )
    paradas = _pedir_paradas_itinerario(usuario_actual)

    paquete = crear_paquete(usuario_actual, titulo, descripcion, paradas)
    print(f"\n  Paquete creado correctamente: {paquete}")
    for p in paquete.obtener_itinerario():
        print("  ", p)


@operacion_segura
def _accion_listar_paquetes(usuario_actual, solo_activos: bool):
    paquetes = listar_paquetes(usuario_actual, solo_activos=solo_activos)
    if not paquetes:
        print("  No hay paquetes registrados con ese filtro.")
        return

    for pkg in paquetes:
        print("\n ", pkg)
        for parada in pkg.obtener_itinerario():
            print("  ", parada)
        if pkg.salidas:
            for s in pkg.salidas:
                print("   ->", s)
        else:
            print("   -> Sin salidas programadas aún.")


@operacion_segura
def _accion_detalle_paquete(usuario_actual):
    paquete_id = pedir("ID del paquete: ", entero_positivo, "El ID del paquete")
    pkg = obtener_paquete(usuario_actual, paquete_id)
    print("\n ", pkg)
    if pkg.descripcion:
        print(f"    Descripción: {pkg.descripcion}")
    print("    Itinerario ordenado:")
    for parada in pkg.obtener_itinerario():
        print("  ", parada)
    print("    Salidas programadas:")
    if not pkg.salidas:
        print("      (Ninguna)")
    for s in pkg.salidas:
        print("     ", s)


@operacion_segura
def _accion_actualizar_paquete(usuario_actual):
    paquete_id = pedir("ID del paquete a actualizar: ", entero_positivo, "El ID")
    pkg = obtener_paquete(usuario_actual, paquete_id)
    print(" ", pkg)
    print("  (Presione Enter para mantener el valor actual)")

    titulo = pedir("Nuevo título: ", texto_no_vacio, "El título", 150, vacio_ok=True)
    descripcion = pedir(
        "Nueva descripción: ", texto_opcional, "La descripción", 1000, vacio_ok=True
    )

    actualizado = actualizar_paquete(
        usuario_actual,
        paquete_id,
        titulo=titulo,
        descripcion=descripcion if descripcion != "" else None,
    )
    print(f"  Paquete actualizado: {actualizado}")


@operacion_segura
def _accion_programar_salida(usuario_actual):
    paquete_id = pedir("ID del paquete: ", entero_positivo, "El ID del paquete")
    pkg = obtener_paquete(usuario_actual, paquete_id)
    print(f"  Paquete seleccionado: {pkg.titulo}")
    print(f"  Costo base sugerido (suma de destinos): ${pkg.calcular_costo_base_total():,.2f}")

    fecha_inicio = pedir(
        "Fecha de inicio (YYYY-MM-DD): ",
        SalidaPaquete.validar_fecha,
        "La fecha de inicio",
    )
    fecha_fin = pedir(
        "Fecha de término (YYYY-MM-DD): ",
        SalidaPaquete.validar_fecha,
        "La fecha de término",
    )
    precio = pedir(
        "Precio por persona para esta salida: ", SalidaPaquete.validar_precio
    )
    cupos = pedir("Cupos totales disponibles: ", entero_positivo, "Los cupos")

    salida = programar_salida(
        usuario_actual, paquete_id, fecha_inicio, fecha_fin, precio, cupos
    )
    print(f"  Salida publicada correctamente: {salida}")


@operacion_segura
def _accion_listar_salidas_disponibles(usuario_actual):
    salidas = listar_salidas_disponibles(usuario_actual)
    if not salidas:
        print("  No hay salidas abiertas con cupos disponibles en este momento.")
        return
    for s in salidas:
        print(" ", s)


@operacion_segura
def _accion_cancelar_salida(usuario_actual):
    salida_id = pedir("ID de la salida a cancelar: ", entero_positivo, "El ID de la salida")
    salida = cancelar_salida(usuario_actual, salida_id)
    print(f"  Salida cancelada: {salida}")


@operacion_segura
def _accion_retirar_paquete(usuario_actual):
    paquete_id = pedir("ID del paquete a desactivar o eliminar: ", entero_positivo, "El ID")
    resultado, pkg = retirar_o_eliminar_paquete(usuario_actual, paquete_id)
    if resultado == "desactivado":
        print(
            f"  Paquete '{pkg.titulo}' desactivado (conserva salidas/reservas históricas)."
        )
    else:
        print(f"  Paquete '{pkg.titulo}' eliminado definitivamente de la base de datos.")


def menu_paquetes(usuario_actual):
    acciones = {
        1: lambda: _accion_crear_paquete(usuario_actual),
        2: lambda: _accion_listar_paquetes(usuario_actual, True),
        3: lambda: _accion_listar_paquetes(usuario_actual, False),
        4: lambda: _accion_detalle_paquete(usuario_actual),
        5: lambda: _accion_actualizar_paquete(usuario_actual),
        6: lambda: _accion_programar_salida(usuario_actual),
        7: lambda: _accion_listar_salidas_disponibles(usuario_actual),
        8: lambda: _accion_cancelar_salida(usuario_actual),
        9: lambda: _accion_retirar_paquete(usuario_actual),
    }
    while True:
        mostrar_menu()
        opcion = solicitar_opcion(9)
        if opcion == 0:
            return
        acciones[opcion]()