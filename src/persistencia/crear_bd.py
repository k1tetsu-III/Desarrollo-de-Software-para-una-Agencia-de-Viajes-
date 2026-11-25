from persistencia.conexion import conexion_segura, obtener_motor


_TABLAS_MYSQL = (
    """
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        full_name VARCHAR(120) NOT NULL,
        email VARCHAR(150) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM('admin', 'cliente') NOT NULL DEFAULT 'cliente',
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS destinations (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(120) NOT NULL UNIQUE,
        description TEXT NOT NULL,
        activities TEXT NOT NULL,
        base_cost DECIMAL(10, 2) NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        CHECK (base_cost >= 0)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS packages (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(150) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        total_cost DECIMAL(10, 2) NOT NULL,
        available_slots INT NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        CHECK (end_date >= start_date),
        CHECK (total_cost >= 0),
        CHECK (available_slots >= 0)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS package_destinations (
        package_id INT NOT NULL,
        destination_id INT NOT NULL,
        PRIMARY KEY (package_id, destination_id),
        CONSTRAINT fk_pkg_dest_package
            FOREIGN KEY (package_id) REFERENCES packages(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_pkg_dest_destination
            FOREIGN KEY (destination_id) REFERENCES destinations(id)
            ON DELETE RESTRICT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS bookings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        package_id INT NOT NULL,
        booking_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        num_people INT NOT NULL,
        total_price DECIMAL(10, 2) NOT NULL,
        status ENUM('pendiente', 'confirmada', 'cancelada') NOT NULL DEFAULT 'confirmada',
        CONSTRAINT fk_bookings_user
            FOREIGN KEY (user_id) REFERENCES users(id)
            ON DELETE RESTRICT,
        CONSTRAINT fk_bookings_package
            FOREIGN KEY (package_id) REFERENCES packages(id)
            ON DELETE RESTRICT,
        CHECK (num_people > 0),
        CHECK (total_price >= 0)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
)


def crear_tablas():
    motor = obtener_motor()
    if motor != "mysql":
        raise ValueError(
            f"Motor no soportado: '{motor}'. Este proyecto requiere MySQL por defecto."
        )

    with conexion_segura() as conexion:
        cursor = conexion.cursor()
        try:
            for sentencia in _TABLAS_MYSQL:
                cursor.execute(sentencia)
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            cursor.close()


if __name__ == "__main__":
    crear_tablas()
    print("Tablas de Viajes Aventura creadas/verificadas correctamente en MySQL.")