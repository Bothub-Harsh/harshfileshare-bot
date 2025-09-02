import os, json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DB_FILE = "movies.json"

# Load database
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        MOVIES = json.load(f)
else:
    MOVIES = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send /movie <name> to get a movie!")

async def send_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /movie <name>")
        return

    movie_name = " ".join(context.args).lower()
    if movie_name in MOVIES:
        message_id = MOVIES[movie_name]
        await context.bot.forward_message(
            chat_id=update.message.chat_id,
            from_chat_id=CHANNEL_ID,
            message_id=message_id
        )
    else:
        await update.message.reply_text("Movie not found in database.")

# Listen to new posts in channel
async def save_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post:
        msg = update.channel_post
        if msg.caption:
            movie_name = msg.caption.lower().strip()
            MOVIES[movie_name] = msg.message_id

            # Save to file
            with open(DB_FILE, "w") as f:
                json.dump(MOVIES, f)

            print(f"Saved: {movie_name} -> {msg.message_id}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("movie", send_movie))

    # Listen for new channel posts
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, save_movie))

    app.run_polling()

if __name__ == "__main__":
    main()
