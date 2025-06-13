from configs import CONFIG_REDIS
import redis.asyncio as redis
from celery import Celery
from typing import Callable, Awaitable, Any, Dict
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timezone
import json


CELERY_BROKER = CONFIG_REDIS()
CELERY_BACKEND = CONFIG_REDIS()


redis_conn = redis.from_url(CONFIG_REDIS(), encoding="utf-8", decode_responses=True)

celery_app = Celery(
    "logger",
    broker=CELERY_BROKER,
    backend=CELERY_BACKEND,
)


def log_event(event_name: str) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """Wraps a handler & pushes event metadata to Redis for later flush."""

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any):
            # Collect minimal info; enrich as needed
            payload: Dict[str, Any] = {
                "event": event_name,
                "user_id": update.effective_user.id if update.effective_user else None,
                "chat_id": update.effective_chat.id if update.effective_chat else None,
                "iso_ts": datetime.now(timezone.utc).isoformat(),
                # What exactly triggered (text or callback)
                "message": update.effective_message.text if update.effective_message else None,
                "callback_data": update.callback_query.data if update.callback_query else None,
            }
            try:
                await redis_conn.rpush(CONFIG_REDIS.buffer_key, json.dumps(payload))
            except Exception as exc:  # noqa: BLE001
                # In prod: log exception via sentry / stderr
                print(f"[WARN] failed to push log to redis: {exc}")
            # Call real handler
            return await func(update, context, *args, **kwargs)

        return wrapper

    return decorator
