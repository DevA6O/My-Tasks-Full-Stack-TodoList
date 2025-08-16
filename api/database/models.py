import uuid
from sqlalchemy import Integer, ForeignKey, desc
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connection import Base


def current_timestamp() -> int:
    from datetime import datetime
    return round(datetime.now().timestamp())


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, unique=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str]
    created_at: Mapped[int] = mapped_column(Integer, default=current_timestamp)

    auth: Mapped[list["Auth"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    todos: Mapped[list["Todo"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by=lambda: (Todo.completed.asc(), desc(Todo.edited_at), desc(Todo.created_at))
    )

class Auth(Base):
    __tablename__ = "auth"

    jti_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, unique=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    ip_address: Mapped[str]
    user_agent: Mapped[str]
    device: Mapped[str]
    browser: Mapped[str]
    os: Mapped[str]

    is_refresh_token: Mapped[bool]
    revoked: Mapped[bool] = mapped_column(default=False)
    expires_at: Mapped[int]

    created_at: Mapped[int] = mapped_column(Integer, default=current_timestamp)
    updated_at: Mapped[int] = mapped_column(Integer, default=current_timestamp, onupdate=current_timestamp)

    user: Mapped["User"] = relationship(back_populates="auth")



class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, unique=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    completed: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[int] = mapped_column(Integer, default=current_timestamp)
    edited_at: Mapped[int] = mapped_column(Integer, default=current_timestamp, onupdate=current_timestamp)

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="todos")