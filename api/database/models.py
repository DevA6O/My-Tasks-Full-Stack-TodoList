import uuid
from datetime import datetime
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column
from database.connection import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, unique=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str]
    created_at: Mapped[int] = mapped_column(Integer, default=round(datetime.now().timestamp()))