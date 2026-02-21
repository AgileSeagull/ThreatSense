from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from engine.models.base import Base


class Machine(Base):
    __tablename__ = "machines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    machine_id: Mapped[str] = mapped_column(String(256), unique=True, index=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Machine(machine_id={self.machine_id!r})>"
