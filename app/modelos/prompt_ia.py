from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.modelos.plan_estudio import PlanDeEstudio

class PromptIA(SQLModel, table=True):
    __tablename__ = "prompt_ia"

    id_prompt: Optional[int] = Field(default=None, primary_key=True)
    id_usuario: Optional[int] = Field(default=None, foreign_key="usuario.id_usuario")
    id_plan: Optional[int] = Field(default=None, foreign_key="plan_de_estudio.id_plan")
    prompt_usuario: Optional[str] = None
    prompt_sistema: Optional[str] = None
    modelo_ia: Optional[str] = Field(default="gemini-2.5-flash", max_length=100)
    embedding: Optional[str] = Field(default=None)
    fecha_generacion: datetime = Field(default_factory=datetime.now)
    estado: Optional[str] = Field(default="completado", max_length=50)

    plan: Optional["PlanDeEstudio"] = Relationship(back_populates="prompts")