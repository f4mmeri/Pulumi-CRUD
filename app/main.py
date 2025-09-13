from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3

from app.database import init_db, EstudianteDB
app = FastAPI(title="CRUD Estudiantes", version="1.0.0")

class EstudianteBase(BaseModel):
    nombre: str
    apellido: str
    email: str
    edad: int

class EstudianteCreate(EstudianteBase):
    pass


class EstudianteUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[str] = None
    edad: Optional[int] = None

class Estudiante(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    edad: int

    class Config:
        from_attributes = True


init_db()

@app.post("/estudiantes/", response_model=Estudiante)
async def crear_estudiante(estudiante: EstudianteCreate):
    """Crear un nuevo estudiante"""
    try:
        resultado = EstudianteDB.crear_estudiante(
            nombre=estudiante.nombre,
            apellido=estudiante.apellido,
            email=estudiante.email,
            edad=estudiante.edad
        )
        return resultado
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

@app.get("/estudiantes/", response_model=List[Estudiante])
async def obtener_estudiantes():
    """Obtener todos los estudiantes"""
    return EstudianteDB.obtener_todos_estudiantes()

@app.put("/estudiantes/{estudiante_id}", response_model=Estudiante)
async def actualizar_estudiante(estudiante_id: int, estudiante: EstudianteUpdate):
    """Actualizar un estudiante existente"""
    try:
        resultado = EstudianteDB.actualizar_estudiante(
            estudiante_id=estudiante_id,
            nombre=estudiante.nombre,
            apellido=estudiante.apellido,
            email=estudiante.email,
            edad=estudiante.edad
        )

        if resultado is None:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")

        return resultado
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

@app.delete("/estudiantes/{estudiante_id}")
async def eliminar_estudiante(estudiante_id: int):
    """Eliminar un estudiante"""
    eliminado = EstudianteDB.eliminar_estudiante(estudiante_id)
    if not eliminado:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return {"message": "Estudiante eliminado exitosamente"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)