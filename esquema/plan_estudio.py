from pydantic import BaseModel
from typing import Optional, Any

class GenerarPlanSolicitud(BaseModel):
    id_usuario: int
    titulo: str
    descripcion: Optional[str] = "Plan personalizado generado por StudNova IA"
    nivel_objetivo: Optional[str] = "Intermedio"
    duracion: Optional[int] = 7  # Duración en días
    id_asignatura: int
    id_ruta: int