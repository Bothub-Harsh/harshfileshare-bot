import os
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")   # Railway env
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DB_FILE = "movies.db"  # Use SQLite database instead of JSON

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Send /movie <name> to get movies!")

# /movie command → forward movie(s)
async def send_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /movie <name>")
        return  

    query = " ".join(context.args).lower()
    
    # Connect to SQLite database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Search for the movie in the database
    cursor.execute("SELECT message_id FROM movies WHERE LOWER(caption) LIKE ?", ('%' + query + '%',))
    results = cursor.fetchall()
    conn.close()

    if results:
        for (msg_id,) in results:
            try:
                await context.bot.forward_message(
                    chat_id=update.message.chat_id,
                    from_chat_id=CHANNEL_ID,
                    message_id=msg_id
                )
            except Exception as e:
                print(f"Error forwarding message ID {msg_id}: {e}")
    else:
        await update.message.reply_text("❌ No matches found. Try another keyword.")

# Show how many movies are stored
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM movies")
    count = cursor.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"📂 Movies stored: {count}")

# /list command → only list captions
async def list_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if context.args:
        keyword = " ".join(context.args).lower()
        cursor.execute("SELECT caption FROM movies WHERE LOWER(caption) LIKE ?", ('%' + keyword + '%',))
    else:
        cursor.execute("SELECT caption FROM movies")
    matches = [row[0] for row in cursor.fetchall()]
    conn.close()

    if not matches:
        await update.message.reply_text("❌ No captions found with that keyword.")
        return

    # limit for safety
    sample = matches[:600000]  
    text = "\n\n".join([f"{i+1}. {cap}" for i, cap in enumerate(sample)])
    await update.message.reply_text(f"📂 Found {len(matches)} matches:\n\n{text}")

# Auto-save when new movie posted in channel
async def save_from_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.channel_post and update.channel_post.caption:
        caption = update.channel_post.caption.lower().strip()
        msg_id = update.channel_post.message_id
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS movies (caption TEXT, message_id INTEGER)")
        cursor.execute("INSERT OR IGNORE INTO movies (caption, message_id) VALUES (?, ?)", (caption, msg_id))
        conn.commit()
        conn.close()
        print(f"✅ Saved from channel: {caption}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()  

    app.add_handler(CommandHandler("start", start))  
    app.add_handler(CommandHandler("movie", send_movie))  
    app.add_handler(CommandHandler("stats", stats))  
    app.add_handler(CommandHandler("list", list_movies))  
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, save_from_channel))  

    app.run_polling()

if __name__ == "__main__":
    main()
