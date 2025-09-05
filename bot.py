import os
import sqlite3
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import Forbidden, BadRequest

BOT_TOKEN = os.getenv("BOT_TOKEN")       # Railway env
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # Source channel
DB_FILE = "movies.db"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔹 1. Initialize DB
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            caption TEXT PRIMARY KEY,
            message_id INTEGER
        )
    """)
    conn.commit()
    conn.close()

# 🔹 2. Save movie into DB
def save_movie(caption, message_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO movies (caption, message_id) VALUES (?, ?)", 
                       (caption, message_id))
        conn.commit()
    except Exception as e:
        logger.error(f"DB Error: {e}")
    finally:
        conn.close()

# 🔹 3. Search movies
def search_movies(keyword):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT caption, message_id FROM movies WHERE caption LIKE ?", (f"%{keyword}%",))
    results = cursor.fetchall()
    conn.close()
    return results

# 🔹 4. Count movies
def count_movies():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM movies")
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ---------------- Bot Handlers ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Send /movie <name> to get movies!")

# /movie command → forward requested movie(s)
async def send_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /movie <name>")
        return

    query = " ".join(context.args).lower()
    results = search_movies(query)

    if not results:
        await update.message.reply_text("❌ No matches found. Try another keyword.")
        return

    for caption, msg_id in results[:10]:  # limit forwarding to 10 results
        try:
            await context.bot.forward_message(
                chat_id=update.message.chat_id,
                from_chat_id=CHANNEL_ID,
                message_id=msg_id
            )
        except (Forbidden, BadRequest) as e:
            logger.error(f"Error forwarding {caption}: {e}")

# /stats command → show how many stored
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total = count_movies()
    await update.message.reply_text(f"📂 Movies stored: {total}")

# /list command → list captions (with optional keyword filter)
async def list_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        keyword = " ".join(context.args).lower()
        matches = search_movies(keyword)
    else:
        matches = search_movies("")  # all movies

    if not matches:
        await update.message.reply_text("❌ No captions found.")
        return

    MAX_CHARS = 4000
    text = ""
    for i, (cap, _) in enumerate(matches, start=1):
        line = f"{i}. {cap}\n"
        if len(text) + len(line) > MAX_CHARS:
            break
        text += line

    await update.message.reply_text(f"📂 Found {len(matches)} matches:\n\n{text}")

# Auto-save when new movie posted in channel
async def save_from_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post and update.channel_post.caption:
        caption = update.channel_post.caption.lower().strip()
        save_movie(caption, update.channel_post.message_id)
        logger.info(f"✅ Saved from channel: {caption}")

# ---------------- Main ----------------
def main():
    init_db()  # make sure DB exists

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("movie", send_movie))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("list", list_movies))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, save_from_channel))

    app.run_polling()

if __name__ == "__main__":
    main()
