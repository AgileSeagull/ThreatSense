from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from engine.models.base import Base


class ThreatHash(Base):
    __tablename__ = "threat_hashes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    command_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
