from dominio.destino import Destino
from menu_comun import operacion_segura, pedir, solicitar_opcion
from servicios.gestion_destinos import (
    actualizar_destino,
    listar_destinos,
    obtener_destino,
    registrar_destino,
    retirar_o_eliminar_destino,
)
from utilidades import entero_positivo, texto_no_vacio, texto_opcional

_MANTENER_TEXTO = object()


def _validar_texto_opcional_edicion(valor, campo, maximo=500):
    if valor == "":
        return _MANTENER_TEXTO
    if valor == "!":
        return ""
    return texto_opcional(valor, campo, maximo)


def mostrar_menu():
    print("\n--- GESTIÓN DE DESTINOS (VIAJES AVENTURA) ---")
    print("1. Registrar nuevo destino")
    print("2. Listar destinos activos")
    print("3. Listar todos los destinos (incluye retirados)")
    print("4. Buscar destino por ID")
    print("5. Actualizar destino")
    print("6. Retirar / eliminar destino")
    print("0. Volver")


@operacion_segura
def _accion_registrar(usuario_actual):
    nombre = pedir("Nombre del destino: ", texto_no_vacio, "El nombre", 120)
    pais = (
        pedir(
            "País (Enter = Chile): ",
            texto_no_vacio,
            "El país",
            100,
            vacio_ok=True,
        )
        or "Chile"
    )
    costo = pedir("Costo base (USD/CLP): ", Destino.validar_costo)
    descripcion = pedir(
        "Descripción (opcional): ", texto_opcional, "La descripción", 500
    )
    actividades = pedir(
        "Actividades principales (opcional): ", texto_opcional, "Las actividades", 500
    )

    destino = registrar_destino(
        usuario_actual, nombre, pais, costo, descripcion, actividades
    )
    print(f"  Destino registrado correctamente: {destino}")


@operacion_segura
def _accion_listar(usuario_actual, solo_activos: bool):
    destinos = listar_destinos(usuario_actual, solo_activos=solo_activos)
    if not destinos:
        print("  No hay destinos registrados con ese filtro.")
        return
    for d in destinos:
        print(" ", d)
        if d.actividades:
            print(f"      Actividades: {d.actividades}")


@operacion_segura
def _accion_buscar(usuario_actual):
    destino_id = pedir("ID del destino: ", entero_positivo, "El ID")
    destino = obtener_destino(usuario_actual, destino_id)
    print(" ", destino)
    if destino.descripcion:
        print(f"      Descripción: {destino.descripcion}")
    if destino.actividades:
        print(f"      Actividades: {destino.actividades}")


@operacion_segura
def _accion_actualizar(usuario_actual):
    destino_id = pedir("ID del destino a actualizar: ", entero_positivo, "El ID")
    destino = obtener_destino(usuario_actual, destino_id)
    print(" ", destino)
    print("  (Presione Enter para mantener el valor actual)")

    nombre = pedir(
        "Nuevo nombre: ", texto_no_vacio, "El nombre", 120, vacio_ok=True
    )
    pais = pedir("Nuevo país: ", texto_no_vacio, "El país", 100, vacio_ok=True)
    costo = pedir("Nuevo costo base: ", Destino.validar_costo, vacio_ok=True)
    descripcion = pedir(
        "Nueva descripción (Enter = mantener, ! = borrar): ",
        _validar_texto_opcional_edicion,
        "La descripción",
        500,
    )
    actividades = pedir(
        "Nuevas actividades (Enter = mantener, ! = borrar): ",
        _validar_texto_opcional_edicion,
        "Las actividades",
        500,
    )

    actualizado = actualizar_destino(
        usuario_actual,
        destino_id,
        nombre=nombre,
        pais=pais,
        costo_base=costo,
        descripcion=None if descripcion is _MANTENER_TEXTO else descripcion,
        actividades=None if actividades is _MANTENER_TEXTO else actividades,
    )
    print(f"  Destino actualizado: {actualizado}")


@operacion_segura
def _accion_retirar_o_eliminar(usuario_actual):
    destino_id = pedir("ID del destino a retirar o eliminar: ", entero_positivo, "El ID")
    resultado, destino = retirar_o_eliminar_destino(usuario_actual, destino_id)
    if resultado == "retirado":
        print(
            f"  Destino '{destino.nombre}' retirado (activo = 0) porque participa "
            "en paquetes turísticos (se conserva historial)."
        )
    else:
        print(
            f"  Destino '{destino.nombre}' eliminado definitivamente de la base de datos "
            "(no estaba asociado a ningún paquete)."
        )


def menu_destinos(usuario_actual):
    acciones = {
        1: lambda: _accion_registrar(usuario_actual),
        2: lambda: _accion_listar(usuario_actual, True),
        3: lambda: _accion_listar(usuario_actual, False),
        4: lambda: _accion_buscar(usuario_actual),
        5: lambda: _accion_actualizar(usuario_actual),
        6: lambda: _accion_retirar_o_eliminar(usuario_actual),
    }
    while True:
        mostrar_menu()
        opcion = solicitar_opcion(6)
        if opcion == 0:
            return
        acciones[opcion]()