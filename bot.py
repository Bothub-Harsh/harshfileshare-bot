from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")   # load from Railway env
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

MOVIES = {
    "inception": 11,
    "avatar": 15
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send /movie <name> to get the movie!")

async def send_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /movie <name>")
        return

    movie_name = " ".join(context.args).lower()
    if movie_name in MOVIES:
        await context.bot.forward_message(
            chat_id=update.message.chat_id,
            from_chat_id=CHANNEL_ID,
            message_id=MOVIES[movie_name]
        )
    else:
        await update.message.reply_text("Movie not found!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("movie", send_movie))
    app.run_polling()

if __name__ == "__main__":
    main()
