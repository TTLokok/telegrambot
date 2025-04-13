import os
import asyncio
from pyrogram import Client as PyroClient, filters as pyro_filters
from pyrogram.types import Message as PyroMessage
from telegram import Update, InputMediaPhoto, InputMediaVideo, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, filters as tg_filters, ContextTypes
from pyrogram.errors import FloodWait

# === 从环境变量读取 ===
BOT_TOKEN = os.getenv("7911637199:AAGq-QcwCoYYInRAR0TquMlzZ4hBBsGaYDk ")
API_ID = int(os.getenv("20380733"))
API_HASH = os.getenv("4896e7f9b203bfdc4b720f193355137b")
SESSION_NAME = os.getenv("SESSION_NAME", "my_session")
TARGET_CHAT_ID = int(os.getenv(" -1002361310821"))
TOPIC_ID = int(os.getenv("17583"))
ALLOWED_USER_ID = int(os.getenv("ALLOWED_USER_ID"))
group_ids = list(map(int, os.getenv("-1002100267512", "-1001522738059").split(",")))

processed_message_ids = set()

pyro_app = PyroClient(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)

def load_processed_message_ids():
    try:
        with open("processed_ids.txt", "r") as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_processed_message_ids():
    with open("processed_ids.txt", "w") as f:
        f.write("\n".join(map(str, processed_message_ids)))

async def send_to_topic(bot, media_group):
    if not media_group:
        return
    await bot.send_media_group(
        chat_id=TARGET_CHAT_ID,
        media=media_group,
        message_thread_id=TOPIC_ID
    )

async def collect_all_history():
    for target_group_id in group_ids:
        async for message in pyro_app.get_chat_history(target_group_id):
            if not message or not hasattr(message, "id"):
                continue
            if str(message.id) in processed_message_ids:
                continue
            await process_media_pyrogram(message)
            await asyncio.sleep(2)

@pyro_app.on_message(pyro_filters.media)
async def handle_new_media(client: PyroClient, message: PyroMessage):
    if str(message.id) in processed_message_ids:
        return
    await process_media_pyrogram(message)

async def process_media_pyrogram(message: PyroMessage):
    bot = Bot(BOT_TOKEN)
    media_group = []

    if message.video:
        media_group.append(InputMediaVideo(message.video.file_id, caption=message.caption or ""))
    elif message.photo:
        media_group.append(InputMediaPhoto(message.photo.file_id, caption=message.caption or ""))
    elif message.document and message.document.mime_type == "video/mp4":
        media_group.append(InputMediaVideo(message.document.file_id, caption=message.caption or ""))

    if media_group:
        await send_to_topic(bot, media_group)

    processed_message_ids.add(str(message.id))
    save_processed_message_ids()

async def handle_user_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if message.from_user.id != ALLOWED_USER_ID:
        await message.reply_text("🚫 你没有权限使用此 bot")
        return

    media_group = []
    if message.video:
        media_group.append(InputMediaVideo(message.video.file_id, caption=message.caption or ""))
    elif message.photo:
        media_group.append(InputMediaPhoto(message.photo[-1].file_id, caption=message.caption or ""))
    elif message.document and message.document.mime_type == "video/mp4":
        media_group.append(InputMediaVideo(message.document.file_id, caption=message.caption or ""))

    if not media_group:
        await message.reply_text("⚠️ 请发送视频、图片或 mp4 文件")
        return

    await asyncio.sleep(2)
    await send_to_topic(context.bot, media_group)
    await message.reply_text("✅ 成功转发到群组 Topic！")

async def main():
    global processed_message_ids
    processed_message_ids = load_processed_message_ids()

    await pyro_app.start()
    await collect_all_history()

    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    media_filter = tg_filters.VIDEO | tg_filters.PHOTO | tg_filters.Document.MimeType("video/mp4")
    bot_app.add_handler(MessageHandler(media_filter, handle_user_upload))

    print("🤖 系统已启动，监听中...")
    await asyncio.gather(bot_app.run_polling(), asyncio.Event().wait())

if __name__ == "__main__":
    asyncio.run(main())
