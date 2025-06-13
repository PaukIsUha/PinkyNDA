import database as db
import os
from typing import Callable, Awaitable, Any, Dict

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from tasks import log_event
from configs import CONFIG_BOT


###############################################################################
# Inline keyboard builders                                                   #
###############################################################################

def kb_start() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💖 Да, расскажи о себе", callback_data="about_me")],
        [InlineKeyboardButton("🤔 Что ты умеешь?", callback_data="what_i_do")],
        [InlineKeyboardButton("💻 Начать пользоваться", callback_data="register")],
    ])


def kb_about_me() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤔 Что ты умеешь?", callback_data="what_i_do")],
        [InlineKeyboardButton("💻 Начать пользоваться", callback_data="register")],
    ])


def kb_what_i_do() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💻 Начать пользоваться", callback_data="register")],
    ])


def kb_register() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Согласен", callback_data="agree")],
    ])


###############################################################################
# Handler functions                                                          #
###############################################################################

@log_event("start")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/start — only once per user."""
    user_data = context.user_data
    if user_data.get("started"):
        return  # Игнорируем повторные /start

    user_data["started"] = True

    await update.message.reply_html(
        "<b>Привет! Я Pinky – твоя digital-подруга 💕 Давай знакомиться?</b>",
        reply_markup=kb_start(),
    )


@log_event("about_me")
async def about_me(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.message:
        await query.edit_message_reply_markup(reply_markup=None)

    await query.message.reply_text(
        "Я твоя новая лучшая подруга! Я умею анализировать твои фото, помогать в переписках, "
        "подбирать стиль и даже советовать, куда сходить сегодня вечером! Регистрируйся и начинаем?",
        reply_markup=kb_about_me(),
    )


@log_event("what_i_do")
async def what_i_do(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.message:
        await query.edit_message_reply_markup(reply_markup=None)

    await query.message.reply_markdown_v2(
        (
            "Я могу помочь тебе найти идеальный тональный крем, разобрать переписку с парнем, выбрать платье "
            "на свидание или даже рассказать, какие вечеринки сегодня самые хайповые\. Начинай скорее\!"
        ),
        reply_markup=kb_what_i_do(),
    )


@log_event("register")
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.message:
        await query.edit_message_reply_markup(reply_markup=None)

    await query.message.reply_text(
        (
            "🎉 Для начала необходимо подтвердить свое согласие, нажимая кнопку «Завершить»:\n"
            "– Политикой конфиденциальности\n– Пользовательским соглашением"
        ),
        reply_markup=kb_register(),
    )


@log_event("agree")
async def agree(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.message:
        await query.edit_message_reply_markup(reply_markup=None)

    await query.message.reply_text(
        "Привет, выбери чем бы ты хотела заняться сегодня ?\n\nВыбери вариант внизу или просто напиши в чат.",
    )

###############################################################################
# Fallback echo for free-text                                                #
###############################################################################


@log_event("free_text")
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    await update.message.reply_text(
        f"Я пока не умею отвечать на \"{text}\", но уже учусь 🤖",
    )

###############################################################################
# Application builder                                                        #
###############################################################################


def build_app() -> Application:
    app = ApplicationBuilder().token(CONFIG_BOT.token).build()

    # Commands
    app.add_handler(CommandHandler("start", start))

    # Callback buttons
    app.add_handler(CallbackQueryHandler(about_me, pattern="^about_me$"))
    app.add_handler(CallbackQueryHandler(what_i_do, pattern="^what_i_do$"))
    app.add_handler(CallbackQueryHandler(register, pattern="^register$"))
    app.add_handler(CallbackQueryHandler(agree, pattern="^agree$"))

    # Fallback echo for any text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    return app


###############################################################################
# Entrypoint                                                                 #
###############################################################################

if __name__ == "__main__":
    application = build_app()
    application.run_polling(allowed_updates=["message", "callback_query"])
