import os
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ChatMemberStatus
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

TOKEN = os.environ["BOT_TOKEN"]

GRUPOS = {
    "@mymundostreaming": "MUNDO STREAMING PERÚ 🇵🇪",
    "@mundocibertetico": "UNIVERSO CIBERNÉTICO PERÚ 🇵🇪",
    "@metaversostreaminggo": "METAVERSO STREAMING PERÚ 🇵🇪",
    "@MundoCachineroStreaming": "MUNDO CACHINERO STREAMING 🌐",
}

ESTADOS_VALIDOS = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.OWNER,
}


async def obtener_grupos_faltantes(bot, user_id):
    faltantes = []

    for grupo, nombre in GRUPOS.items():
        try:
            miembro = await bot.get_chat_member(
                chat_id=grupo,
                user_id=user_id,
            )

            if miembro.status not in ESTADOS_VALIDOS:
                faltantes.append((grupo, nombre))

        except TelegramError:
            faltantes.append((grupo, nombre))

    return faltantes


def crear_botones(faltantes):
    botones = []

    for grupo, nombre in faltantes:
        enlace = f"https://t.me/{grupo.replace('@', '')}"

        botones.append(
            [
                InlineKeyboardButton(
                    text=f"👉 UNIRME A {nombre}",
                    url=enlace,
                )
            ]
        )

    botones.append(
        [
            InlineKeyboardButton(
                text="✅ YA ME UNÍ — VERIFICAR",
                callback_data="verificar",
            )
        ]
    )

    return InlineKeyboardMarkup(botones)


async def verificar_usuario(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    mensaje = update.effective_message
    usuario = update.effective_user
    chat = update.effective_chat

    if not mensaje or not usuario or not chat:
        return

    if usuario.is_bot:
        return

    try:
        miembro_actual = await context.bot.get_chat_member(
            chat_id=chat.id,
            user_id=usuario.id,
        )

        if miembro_actual.status in {
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        }:
            return

    except TelegramError:
        return

    faltantes = await obtener_grupos_faltantes(
        context.bot,
        usuario.id,
    )

    if not faltantes:
        return

    try:
        await mensaje.delete()
    except TelegramError:
        pass

    texto = (
        f"🚫 <b>{usuario.first_name}, aún no puedes publicar.</b>\n\n"
        "Para escribir o publicar debes pertenecer a "
        "<b>todos los grupos de nuestra comunidad</b>.\n\n"
        "👇 Únete a los grupos que te faltan y luego pulsa "
        "<b>YA ME UNÍ — VERIFICAR</b>."
    )

    await context.bot.send_message(
        chat_id=chat.id,
        text=texto,
        parse_mode="HTML",
        reply_markup=crear_botones(faltantes),
    )


async def verificar_boton(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    faltantes = await obtener_grupos_faltantes(
        context.bot,
        query.from_user.id,
    )

    if faltantes:
        await query.answer(
            "❌ Todavía te falta unirte a uno o más grupos.",
            show_alert=True,
        )
        return

    await query.edit_message_text(
        "✅ <b>VERIFICACIÓN COMPLETADA</b>\n\n"
        "Ya perteneces a todos los grupos de nuestra comunidad.\n\n"
        "🎉 Ahora puedes escribir y publicar.",
        parse_mode="HTML",
    )


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "🤖 Bot de control de membresía activo.\n\n"
        "Verifico el acceso a los grupos de la comunidad."
    )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            verificar_boton,
            pattern="^verificar$",
        )
    )

    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            verificar_usuario,
        )
    )

    print("Bot iniciado correctamente")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()
