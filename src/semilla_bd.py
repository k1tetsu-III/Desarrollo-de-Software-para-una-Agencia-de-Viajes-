from dominio.destino import Destino
from dominio.paquete import PaqueteTuristico, ParadaItinerario, SalidaPaquete
from dominio.usuario import Usuario
from persistencia.conexion import obtener_motor
from persistencia.crear_bd import crear_tablas
from persistencia.destino_dao import DestinoDAO
from persistencia.paquete_dao import PaqueteDAO
from persistencia.usuario_dao import UsuarioDAO


def cargar_datos_semilla():
    print(f"--- Carga de Datos Semilla ({obtener_motor().upper()}) ---")
    crear_tablas()

    # 1. Usuarios iniciales (Administrador y Cliente)
    usuarios_demo = [
        ("Administrador Viajes", "admin@viajesaventura.cl", "Admin123!", "admin"),
        ("Ana Pérez", "ana@viajesaventura.cl", "Cliente123!", "cliente"),
    ]
    for nombre, correo, clave, rol in usuarios_demo:
        if UsuarioDAO.buscar_por_email(correo) is None:
            usuario = Usuario(
                full_name=nombre,
                email=correo,
                password_hash=Usuario.encriptar_clave(clave),
                role=rol,
            )
            UsuarioDAO.insertar(usuario)
            print(f"  Usuario creado: {usuario}")
        else:
            print(f"  Usuario ya existe: {correo}")

    # 2. Destinos turísticos base
    destinos_ejemplo = [
        {
            "nombre": "Santiago",
            "pais": "Chile",
            "costo_base": "120.00",
            "descripcion": "Capital cosmopolita rodeada por la Cordillera de los Andes.",
            "actividades": "City tour histórico, Cerro San Cristóbal, viñedos del Valle del Maipo",
        },
        {
            "nombre": "Buenos Aires",
            "pais": "Argentina",
            "costo_base": "280.00",
            "descripcion": "Capital cultural y gastronómica del Río de la Plata.",
            "actividades": "Show de tango, Caminito en La Boca, recorrido por Palermo y Recoleta",
        },
        {
            "nombre": "Mendoza",
            "pais": "Argentina",
            "costo_base": "210.00",
            "descripcion": "Tierra del sol y del buen vino al pie del Aconcagua.",
            "actividades": "Ruta del vino en Luján de Cuyo, excursión de alta montaña",
        },
    ]

    destinos_guardados: dict[str, Destino] = {}
    for datos in destinos_ejemplo:
        existente = DestinoDAO.buscar_por_nombre_y_pais(datos["nombre"], datos["pais"])
        if existente is None:
            destino = Destino(**datos)
            existente = DestinoDAO.insertar(destino)
            print(f"  Destino creado: {existente}")
        else:
            print(f"  Destino ya existe: {existente}")
        destinos_guardados[datos["nombre"]] = existente

    # 3. Paquete turístico y salida de prueba (Ruta Andina con 3 cupos)
    titulo_paquete = "Ruta Andina"
    paquetes_actuales = PaqueteDAO.listar_paquetes(solo_activos=False)
    if not any(p.titulo == titulo_paquete for p in paquetes_actuales):
        paquete = PaqueteTuristico(
            titulo=titulo_paquete,
            descripcion="Travesía cordillerana conectando Chile y Argentina.",
            activo=True,
        )
        paquete.agregar_parada(
            ParadaItinerario(
                destino_id=destinos_guardados["Santiago"].id,
                orden=1,
                notas="Recepción y tour panorámico",
            )
        )
        paquete.agregar_parada(
            ParadaItinerario(
                destino_id=destinos_guardados["Mendoza"].id,
                orden=2,
                notas="Cruce por Los Libertadores y ruta del vino",
            )
        )
        paquete.agregar_parada(
            ParadaItinerario(
                destino_id=destinos_guardados["Buenos Aires"].id,
                orden=3,
                notas="Cierre cultural y cena show de tango",
            )
        )
        paquete_creado = PaqueteDAO.insertar_paquete(paquete)
        print(f"  Paquete creado: {paquete_creado}")

        salida = SalidaPaquete(
            paquete_id=paquete_creado.id,
            fecha_inicio="2026-12-10",
            fecha_fin="2026-12-17",
            precio_por_persona="650.00",
            cupos_totales=3,
        )
        salida_creada = PaqueteDAO.insertar_salida(salida)
        print(f"  Salida creada: {salida_creada}")
    else:
        print(f"  Paquete ya existe: {titulo_paquete}")


if __name__ == "__main__":
    cargar_datos_semilla()
    print("Semilla ejecutada con éxito.")