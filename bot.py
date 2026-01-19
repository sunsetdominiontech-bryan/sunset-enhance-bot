import logging
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from telegram.constants import ParseMode, ChatMemberStatus

logging.basicConfig(level=logging.INFO)

# ================= CONFIG ================= #

TOKEN = "7575109319:AAETfT8fuI2QyDvYM-AmEjHiIfPQAc8GzLE"

ADMIN_IDS = [7125501771]  # 🔴 replace with YOUR Telegram ID

REQUIRED_CHATS = [
    "@sunset_hacking_group",
    "@sunset_dominion_tech",
    "@sunset_channel_bot",
    "@sunset_bot_group",
    "@sunsettechgroup",
    "@sunsetdominionchat"
]

PROMO_CHANNEL = "https://t.me/sunset_dominion_tech"
WELCOME_PHOTO = "https://files.catbox.moe/chgfqq.png"

# ================= STORAGE ================= #

USERS = set()  # simple in-memory users list for broadcast

# ================= MEMBER VERIFICATION ================= #

async def check_membership(user_id, context):
    not_joined = []
    for chat in REQUIRED_CHATS:
        try:
            member = await context.bot.get_chat_member(chat, user_id)
            if member.status in (
                ChatMemberStatus.LEFT,
                ChatMemberStatus.KICKED
            ):
                not_joined.append(chat)
        except:
            not_joined.append(chat)
    return not_joined

def join_keyboard(chats):
    buttons = []
    for chat in chats:
        buttons.append([
            InlineKeyboardButton(
                f"Join {chat.replace('@','')}",
                url=f"https://t.me/{chat[1:]}"
            )
        ])
    buttons.append([
        InlineKeyboardButton("✅ I've Joined All Channels", callback_data="verify_join")
    ])
    return InlineKeyboardMarkup(buttons)

# ================= PHOTO ENHANCER ================= #

def enhance_photo(data, mode):
    img = Image.open(BytesIO(data)).convert("RGB")

    if mode == "auto":
        img = ImageEnhance.Sharpness(img).enhance(1.6)
        img = ImageEnhance.Contrast(img).enhance(1.3)
    elif mode == "hd":
        img = img.filter(ImageFilter.UnsharpMask(2, 160, 3))
    elif mode == "bright":
        img = ImageEnhance.Brightness(img).enhance(1.35)
    elif mode == "vivid":
        img = ImageEnhance.Color(img).enhance(1.6)
    elif mode == "sharp":
        img = ImageEnhance.Sharpness(img).enhance(2.5)
    elif mode == "smooth":
        img = img.filter(ImageFilter.SMOOTH_MORE)

    out = BytesIO()
    img.save(out, "JPEG", quality=90)
    out.seek(0)
    return out.getvalue()

# ================= KEYBOARDS ================= #

def mode_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Auto", callback_data="enh_auto"),
            InlineKeyboardButton("HD", callback_data="enh_hd")
        ],
        [
            InlineKeyboardButton("Bright", callback_data="enh_bright"),
            InlineKeyboardButton("Vivid", callback_data="enh_vivid")
        ],
        [
            InlineKeyboardButton("Sharp", callback_data="enh_sharp"),
            InlineKeyboardButton("Smooth", callback_data="enh_smooth")
        ]
    ])

def promo_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Join Sunset Dominion Tech", url=PROMO_CHANNEL)]
    ])

# ================= COMMANDS ================= #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USERS.add(user.id)

    not_joined = await check_membership(user.id, context)
    if not_joined:
        await update.message.reply_photo(
            photo=WELCOME_PHOTO,
            caption="""
🔒 <b>Channel Verification Required</b>

You must join all channels below
to use this bot.
""",
            parse_mode=ParseMode.HTML,
            reply_markup=join_keyboard(not_joined)
        )
        return

    await update.message.reply_photo(
        photo=WELCOME_PHOTO,
        caption="✅ <b>Verified!</b>\n\n📸 Send a photo to enhance it.",
        parse_mode=ParseMode.HTML
    )

# ================= CALLBACKS ================= #

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    USERS.add(user.id)

    if query.data == "verify_join":
        not_joined = await check_membership(user.id, context)
        if not_joined:
            await query.answer("❌ Join all channels first", show_alert=True)
            return

        await query.message.reply_text(
            "✅ Verification successful!\n\n📸 Send a photo now."
        )

    elif query.data.startswith("enh_"):
        mode = query.data.replace("enh_", "")
        file_id = context.user_data.get("photo")

        if not file_id:
            await query.message.reply_text("❌ Send a photo first")
            return

        await query.edit_message_text("⚡ Enhancing photo...")

        file = await context.bot.get_file(file_id)
        data = await file.download_as_bytearray()
        result = enhance_photo(bytes(data), mode)

        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=BytesIO(result),
            caption="✅ Enhanced successfully",
            reply_markup=promo_keyboard()
        )

# ================= PHOTO HANDLER ================= #

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USERS.add(user.id)

    not_joined = await check_membership(user.id, context)
    if not_joined:
        await update.message.reply_text(
            "🔒 Join all required channels first.\nUse /start"
        )
        return

    context.user_data["photo"] = update.message.photo[-1].file_id
    await update.message.reply_text(
        "⚡ Choose enhancement mode:",
        reply_markup=mode_keyboard()
    )

# ================= BROADCAST ================= #

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Admin only")
        return

    if not context.args:
        await update.message.reply_text(
            "Usage:\n/broadcast your message"
        )
        return

    text = " ".join(context.args)
    sent = 0

    for user_id in USERS:
        try:
            await context.bot.send_message(
                user_id,
                f"📢 <b>Broadcast</b>\n\n{text}",
                parse_mode=ParseMode.HTML
            )
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ Broadcast sent to {sent} users")

# ================= MAIN ================= #

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(CallbackQueryHandler(callbacks))

    print("✅ Photo Enhancer Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()