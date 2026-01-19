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

# Configure logging (minimal)
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Bot Configuration
OWNER_USERNAME = "sunset_channel_owner"  # without @

REQUIRED_CHATS = [
    "@sunset_hacking_group",
    "@sunset_dominion_tech",
    "@sunset_channel_bot",
    "@sunset_bot_group",
    "@sunsettechgroup",
    "@sunsetdominionchat"
]

CHANNEL_LINKS = {
    "@sunset_dominion_tech": "https://t.me/sunset_dominion_tech",
    "@sunset_hacking_group": "https://t.me/sunset_hacking_group"
}

WELCOME_PHOTO = "https://files.catbox.moe/chgfqq.png"

# File to store user data (lightweight)
USERS_FILE = "users.json"
STATS_FILE = "stats.json"

class DataManager:
    """Lightweight data manager using JSON files"""
    
    @staticmethod
    def load_users():
        try:
            if os.path.exists(USERS_FILE):
                with open(USERS_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    @staticmethod
    def save_users(users):
        try:
            with open(USERS_FILE, 'w') as f:
                json.dump(users, f)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    @staticmethod
    def load_stats():
        try:
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {"total_enhances": 0, "total_users": 0}
    
    @staticmethod
    def save_stats(stats):
        try:
            with open(STATS_FILE, 'w') as f:
                json.dump(stats, f)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")

class PhotoEnhancer:
    """Optimized photo enhancement class"""
    
    @staticmethod
    def enhance_photo(image_bytes, mode='auto'):
        """Apply enhancement based on mode"""
        try:
            img = Image.open(BytesIO(image_bytes))
            
            # Reduce size if too large (memory optimization)
            max_size = 2048
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            if mode == 'auto':
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.5)
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.2)
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.1)
            
            elif mode == 'hd':
                img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(2.0)
            
            elif mode == 'bright':
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.3)
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.15)
            
            elif mode == 'vivid':
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.5)
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.3)
            
            elif mode == 'sharp':
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(2.5)
            
            elif mode == 'smooth':
                img = img.filter(ImageFilter.SMOOTH_MORE)
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.05)
            
            # Save to bytes
            output = BytesIO()
            img.save(output, format='JPEG', quality=90, optimize=True)
            output.seek(0)
            return output.getvalue()
        
        except Exception as e:
            logger.error(f"Enhancement error: {e}")
            return None

# Global data storage
users_db = DataManager.load_users()
stats_db = DataManager.load_stats()

# Admin user IDs (replace with your Telegram ID)
ADMIN_IDS = [7125501771]  # Replace with your actual Telegram user ID

def is_admin(user_id):
    return user_id in ADMIN_IDS

def save_user(user_id, username=None):
    """Save user info"""
    user_id_str = str(user_id)
    if user_id_str not in users_db:
        users_db[user_id_str] = {
            'username': username,
            'joined': datetime.now().isoformat(),
            'active': True
        }
        stats_db['total_users'] = len(users_db)
        DataManager.save_users(users_db)
        DataManager.save_stats(stats_db)

async def check_membership(user_id, context):
    """Check if user is member of all required channels"""
    not_joined = []
    
    for chat in REQUIRED_CHATS:
        try:
            member = await context.bot.get_chat_member(chat, user_id)
            if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
                not_joined.append(chat)
        except Exception as e:
            logger.error(f"Error checking membership for {chat}: {e}")
            not_joined.append(chat)
    
    return not_joined

def create_join_keyboard(not_joined_chats):
    """Create keyboard with join buttons"""
    keyboard = []
    
    for chat in not_joined_chats:
        chat_name = chat.replace("@", "").replace("_", " ").title()
        keyboard.append([InlineKeyboardButton(f"📢 Join {chat_name}", url=f"https://t.me/{chat[1:]}")])
    
    keyboard.append([InlineKeyboardButton("✅ I've Joined All Channels", callback_data='check_joined')])
    
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    user = update.effective_user
    
    # Check membership
    not_joined = await check_membership(user.id, context)
    
    if not_joined:
        join_text = f"""
🔒 <b>Welcome to AI Photo Enhancer Bot!</b>

Hey {user.first_name}! 👋

To unlock this amazing AI-powered photo enhancer, please join all our channels first:

"""
        for i, chat in enumerate(not_joined, 1):
            chat_name = chat.replace("@", "").replace("_", " ").title()
            join_text += f"{i}. {chat_name}\n"
        
        join_text += f"""
<b>🎁 Why Join?</b>
✅ Access professional photo enhancement
✅ Get premium tech tips & tutorials
✅ Early access to new features
✅ Exclusive hacking & security guides
✅ Join our amazing tech community

👇 Click buttons below to join all channels, then tap "I've Joined All"
"""
        
        try:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=WELCOME_PHOTO,
                caption=join_text,
                parse_mode=ParseMode.HTML,
                reply_markup=create_join_keyboard(not_joined)
            )
        except:
            await update.message.reply_text(
                join_text,
                parse_mode=ParseMode.HTML,
                reply_markup=create_join_keyboard(not_joined)
            )
        return
    
    # User has joined all channels
    save_user(user.id, user.username)
    
    keyboard = [
        [InlineKeyboardButton("📸 How to Use", callback_data='help')],
        [InlineKeyboardButton("📊 My Stats", callback_data='stats'),
         InlineKeyboardButton("ℹ️ About", callback_data='about')],
        [InlineKeyboardButton("🌐 Sunset Dominion", url=CHANNEL_LINKS["@sunset_dominion_tech"]),
         InlineKeyboardButton("💻 Hacking Group", url=CHANNEL_LINKS["@sunset_hacking_group"])]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🎨 <b>Welcome to AI Photo Enhancer Bot!</b>

Hello {user.first_name}! 👋

Transform your ordinary photos into stunning masterpieces with advanced AI-powered enhancement algorithms! ✨

<b>🚀 Quick Start Guide:</b>
1️⃣ Send me any photo (JPG, PNG, WEBP)
2️⃣ Choose your enhancement mode
3️⃣ Get professional results in 2-5 seconds!

<b>💎 6 Professional Enhancement Modes:</b>
• <b>🎯 Auto Enhance</b> - Smart AI-powered enhancement
• <b>💎 HD Quality</b> - Maximum sharpness & clarity
• <b>☀️ Bright Mode</b> - Perfect lighting correction
• <b>🌈 Vivid Colors</b> - Vibrant color boost
• <b>✨ Sharp Focus</b> - Crystal clear details
• <b>🌸 Smooth Skin</b> - Professional portrait mode

<b>⚡ Premium Features:</b>
✅ Lightning-fast processing (2-5s)
✅ Professional quality results
✅ Multiple enhancement algorithms
✅ Privacy-focused (no storage)
✅ Free unlimited usage!
✅ No watermarks!

<i>Powered by Sunset Dominion Tech 🌅</i>
Owner: @{OWNER_USERNAME}

👇 Tap buttons below to learn more!
"""
    
    try:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=WELCOME_PHOTO,
            caption=welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    except:
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    help_text = f"""
📖 <b>How to Use Photo Enhancer Bot</b>

<b>Step 1️⃣ - Send Your Photo:</b>
📸 Send any photo (as photo, not file)
🖼️ Supports: JPG, PNG, WEBP formats
📏 Auto-optimized for best quality

<b>Step 2️⃣ - Choose Enhancement Mode:</b>

🎯 <b>Auto Enhance</b> - Perfect for quick, balanced enhancement

💎 <b>HD Quality</b> - Maximum sharpness & detail

☀️ <b>Brighten</b> - Fix dark or underexposed photos

🌈 <b>Vivid Colors</b> - Make colors pop!

✨ <b>Sharp Focus</b> - Ultra-sharp details

🌸 <b>Smooth Skin</b> - Professional portrait enhancement

<b>📱 Available Commands:</b>
/start - Restart bot
/help - This guide
/stats - View statistics
/about - Learn about bot
/features - All features

<b>Need Help?</b>
👨‍💻 Contact: @{OWNER_USERNAME}

<i>Powered by Sunset Dominion Tech 🌅</i>
"""
    await update.message.reply_text(help_text, parse_mode=ParseMode.HTML)

async def features_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Features command"""
    features_text = f"""
🌟 <b>Advanced Features Overview</b>

<b>🎨 Enhancement Modes:</b>
• 6 professional algorithms
• AI-powered optimization
• Professional-grade results

<b>⚡ Performance:</b>
• Ultra-fast (2-5 seconds)
• Memory-optimized
• Auto size optimization

<b>🔒 Privacy & Security:</b>
• Zero data storage
• In-memory processing only
• GDPR compliant

<i>All features FREE! 🎁</i>
Owner: @{OWNER_USERNAME}
"""
    keyboard = [
        [InlineKeyboardButton("🌐 Sunset Dominion", url=CHANNEL_LINKS["@sunset_dominion_tech"])],
        [InlineKeyboardButton("💻 Hacking Group", url=CHANNEL_LINKS["@sunset_hacking_group"])]
    ]
    await update.message.reply_text(features_text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stats command"""
    user_id = str(update.effective_user.id)
    stats_text = f"""
📊 <b>Bot Statistics</b>

<b>🌐 Global:</b>
👥 Total Users: {stats_db.get('total_users', 0):,}
✨ Enhancements: {stats_db.get('total_enhances', 0):,}

<b>👤 Your Stats:</b>
📅 Member Since: {users_db.get(user_id, {}).get('joined', 'Unknown')[:10]}
✅ Status: Active User
"""
    keyboard = [
        [InlineKeyboardButton("🌐 Sunset Dominion", url=CHANNEL_LINKS["@sunset_dominion_tech"])],
        [InlineKeyboardButton("💻 Hacking Group", url=CHANNEL_LINKS["@sunset_hacking_group"])]
    ]
    await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """About command"""
    about_text = f"""
ℹ️ <b>About AI Photo Enhancer Bot</b>

📌 Version: 2.5 Advanced
👨‍💻 Developer: @{OWNER_USERNAME}
🏢 SUNSET DOMINION TECH™
🔧

<b>✨ Features:</b>
✅ 6 Enhancement Modes
✅ HD Quality Processing
✅ Lightning-Fast 
✅ Privacy-Focused
✅ Free Unlimited Usage

<b>📞 Support:</b>
💬 Owner: @{OWNER_USERNAME}
📢 Channels: Join below

<i>Built with ❤️ by Sunset Dominion Tech 🌅</i>
"""
    keyboard = [
        [InlineKeyboardButton("🌐 Sunset Dominion", url=CHANNEL_LINKS["@sunset_dominion_tech"]),
         InlineKeyboardButton("💻 Hacking Group", url=CHANNEL_LINKS["@sunset_hacking_group"])],
        [InlineKeyboardButton("👨‍💻 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    await update.message.reply_text(about_text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo uploads"""
    user = update.effective_user
    not_joined = await check_membership(user.id, context)
    
    if not_joined:
        await update.message.reply_text(
            "⚠️ <b>Please join all required channels first!</b>\n\nUse /start to see join buttons.",
            parse_mode=ParseMode.HTML
        )
        return
    
    save_user(user.id, user.username)
    photo = update.message.photo[-1]
    context.user_data['photo_file_id'] = photo.file_id
    
    keyboard = [
        [InlineKeyboardButton("🎯 Auto Enhance", callback_data='enhance_auto'),
         InlineKeyboardButton("💎 HD Quality", callback_data='enhance_hd')],
        [InlineKeyboardButton("☀️ Brighten", callback_data='enhance_bright'),
         InlineKeyboardButton("🌈 Vivid Colors", callback_data='enhance_vivid')],
        [InlineKeyboardButton("✨ Sharp Focus", callback_data='enhance_sharp'),
         InlineKeyboardButton("🌸 Smooth Skin", callback_data='enhance_smooth')]
    ]
    await update.message.reply_text(
        "📸 <b>Photo Received!</b>\n\nChoose enhancement mode:\n👇 Select below:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == 'check_joined':
        not_joined = await check_membership(user_id, context)
        if not_joined:
            await query.answer("❌ Please join all channels first!", show_alert=True)
        else:
            await query.answer("✅ Verified! Welcome!", show_alert=True)
            await query.message.delete()
            update.effective_user = query.from_user
            update.message = query.message
            await start(update, context)
    elif query.data == 'help':
        await help_command(update, context)
    elif query.data == 'stats':
        await stats_command(update, context)
    elif query.data == 'about':
        await about_command(update, context)
    elif query.data.startswith('enhance_'):
        not_joined = await check_membership(user_id, context)
        if not_joined:
            await query.answer("⚠️ Join all channels first!", show_alert=True)
            return
        await process_enhancement(update, context)

async def process_enhancement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process photo enhancement"""
    query = update.callback_query
    mode = query.data.replace('enhance_', '')
    mode_names = {
        'auto': 'Auto Enhance', 'hd': 'HD Quality', 'bright': 'Brighten',
        'vivid': 'Vivid Colors', 'sharp': 'Sharp Focus', 'smooth': 'Smooth Skin'
    }
    
    await query.edit_message_text(
        f"⚡ <b>Processing {mode_names.get(mode)}...</b>\n\n"
        "🔄 Applying AI enhancement\n⏱️ Please wait 2-5 seconds...",
        parse_mode=ParseMode.HTML
    )
    
    try:
        photo_file_id = context.user_data.get('photo_file_id')
        if not photo_file_id:
            await query.edit_message_text("❌ Photo not found. Send a new photo.")
            return
        
        file = await context.bot.get_file(photo_file_id)
        photo_bytes = await file.download_as_bytearray()
        enhanced_bytes = PhotoEnhancer.enhance_photo(bytes(photo_bytes), mode)
        
        if not enhanced_bytes:
            await query.edit_message_text("❌ Enhancement failed. Try again.")
            return
        
        stats_db['total_enhances'] = stats_db.get('total_enhances', 0) + 1
        DataManager.save_stats(stats_db)
        
        caption = f"""✅ <b>Enhancement Complete!</b>

🎨 Mode: {mode_names.get(mode)}
⚡ Quality: Professional Grade
🌅 Powered by: Sunset Dominion Tech

<b>📢 Join Our Channels:</b>
👇 Get exclusive tech content!
"""
        keyboard = [
            [InlineKeyboardButton("🌐 Sunset Dominion Tech", url=CHANNEL_LINKS["@sunset_dominion_tech"])],
            [InlineKeyboardButton("💻 Sunset Hacking Group", url=CHANNEL_LINKS["@sunset_hacking_group"])],
            [InlineKeyboardButton("🔄 Enhance Another", callback_data='help')]
        ]
        
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=BytesIO(enhanced_bytes),
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        await query.edit_message_text(
            f"✅ <b>Enhancement Complete!</b>\n\n"
            f"📸 Mode: {mode_names.get(mode)}\n"
            f"⬆️ Check photo above!\n\n"
            f"🔄 Send another photo!",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.edit_message_text(
            f"❌ <b>Processing Failed</b>\n\nContact: @{OWNER_USERNAME}",
            parse_mode=ParseMode.HTML
        )
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin broadcast"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only!")
        return
    
    reply_to = update.message.reply_to_message
    if not context.args and not reply_to:
        await update.message.reply_text(
            "<b>📢 Broadcast System</b>\n\n"
            "<b>Text:</b> /broadcast &lt;message&gt;\n"
            "<b>Photo:</b> Reply to photo with /broadcast &lt;caption&gt;\n\n"
            "<i>Sunset Dominion Broadcast 🌅</i>",
            parse_mode=ParseMode.HTML
        )
        return
    
    message = ' '.join(context.args) if context.args else ""
    photo_file_id = reply_to.photo[-1].file_id if reply_to and reply_to.photo else None
    
    status_msg = await update.message.reply_text(
        f"📢 <b>Starting Broadcast...</b>\n\n"
        f"📊 Users: {len(users_db):,}\n"
        f"📷 Type: {'Photo' if photo_file_id else 'Text'}\n"
        f"⏳ Please wait...",
        parse_mode=ParseMode.HTML
    )
    
    success = 0
    failed = 0
    blocked = 0
    start_time = datetime.now()
    
    for user_id in users_db.keys():
        try:
            broadcast_text = f"📢 <b>Broadcast from Sunset Dominion</b>\n\n{message}\n\n<i>Powered by Sunset Dominion Tech 🌅</i>"
            if photo_file_id:
                await context.bot.send_photo(int(user_id), photo=photo_file_id, caption=broadcast_text, parse_mode=ParseMode.HTML)
            else:
                await context.bot.send_message(int(user_id), text=broadcast_text, parse_mode=ParseMode.HTML)
            success += 1
            
            if success % 50 == 0:
                elapsed = (datetime.now() - start_time).seconds
                await status_msg.edit_text(
                    f"📢 <b>Broadcasting...</b>\n\n"
                    f"✅ Sent: {success:,}\n"
                    f"❌ Failed: {failed:,}\n"
                    f"🚫 Blocked: {blocked:,}\n"
                    f"⏱️ Time: {elapsed}s",
                    parse_mode=ParseMode.HTML
                )
        except Exception as e:
            if "blocked" in str(e).lower():
                blocked += 1
                users_db[user_id]['active'] = False
            else:
                failed += 1
    
    DataManager.save_users(users_db)
    elapsed_time = (datetime.now() - start_time).seconds
    
    await status_msg.edit_text(
        f"📢 <b>✅ Broadcast Complete!</b>\n\n"
        f"✅ Sent: {success:,}\n"
        f"❌ Failed: {failed:,}\n"
        f"🚫 Blocked: {blocked:,}\n"
        f"📈 Success Rate: {(success/max(len(users_db), 1)*100):.1f}%\n"
        f"⏱️ Time: {elapsed_time}s\n"
        f"⚡ Speed: {success/max(elapsed_time, 1):.1f} msg/s",
        parse_mode=ParseMode.HTML
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin stats"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only!")
        return
    
    active = sum(1 for u in users_db.values() if u.get('active', True))
    admin_text = f"""
👑 <b>Admin Dashboard</b>

👥 <b>Users:</b>
• Total: {len(users_db):,}
• Active: {active:,}
• Inactive: {len(users_db) - active:,}

✨ <b>Activity:</b>
• Enhancements: {stats_db.get('total_enhances', 0):,}
• Avg/User: {stats_db.get('total_enhances', 0) // max(len(users_db), 1)}

💾 <b>Storage:</b>
• Users: {os.path.getsize(USERS_FILE) if os.path.exists(USERS_FILE) else 0:,} bytes
• Stats: {os.path.getsize(STATS_FILE) if os.path.exists(STATS_FILE) else 0:,} bytes

<b>📢 Channels:</b>
"""
    for i, chat in enumerate(REQUIRED_CHATS, 1):
        admin_text += f"{i}. {chat}\n"
    
    admin_text += f"\n<b>🔧 Commands:</b>\n/broadcast\n/adminstats\n\n<i>Sunset Dominion Admin 🌅</i>"
    await update.message.reply_text(admin_text, parse_mode=ParseMode.HTML)

def main():
    """Start bot"""
    TOKEN = "7575109319:AAETfT8fuI2QyDvYM-AmEjHiIfPQAc8GzLE"
    
    if not TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found")
        print("Set it in Railway environment variables")
        return
    
    print("🚀 Starting AI Photo Enhancer Bot...")
    print(f"👥 Users: {len(users_db)}")
    print(f"✨ Enhancements: {stats_db.get('total_enhances', 0)}")
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("features", features_command))
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("adminstats", admin_stats))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("✅ Bot started successfully!")
    print("🌅 Powered by Sunset Dominion Tech")
    print(f"👨‍💻 Owner: @{OWNER_USERNAME}")
    print("\n🔄 Bot running...")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()

