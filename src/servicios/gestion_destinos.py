from dominio.destino import Destino
from persistencia.destino_dao import DestinoDAO
from servicios.permisos import exigir_admin, exigir_sesion


def registrar_destino(
    sesion: dict | None,
    nombre: str,
    pais: str,
    costo_base,
    descripcion: str = "",
    actividades: str = "",
) -> Destino:
    exigir_admin(sesion)
    destino = Destino(
        nombre=nombre,
        pais=pais,
        costo_base=costo_base,
        descripcion=descripcion,
        actividades=actividades,
        activo=True,
    )
    destino.validar()

    if DestinoDAO.buscar_por_nombre_y_pais(destino.nombre, destino.pais) is not None:
        raise ValueError(
            f"Ya existe el destino '{destino.nombre}' en '{destino.pais}'."
        )

    return DestinoDAO.insertar(destino)


def listar_destinos(sesion: dict | None, solo_activos: bool = True) -> list[Destino]:
    exigir_sesion(sesion)
    return DestinoDAO.listar(solo_activos=solo_activos)


def obtener_destino(sesion: dict | None, destino_id: int) -> Destino:
    exigir_sesion(sesion)
    destino = DestinoDAO.buscar_por_id(destino_id)
    if destino is None:
        raise ValueError("Destino no encontrado.")
    return destino


def actualizar_destino(
    sesion: dict | None,
    destino_id: int,
    nombre: str | None = None,
    pais: str | None = None,
    costo_base=None,
    descripcion: str | None = None,
    actividades: str | None = None,
) -> Destino:
    exigir_admin(sesion)
    destino = DestinoDAO.buscar_por_id(destino_id)
    if destino is None:
        raise ValueError("Destino no encontrado.")

    if nombre is not None:
        destino.nombre = nombre
    if pais is not None:
        destino.pais = pais
    if costo_base is not None:
        destino.costo_base = costo_base
    if descripcion is not None:
        destino.descripcion = descripcion
    if actividades is not None:
        destino.actividades = actividades

    destino.validar()

    duplicado = DestinoDAO.buscar_por_nombre_y_pais(destino.nombre, destino.pais)
    if duplicado is not None and duplicado.id != destino.id:
        raise ValueError(
            f"Ya existe otro destino llamado '{destino.nombre}' en '{destino.pais}'."
        )

    DestinoDAO.actualizar(destino)
    return destino


def retirar_o_eliminar_destino(
    sesion: dict | None, destino_id: int
) -> tuple[str, Destino]:
    """
    Aplica la regla del BPMN 1:
    - Si el destino participa en algún paquete: aplica retiro lógico (activo = False).
    - Si no participa en ningún paquete: elimina el registro físicamente de la BD.
    """
    exigir_admin(sesion)
    destino = DestinoDAO.buscar_por_id(destino_id)
    if destino is None:
        raise ValueError("Destino no encontrado.")

    paquetes_asociados = DestinoDAO.contar_paquetes_asociados(destino_id)
    if paquetes_asociados > 0:
        if not destino.activo:
            raise ValueError(
                "El destino ya está retirado y se conserva por participar en paquetes."
            )
        destino.retirar()
        DestinoDAO.retirar(destino.id)
        return "retirado", destino

    DestinoDAO.eliminar_fisico(destino.id)
    return "eliminado", destino