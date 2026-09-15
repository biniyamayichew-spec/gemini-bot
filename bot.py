import telebot
from telebot import types
import requests
from flask import Flask
from threading import Thread

# Render ወደብ እንዲያገኝ የሚረዳ አነስተኛ Web Server
app = Flask('')

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 1. መሰረታዊ መረጃዎች
BOT_TOKEN = "8933234159:AAFRgSyYYwdJS4B06TW7DEtsjAq3v1pTnGE"
ADMIN_CHAT_ID = 7784016689
HUBX_API_KEY = "rsk_live_4b9e7da5dbdc4fa20bdde731819ae5cf4e6d9b2a53a18586"
BASE_URL = "https://open-greeting-glow-production.up.railway.app/api/public/reseller/v1"

PRICE_BIRR = 500
TELEBIRR_PHONE = "0944905958"
ACCOUNT_NAME = "Biniyam Ayichew"

bot = telebot.TeleBot(BOT_TOKEN)

HEADERS = {
    "Authorization": f"Bearer {HUBX_API_KEY}",
    "Content-Type": "application/json"
}

@bot.message_handler(commands=['start'])
def start_handler(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✨ Gemini Pro ግዛ (500 ETB)", callback_data="buy_gemini"))
    welcome_text = (
        "👋 <b>እንኳን ወደ Gemini AI Pro መሸጫ ቦት በሰላም መጡ!</b>\n\n"
        "ፈጣን እና አስተማማኝ አገልግሎት ለማግኘት ከታች ያለውን ይጫኑ፦"
    )
    bot.reply_to(message, welcome_text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "buy_gemini")
def buy_click(call):
    pay_text = (
        "💳 <b>የክፍያ መመሪያ፦</b>\n\n"
        f"• የክፍያ መጠን፦ <b>{PRICE_BIRR} ብር</b>\n"
        f"• የቴሌብር ቁጥር፦ <code>{TELEBIRR_PHONE}</code> <i>(ለመቅዳት ቁጥሩን ይንኩት)</i>\n"
        f"• ስም፦ <b>{ACCOUNT_NAME}</b>\n\n"
        "⚠️ <b>ማሳሰቢያ፦</b> እባክዎ ክፍያ ከፈጸሙ በኋላ የከፈሉበትን <b>Screenshot (ደረሰኝ)</b> እዚህ ቦት ላይ ይላኩ። እንዳረጋገጥን ወዲያውኑ ይላክልዎታል!"
    )
    bot.send_message(call.message.chat.id, pay_text, parse_mode="HTML")

@bot.message_handler(content_types=['photo'])
def receive_screenshot(message):
    user_id = message.chat.id
    user_name = message.from_user.first_name or "ደንበኛ"
    user_handle = f"@{message.from_user.username}" if message.from_user.username else "የለውም"
    
    markup = types.InlineKeyboardMarkup()
    approve_btn = types.InlineKeyboardButton("✅ አጽድቅ (Approve)", callback_data=f"approve_{user_id}")
    reject_btn = types.InlineKeyboardButton("❌ ሰርዝ (Reject)", callback_data=f"reject_{user_id}")
    markup.add(approve_btn, reject_btn)

    caption = (
        "🔔 <b>አዲስ የክፍያ ደረሰኝ ደርሷል!</b>\n\n"
        f"• ደንበኛ፦ {user_name} ({user_handle})\n"
        f"• የደንበኛ መለያ (ID)፦ <code>{user_id}</code>\n"
        f"• መጠን፦ {PRICE_BIRR} ብር\n\n"
        "በቴሌብርህ ገንዘቡ መግባቱን አረጋግጠህ አጽድቅ።"
    )

    photo_id = message.photo[-1].file_id
    bot.send_photo(ADMIN_CHAT_ID, photo_id, caption=caption, reply_markup=markup, parse_mode="HTML")
    bot.reply_to(message, "✅ ደረሰኝዎ ደርሶናል! አስተዳዳሪው ክፍያውን ሲያረጋግጥ አካውንቱ/ቁልፉ ወዲያውኑ ይላክልዎታል።")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def admin_action(call):
    action, target_user_id = call.data.split("_")
    target_user_id = int(target_user_id)

    if call.from_user.id != ADMIN_CHAT_ID:
        bot.answer_callback_query(call.id, "ይህ ላንተ አይፈቀድም!", show_alert=True)
        return

    if action == "approve":
        current_caption = call.message.caption or ""
        bot.edit_message_caption(
            chat_id=ADMIN_CHAT_ID,
            message_id=call.message.message_id,
            caption=current_caption + "\n\n🟢 <b>ተረጋግጦ ትዕዛዝ ተልኳል!</b>",
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id, "ትዕዛዙ እየተስተናገደ ነው...")

        payload = {"quantity": 1}
        try:
            res = requests.post(f"{BASE_URL}/orders", headers=HEADERS, json=payload)
            res_data = res.json()

            if res.status_code in [200, 201]:
                item = res_data.get("data", res_data.get("code", "የተሳካ ግዢ!"))
                success_msg = (
                    "🎉 <b>ክፍያዎ ተረጋግጧል!</b>\n\n"
                    f"የእርስዎ Gemini Pro መረጃ፦\n<code>{item}</code>\n\n"
                    "አገልግሎታችንን ስለተጠቀሙ እናመሰግናለን!"
                )
                bot.send_message(target_user_id, success_msg, parse_mode="HTML")
            else:
                err_msg = res_data.get("message", "በHubX በኩል ስህተት ገጥሟል")
                bot.send_message(ADMIN_CHAT_ID, f"⚠️ ትዕዛዝ አልተሳካም (HubX Error)፦ {err_msg}")
                bot.send_message(target_user_id, "⚠️ በትዕዛዝዎ ላይ ትንሽ መዘግየት አጋጥሟል፤ አስተዳዳሪው ያነጋግርዎታል።")
        except Exception as e:
            bot.send_message(ADMIN_CHAT_ID, f"⚠️ የAPI ግንኙነት ስህተት፦ {str(e)}")

    elif action == "reject":
        current_caption = call.message.caption or ""
        bot.edit_message_caption(
            chat_id=ADMIN_CHAT_ID,
            message_id=call.message.message_id,
            caption=current_caption + "\n\n🔴 <b>ክፍያው ተሰርዟል!</b>",
            parse_mode="HTML"
        )
        bot.send_message(target_user_id, "❌ የላኩት ደረሰኝ ትክክል ስላልሆነ ክፍያዎ አልተፈቀደም። እባክዎ እንደገና ይሞክሩ ወይም አስተዳዳሪውን ያነጋግሩ።")
        bot.answer_callback_query(call.id, "ትዕዛዙ ተሰርዟል!")

# Web Server ማስነሻ
keep_alive()

print("ቦቱ እየሰራ ነው...")
bot.infinity_polling()
                
