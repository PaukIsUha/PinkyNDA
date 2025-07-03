import base64
import logging
import os
from io import BytesIO
from typing import Dict, Any, Optional

import aiohttp
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    CallbackQuery, Message,
)
from configs import BOT_CONFIGS, SPEAKER_CONFIGS
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

users_whitelist = ["FxJGlopNd"]
WHITELIST = {u.strip().lower() for u in users_whitelist if u}

TOPICS = [
    "Разбор переписки",
    "Астрология",
    "Косметика и уход",
    "Здоровье и спорт",
    "Стиль",
    "Учёба",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

bot = Bot(
    BOT_CONFIGS.token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)  # ← новинка 3.7
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)


# ---------- helpers ---------------------------------------------------------
async def post_json(path: str, payload: Dict[str, Any]):
    async with aiohttp.ClientSession() as s:
        async with s.post(f"{SPEAKER_CONFIGS.url}{path}", json=payload, timeout=60) as r:
            r.raise_for_status()
            return await r.json()


def kb_topics() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=topic, callback_data=f"t:{topic}")]
            for topic in TOPICS
        ]
    )


def kb_confirm() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Да", callback_data="yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="no"),
        ]]
    )


async def photo_to_b64(message: Message) -> Optional[str]:
    if not message.photo:
        return None
    file = await bot.get_file(message.photo[-1].file_id)
    buf = BytesIO()
    await bot.download_file(file.file_path, buf)
    return base64.b64encode(buf.getvalue()).decode()


# ---------- FSM -------------------------------------------------------------
class St(StatesGroup):
    wait_q = State()
    wait_ok = State()


# ---------- handlers --------------------------------------------------------
@dp.message(CommandStart())
async def start(msg: Message):
    if WHITELIST and msg.from_user.username.lower() not in WHITELIST:
        await msg.answer("⛔️ У вас нет доступа к боту.")
        return

    await msg.answer("Привет! Выбери тему вопроса:", reply_markup=kb_topics())


@router.callback_query(F.data.startswith("t:"))
async def choose_topic(cb: CallbackQuery, state):
    topic = cb.data[2:]
    await state.update_data(topic=topic)
    await state.set_state(St.wait_q)
    await cb.message.answer(f"Тема «{topic}». Пришли вопрос (можно с фото).")
    await cb.answer()


@router.message(St.wait_q)
async def got_q(msg: Message, state):
    text = msg.text or msg.caption
    if not text:
        await msg.answer("Нужен текстовый вопрос.")
        return

    data = await state.get_data()
    b64 = await photo_to_b64(msg)

    payload = dict(chosen_topic=data["topic"], query=text, base64_image=b64)
    try:
        v = await post_json("/chat_ai/validation", payload)
    except Exception as e:
        logging.exception("validation")
        await msg.answer("Ошибка сервиса, попробуйте позже.")
        return

    if v["true_topic"] == "Другое":
        await msg.answer("🤔 К сожалению, не знаю, как ответить на этот вопрос.")
        await state.clear()
        return

    await state.update_data(
        query=text, base64=b64,
        true_topic=v["true_topic"], cost=v["cost"]
    )
    await state.set_state(St.wait_ok)

    prefix = "" if v["is_valid"] else f"Похоже, это тема «{v['true_topic']}».\n"
    await msg.answer(
        f"{prefix}Стоимость ответа: <b>{v['cost']}❤️</b>\nПодтверждаешь?",
        reply_markup=kb_confirm()
    )


@router.callback_query(St.wait_ok, F.data == "no")
async def cancel(cb: CallbackQuery, state):
    await cb.message.answer("🚫 Отменено.")
    await state.clear()
    await cb.answer()


@router.callback_query(St.wait_ok, F.data == "yes")
async def proceed(cb: CallbackQuery, state):
    d = await state.get_data()
    await cb.answer("Думаю…")

    payload = dict(
        topic=d["true_topic"], query=d["query"], base64_image=d["base64"]
    )
    try:
        r = await post_json("/chat_ai/general_inference", payload)
    except Exception as e:
        logging.exception("inference")
        await cb.message.answer("Ошибка ИИ. Попробуйте позже.")
        await state.clear()
        return

    await cb.message.answer(r["response_text"])
    await state.clear()


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
