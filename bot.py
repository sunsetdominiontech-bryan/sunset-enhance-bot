import os
import logging
from datetime import datetime
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ParseMode, ChatMemberStatus
from PIL import Image, ImageEnhance, ImageFilter
import json

logging.basicConfig(level=logging.WARNING)

OWNER_USERNAME = "sunset_channel_owner"

REQUIRED_CHATS = [
    "@sunset_hacking_group",
    "@sunset_dominion_tech",
    "@sunset_channel_bot",
    "@sunset_bot_group",
    "@sunsettechgroup",
    "@sunsetdominionchat"
]

WELCOME_PHOTO = "https://files.catbox.moe/chgfqq.png"

USERS_FILE = "users.json"
STATS_FILE = "stats.json"

ADMIN_IDS = [7125501771]

# ================= DATA ================= #

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f:
                return json.load(f)
        except:
            pass
    return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

users_db = load_json(USERS_FILE, {})
stats_db = load_json(STATS_FILE, {"total_users": 0, "total_enhances": 0})

def save_user(user):
    uid = str(user.id)
    if uid not in users_db:
        users_db[uid] = {
            "username": user.username,
            "joined": datetime.now().strftime("%Y-%m-%d"),
            "active": True
        }
        stats_db["total_users"] = len(users_db)
        save_json(USERS_FILE, users_db)
        save_json(STATS_FILE, stats_db)

# ================= ENHANCER ================= #

class PhotoEnhancer:
    @staticmethod
    def enhance(data, mode):
        img = Image.open(BytesIO(data)).convert("RGB")

        if mode == "auto":
            img = ImageEnhance.Sharpness(img).enhance(1.5)
            img = ImageEnhance.Contrast(img).enhance(1.2)
        elif mode == "hd":
            img = img.filter(ImageFilter.UnsharpMask(2, 150, 3))
        elif mode == "bright":
            img = ImageEnhance.Brightness(img).enhance(1.3)
        elif mode == "vivid":
            img = ImageEnhance.Color(img).enhance(1.5)
        elif mode == "sharp":
            img = ImageEnhance.Sharpness(img).enhance(2.5)
        elif mode == "smooth":
            img = img.filter(ImageFilter.SMOOTH_MORE)

        out = BytesIO()
        img.save(out, "JPEG", quality=90)
        out.seek(0)
        return out.getvalue()

# ================= HELPERS ================= #

async def check_membership(user_id, context):
    not_joined = []
    for chat in REQUIRED_CHATS:
        try:
            member = await context.bot.get_chat_member(chat, user_id)
            if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
                not_joined.append(chat)
        except:
            not_joined.append(chat)
    return not_joined

def join_keyboard(chats):
    kb = []
    for chat in chats:
        kb.append([
            InlineKeyboardButton(
                f"Join {chat.replace('@','')}",
                url=f"https://t.me/{chat[1:]}"
            )
        ])
    kb.append([
        InlineKeyboardButton("✅ I've Joined All Channels", callback_data="check_joined")
    ])
    return InlineKeyboardMarkup(kb)

# ================= COMMANDS ================= #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    not_joined = await check_membership(user.id, context)

    if not_joined:
        await update.message.reply_photo(
            WELCOME_PHOTO,
            caption=f"""
🔒 <b>Join Required</b>

Hi {user.first_name} 👋  
Join all channels below, then tap <b>I've Joined All Channels</b>.
""",
            parse_mode=ParseMode.HTML,
            reply_markup=join_keyboard(not_joined)
        )
        return

    save_user(user)

    await update.message.reply_photo(
        WELCOME_PHOTO,
        caption=f"""
🎨 <b>AI Photo Enhancer</b>

Welcome {user.first_name} 👋

📸 Send a photo  
⚡ Choose a mode  
✅ Get result

Modes: Auto • HD • Bright • Vivid • Sharp • Smooth
Owner: @{OWNER_USERNAME}
""",
        parse_mode=ParseMode.HTML
    )

# ================= CALLBACK ================= #

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data == "check_joined":
        not_joined = await check_membership(user.id, context)
        if not_joined:
            await query.answer("❌ You never join all channels", show_alert=True)
            return

        await query.message.reply_text("✅ Verified! Now send /start")
        return

# ================= PHOTO ================= #

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    not_joined = await check_membership(user.id, context)

    if not_joined:
        await update.message.reply_text("⚠️ Join channels first. Use /start")
        return

    save_user(user)
    context.user_data["photo"] = update.message.photo[-1].file_id

    keyboard = [
        [InlineKeyboardButton("Auto", callback_data="enh_auto"),
         InlineKeyboardButton("HD", callback_data="enh_hd")],
        [InlineKeyboardButton("Bright", callback_data="enh_bright"),
         InlineKeyboardButton("Vivid", callback_data="enh_vivid")],
        [InlineKeyboardButton("Sharp", callback_data="enh_sharp"),
         InlineKeyboardButton("Smooth", callback_data="enh_smooth")]
    ]

    await update.message.reply_text(
        "Choose enhancement mode:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def enhance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    mode = query.data.replace("enh_", "")
    file_id = context.user_data.get("photo")

    if not file_id:
        await query.message.reply_text("❌ Send photo again")
        return

    await query.edit_message_text("⚡ Enhancing...")

    file = await context.bot.get_file(file_id)
    data = await file.download_as_bytearray()
    result = PhotoEnhancer.enhance(bytes(data), mode)

    stats_db["total_enhances"] += 1
    save_json(STATS_FILE, stats_db)

    await context.bot.send_photo(
        query.message.chat_id,
        photo=BytesIO(result),
        caption="✅ Enhancement done"
    )

# ================= MAIN ================= #

def main():
    TOKEN = "7575109319:AAETfT8fuI2QyDvYM-AmEjHiIfPQAc8GzLE"

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(CallbackQueryHandler(enhance_handler, pattern="^enh_"))
    app.add_handler(CallbackQueryHandler(callbacks))

    print("✅ Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()