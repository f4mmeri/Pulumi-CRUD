import sqlite3
import contextlib
from typing import List, Optional, Dict, Any

DATABASE_URL = "estudiantes.db"


def init_db():
    conn = sqlite3.connect(DATABASE_URL)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS estudiantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            edad INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@contextlib.contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


class EstudianteDB:
    @staticmethod
    def crear_estudiante(nombre: str, apellido: str, email: str, edad: int) -> Dict[str, Any]:
        with get_db() as conn:
            cursor = conn.execute(
                "INSERT INTO estudiantes (nombre, apellido, email, edad) VALUES (?, ?, ?, ?)",
                (nombre, apellido, email, edad)
            )
            conn.commit()
            estudiante_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM estudiantes WHERE id = ?", (estudiante_id,)).fetchone()
            return dict(row)

    @staticmethod
    def obtener_todos_estudiantes() -> List[Dict[str, Any]]:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM estudiantes").fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def actualizar_estudiante(estudiante_id: int, **campos) -> Optional[Dict[str, Any]]:
        with get_db() as conn:
            existing = conn.execute("SELECT * FROM estudiantes WHERE id = ?", (estudiante_id,)).fetchone()
            if existing is None:
                return None
            update_fields = []
            values = []

            for campo, valor in campos.items():
                if valor is not None and campo in ['nombre', 'apellido', 'email', 'edad']:
                    update_fields.append(f"{campo} = ?")
                    values.append(valor)

            if not update_fields:
                return dict(existing)

            values.append(estudiante_id)
            query = f"UPDATE estudiantes SET {', '.join(update_fields)} WHERE id = ?"
            conn.execute(query, values)
            conn.commit()
            row = conn.execute("SELECT * FROM estudiantes WHERE id = ?", (estudiante_id,)).fetchone()
            return dict(row)

    @staticmethod
    def eliminar_estudiante(estudiante_id: int) -> bool:
        with get_db() as conn:
            existing = conn.execute("SELECT * FROM estudiantes WHERE id = ?", (estudiante_id,)).fetchone()
            if existing is None:
                return False

            conn.execute("DELETE FROM estudiantes WHERE id = ?", (estudiante_id,))
            conn.commit()
            return True