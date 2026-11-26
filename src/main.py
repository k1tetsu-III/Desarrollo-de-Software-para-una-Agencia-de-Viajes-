import logging

from menu_destinos import menu_destinos
from menu_paquetes import menu_paquetes
from menu_reservas import menu_reservas_admin, menu_reservas_cliente
from menu_usuario import solicitar_login, solicitar_registro_cliente
from persistencia.conexion import ERRORES_BD, ErrorConfiguracion, obtener_motor
from persistencia.crear_bd import crear_tablas
from servicios.gestion_destinos import listar_destinos
from servicios.gestion_paquetes import listar_paquetes, listar_salidas_disponibles


def preparar_base_de_datos() -> bool:
    try:
        crear_tablas()
        return True
    except ErrorConfiguracion as error:
        print(f"Error de configuración: {error}. Revise el archivo .env.")
    except ERRORES_BD:
        logging.getLogger("viajes_aventura").exception("No se pudo preparar la BD")
        print("No fue posible conectar con la base de datos. Revise el archivo .env.")
    return False


def solicitar_opcion(max_opcion: int) -> int | None:
    try:
        opcion = int(input(f"Seleccione una opción (0-{max_opcion}): "))
        if 0 <= opcion <= max_opcion:
            return opcion
    except ValueError:
        pass
    print("Opción inválida.")
    return None


def flujo_admin(usuario_actual: dict) -> bool:
    while True:
        print(f"\n=== VIAJES AVENTURA [ADMIN] ({obtener_motor().upper()}) ===")
        print("1. Gestión de Destinos (CRUD)")
        print("2. Gestión de Paquetes Turísticos y Salidas (CRUD)")
        print("3. Gestión de Reservas, Pasajeros y Seguimiento (CRUD)")
        print("9. Cerrar sesión")
        print("0. Salir del programa")

        opcion = input("Opción: ").strip()
        if opcion == "0":
            return True
        if opcion == "9":
            return False
        if opcion == "1":
            menu_destinos(usuario_actual)
        elif opcion == "2":
            menu_paquetes(usuario_actual)
        elif opcion == "3":
            menu_reservas_admin(usuario_actual)
        else:
            print("Opción no válida.")


def flujo_cliente(usuario_actual: dict) -> bool:
    while True:
        print(f"\n=== VIAJES AVENTURA [CLIENTE] ({obtener_motor().upper()}) ===")
        print("1. Ver destinos disponibles")
        print("2. Ver paquetes turísticos y salidas abiertas")
        print("3. Mis reservas, pasajeros y avances de viaje")
        print("9. Cerrar sesión")
        print("0. Salir del programa")

        opcion = input("Opción: ").strip()
        if opcion == "0":
            return True
        if opcion == "9":
            return False
        if opcion == "1":
            destinos = listar_destinos(usuario_actual, solo_activos=True)
            if not destinos:
                print("  No hay destinos disponibles.")
            for d in destinos:
                print(" ", d)
        elif opcion == "2":
            paquetes = listar_paquetes(usuario_actual, solo_activos=True)
            if not paquetes:
                print("  No hay paquetes activos disponibles.")
            for pkg in paquetes:
                print("\n ", pkg)
                for parada in pkg.obtener_itinerario():
                    print("  ", parada)
            salidas = listar_salidas_disponibles(usuario_actual)
            if salidas:
                print("\n  Salidas abiertas con cupos:")
                for s in salidas:
                    print("   ->", s)
        elif opcion == "3":
            menu_reservas_cliente(usuario_actual)
        else:
            print("Opción no válida.")


def main():
    logging.basicConfig(
        filename="viajes_aventura.log",
        level=logging.ERROR,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if not preparar_base_de_datos():
        return

    while True:
        print(f"\n--- BIENVENIDO A VIAJES AVENTURA (Motor: {obtener_motor().upper()}) ---")
        print("1. Iniciar sesión")
        print("2. Registrarse como cliente")
        print("0. Salir")

        opcion = solicitar_opcion(2)
        if opcion == 0:
            print("Programa finalizado.")
            return
        if opcion == 2:
            solicitar_registro_cliente()
            continue
        if opcion != 1:
            continue

        usuario_actual = solicitar_login()
        if usuario_actual is None:
            continue

        print(f"\nBienvenido/a, {usuario_actual['full_name']} (Rol: {usuario_actual['role']})")
        if usuario_actual["role"] == "admin":
            salir = flujo_admin(usuario_actual)
        else:
            salir = flujo_cliente(usuario_actual)

        if salir:
            print("Programa finalizado.")
            return
        print("Sesión cerrada.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma interrumpido. Hasta luego.")