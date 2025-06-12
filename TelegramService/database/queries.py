import functools
from contextlib import contextmanager
from typing import Callable, TypeVar, ParamSpec

import sqlalchemy as sa

from .database import SessionLocal

_P = ParamSpec("_P")
_R = TypeVar("_R")


# -----------------------------
# Низкоуровневые контекст-менеджеры
# -----------------------------
@contextmanager
def _get_session(isolation: str):
    """Создаёт сессию с заданным уровнем изоляции."""
    session = SessionLocal()
    try:
        session.connection(
            execution_options={"isolation_level": isolation}
        )  # транзакция откроется при первом запросе
        yield session
    finally:
        session.close()


# -----------------------------
# Декораторы
# -----------------------------
def db_query(func: Callable[_P, _R]) -> Callable[_P, _R]:
    """READ COMMITTED, rollback on error, без commit."""

    @functools.wraps(func)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:  # type: ignore[name-defined]
        with _get_session("READ COMMITTED") as session:
            try:
                result = func(session, *args, **kwargs)
                return result
            except Exception:
                session.rollback()
                raise

    return wrapper


def db_update(func: Callable[_P, _R]) -> Callable[_P, _R]:
    """
    SERIALIZABLE, commit по окончании.
    Также авто-заполняет server-default поля, если объект ещё не в БД
    (например, `ts = func.now()`).
    """

    @functools.wraps(func)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:  # type: ignore[name-defined]
        with _get_session("SERIALIZABLE") as session:
            try:
                result = func(session, *args, **kwargs)

                # --- auto defaults ---
                # Прогоняем before_flush, чтобы серверные default-ы проставились
                for obj in session.new:
                    session.flush([obj])

                session.commit()
                return result
            except Exception:
                session.rollback()
                raise

    return wrapper


### ---------------------------------------------------

@db_update
def add_user(session, name: str):
    session.add(UserHub(name=name, is_reg=True))
