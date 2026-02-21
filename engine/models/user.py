from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from engine.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    machine_id: Mapped[str] = mapped_column(String(256), index=True, nullable=False)

    def __repr__(self) -> str:
        return f"<User(username={self.username!r}, machine_id={self.machine_id!r})>"
