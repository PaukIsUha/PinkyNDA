import functools
from contextlib import contextmanager
from typing import Callable, TypeVar, ParamSpec

import sqlalchemy as sa

from .database import SessionLocal
from .models import *
from tasks import celery_app
from log_handle import log

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


# -------- REDIS FLUSH -----------------------------------------------

@celery_app.task
def flush_logs(batch_size: int = 1000) -> int:
    """Pop events from Redis and bulk-insert into Postgres via SQLAlchemy.

    Args:
        batch_size: сколько записей брать за один проход Lua-скрипта.
    Returns:
        Итоговое число вставленных строк.
    """

    total_flushed = 0

    # Lua-скрипт атомарно вытаскивает up-to N элементов списка
    lua_script = (
        "local n=tonumber(ARGV[1]);"
        "local res={};"
        "for i=1,n do "
        "  local v=redis.call('lpop', KEYS[1]);"  # FIFO pop
        "  if not v then return res end;"
        "  table.insert(res, v);"
        "end;"
        "return res;"
    )

    while True:
        # 1. Берём пачку json-строк из Redis
        raw_records = redis_conn.eval(lua_script, 1, BUFFER_KEY, batch_size)
        if not raw_records:
            break  # Всё кончилось

        # 2. Преобразуем в ready-to-insert dicts
        rows = []
        for raw in raw_records:
            try:
                doc = json.loads(raw)
                if doc.get("user_id") is None:
                    continue  # пропуск анонимов / системных событий
                rows.append(
                    {
                        "user_id": int(doc["user_id"]),
                        "action": doc,  # хранится как JSONB
                        "ts": datetime.fromisoformat(doc["iso_ts"]),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[WARN] corrupt log entry dropped: {exc}: {raw}")

        if not rows:
            continue

        # 3. Одним батчем пишем через SQLAlchemy Core (быстрее ORM add_all)
        with SessionLocal() as session:
            session.execute(insert(SpyLog), rows)
            session.commit()
            total_flushed += len(rows)

    return total_flushed


# -------- QUERIES ---------------------------------------------------

@db_update
def new_user(session, id: int, name: str):
    session.add(UserHub(id=id, name=name))
    log.info(f"INSERT POSTGRESQL UserHub --- id: {id}, name: {name}")


@db_update
def user_reg(session, id: int):
    user: UserHub | None = session.get(UserHub, id)
    if user is None:
        raise ValueError(f"UserHub(id={id}) not found")

    user.is_reg = True
    log.info(f"UPDATE POSTGRESQL UserHub --- id: {id}, is_reg={True}")
