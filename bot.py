import os, json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")   # put in Railway env
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DB_FILE = "movies.json"

# Load DB
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        MOVIES = json.load(f)
else:
    MOVIES = {}   # {caption: message_id}

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Send /movie <name> to get movies!")

# /movie command → forward movie(s)
async def send_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /movie <name>")
        return

    query = " ".join(context.args).lower()
    found = False

    for caption, msg_id in MOVIES.items():
        if query in caption:   # ✅ substring match
            try:
                # Forward from channel using saved message_id
                await context.bot.forward_message(
                    chat_id=update.message.chat_id,
                    from_chat_id=CHANNEL_ID,
                    message_id=msg_id
                )
                found = True
            except Exception as e:
                print(f"Error forwarding {caption}: {e}")

    if not found:
        await update.message.reply_text("❌ No matches found. Try another keyword.")

# Show how many movies are stored
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📂 Movies stored: {len(MOVIES)}")
    
# /list command → only list captions
async def list_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not MOVIES:
        await update.message.reply_text("⚠️ No movies saved yet.")
        return

    if context.args:
        keyword = " ".join(context.args).lower()
        matches = [cap for cap in MOVIES.keys() if keyword in cap]
    else:
        matches = list(MOVIES.keys())

    if not matches:
        await update.message.reply_text("❌ No captions found with that keyword.")
        return

    # limit for safety
    sample = matches[:600000]
    text = "\n".join([f"{i+1}. {cap}" for i, cap in enumerate(sample)])
    await update.message.reply_text(f"📂 Found {len(matches)} matches:\n\n{text}")

    # query = " ".join(context.args).lower()
    # found = False

    # for caption, msg_id in MOVIES.items():
    #     if query in caption:   # ✅ simple substring match
    #         await context.bot.forward_message(
    #             chat_id=update.message.chat_id,
    #             from_chat_id=CHANNEL_ID,
    #             message_id=msg_id
    #         )
    #         found = True

    # if not found:
    #     await update.message.reply_text("No matches yet. Try another keyword.")

# Auto-save when new movie posted in channel
async def save_from_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post and update.channel_post.caption:
        caption = update.channel_post.caption.lower().strip()
        MOVIES[caption] = update.channel_post.message_id
        with open(DB_FILE, "w") as f:
            json.dump(MOVIES, f)
        print(f"✅ Saved from channel: {caption}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("movie", send_movie))
    app.add_handler(CommandHandler("stats", stats))   # ✅ new command registered
    app.add_handler(CommandHandler("list", list_movies))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, save_from_channel))

    app.run_polling()

if __name__ == "__main__":
    main()
