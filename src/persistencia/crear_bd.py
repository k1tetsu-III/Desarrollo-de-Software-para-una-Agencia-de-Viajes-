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
        name VARCHAR(120) NOT NULL,
        country VARCHAR(100) NOT NULL DEFAULT 'Chile',
        description TEXT NOT NULL,
        activities TEXT NOT NULL,
        base_cost DECIMAL(10, 2) NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        UNIQUE KEY uq_destination_name_country (name, country),
        CHECK (base_cost >= 0)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS packages (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(150) NOT NULL,
        description TEXT NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS itinerary_stops (
        id INT AUTO_INCREMENT PRIMARY KEY,
        package_id INT NOT NULL,
        destination_id INT NOT NULL,
        visit_order INT NOT NULL,
        notes VARCHAR(255) NOT NULL DEFAULT '',
        UNIQUE KEY uq_package_order (package_id, visit_order),
        CONSTRAINT fk_stops_package
            FOREIGN KEY (package_id) REFERENCES packages(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_stops_destination
            FOREIGN KEY (destination_id) REFERENCES destinations(id)
            ON DELETE RESTRICT,
        CHECK (visit_order > 0)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS package_departures (
        id INT AUTO_INCREMENT PRIMARY KEY,
        package_id INT NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        unit_price DECIMAL(10, 2) NOT NULL,
        total_slots INT NOT NULL,
        available_slots INT NOT NULL,
        status ENUM('abierta', 'cerrada', 'cancelada') NOT NULL DEFAULT 'abierta',
        CONSTRAINT fk_departures_package
            FOREIGN KEY (package_id) REFERENCES packages(id)
            ON DELETE CASCADE,
        CHECK (end_date >= start_date),
        CHECK (unit_price >= 0),
        CHECK (total_slots > 0),
        CHECK (available_slots >= 0 AND available_slots <= total_slots)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS bookings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        departure_id INT NOT NULL,
        booking_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        frozen_unit_price DECIMAL(10, 2) NOT NULL,
        total_price DECIMAL(10, 2) NOT NULL,
        status ENUM('pendiente', 'confirmada', 'cancelada') NOT NULL DEFAULT 'confirmada',
        CONSTRAINT fk_bookings_user
            FOREIGN KEY (user_id) REFERENCES users(id)
            ON DELETE RESTRICT,
        CONSTRAINT fk_bookings_departure
            FOREIGN KEY (departure_id) REFERENCES package_departures(id)
            ON DELETE RESTRICT,
        CHECK (frozen_unit_price >= 0),
        CHECK (total_price >= 0)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS passengers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        booking_id INT NOT NULL,
        document_id VARCHAR(30) NOT NULL,
        full_name VARCHAR(120) NOT NULL,
        birth_date DATE NULL,
        phone VARCHAR(30) NOT NULL DEFAULT '',
        CONSTRAINT fk_passengers_booking
            FOREIGN KEY (booking_id) REFERENCES bookings(id)
            ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS stage_progress (
        id INT AUTO_INCREMENT PRIMARY KEY,
        passenger_id INT NOT NULL,
        itinerary_stop_id INT NOT NULL,
        stage_status ENUM('pendiente', 'en_curso', 'completada') NOT NULL DEFAULT 'pendiente',
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        notes VARCHAR(255) NOT NULL DEFAULT '',
        UNIQUE KEY uq_passenger_stop (passenger_id, itinerary_stop_id),
        CONSTRAINT fk_progress_passenger
            FOREIGN KEY (passenger_id) REFERENCES passengers(id)
            ON DELETE CASCADE,
        CONSTRAINT fk_progress_stop
            FOREIGN KEY (itinerary_stop_id) REFERENCES itinerary_stops(id)
            ON DELETE RESTRICT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
)


def crear_tablas():
    obtener_motor()
    with conexion_segura() as conexion:
        cursor = conexion.cursor()
        try:
            for sentencia in _TABLAS_MYSQL:
                cursor.execute(sentencia)
        finally:
            cursor.close()


if __name__ == "__main__":
    crear_tablas()
    print("Tablas de Viajes Aventura (Modelo Físico v2) creadas correctamente en MySQL.")