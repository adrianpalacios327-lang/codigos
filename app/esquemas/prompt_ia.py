from pydantic import BaseModel
from typing import Optional

class ChatSolicitud(BaseModel):
    id_usuario: int
    id_plan: Optional[int] = None
    mensaje: str

class GenerarPlanSolicitud(BaseModel):
    id_usuario: int
    id_asignatura: int
    objetivo_estudio: str
    nivel_objetivo: str
    duracion_dias: int