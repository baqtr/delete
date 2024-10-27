import nest_asyncio
import re
import asyncio
from telethon import TelegramClient, events
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telethon.sessions import StringSession

# إعداد nest_asyncio لتجنب مشاكل الحلقة
nest_asyncio.apply()

# إعدادات تيليثون
api_id = 22377281  # API ID الخاص بك
api_hash = '7882457407a0b7e0fe71984064fbe6d7'  # API Hash الخاص بك

# معلومات بوت التلجرام
bot_token = '7924484400:AAFy7EXN-bBbzyElloNL7Y3uGU_E1rnuttM'

# إعداد الجلسة
session_string = None
client = None

# متغيرات لتخزين الرقم ووقت آخر رسالة
number = ''
message_interval = 600  # 600 ثانية = 10 دقائق

async def start(update: Update, context) -> None:
    keyboard = [
        [InlineKeyboardButton("تسجيل", callback_data='register')],
        [InlineKeyboardButton("ارسال الرسائل", callback_data='send_message')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('اختر خيار:', reply_markup=reply_markup)

async def button_handler(update: Update, context) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == 'register':
        await query.message.reply_text('من فضلك أرسل الجلسة الخاصة بك.')
        context.user_data['action'] = 'register'
    
    elif query.data == 'send_message':
        # التحقق من تسجيل الجلسة
        if client is None or not await client.is_user_authorized():
            await query.message.reply_text('يجب تسجيل الدخول أولاً. من فضلك أرسل الجلسة الخاصة بك.')
            context.user_data['action'] = 'register'
        else:
            await query.message.reply_text('أرسل لي اسم مستخدم الشخص الذي تريد إرسال رسالة إليه.')
            context.user_data['action'] = 'send_message'

async def message_handler(update: Update, context) -> None:
    global client
    action = context.user_data.get('action')
    
    if action == 'register':
        session_string = update.message.text
        try:
            client = TelegramClient(StringSession(session_string), api_id, api_hash)
            await client.connect()
            if not await client.is_user_authorized():
                await update.message.reply_text('فشل تسجيل الدخول. الجلسة غير صحيحة.')
            else:
                await update.message.reply_text('تم تسجيل الدخول بنجاح.')
        except Exception as e:
            await update.message.reply_text(f'حدث خطأ: {str(e)}')

    elif action == 'send_message':
        username = update.message.text
        context.user_data['username'] = username
        await update.message.reply_text(f'سيتم إرسال الرسائل تلقائيًا إلى {username}.')

        # تشغيل العملية التلقائية لإرسال الرسائل
        await send_automatic_messages(username)

async def send_automatic_messages(username):
    global client

    recipient = username  # المرسل إليه
    notification_recipient = '@Mt_9u'  # حساب تيليجرام لإرسال الوقت المتبقي

    try:
        while True:
            # إرسال الرسائل كل 10 دقائق
            await send_messages(recipient)

            # بدء العد التنازلي
            remaining_time = message_interval
            while remaining_time > 0:
                # إرسال الوقت المتبقي إلى الحساب المحدد
                await client.send_message(notification_recipient, f'الوقت المتبقي للنشر مرة أخرى: {remaining_time} ثانية')
                await asyncio.sleep(10)  # الانتظار 10 ثوانٍ
                remaining_time -= 10

    except Exception as e:
        # في حالة التوقف، إرسال رسالة "تم توقف البوت"
        await client.send_message(notification_recipient, f"تم توقف البوت بسبب: {str(e)}")

async def send_messages(recipient):
    global client, number

    # إرسال الرسائل المطلوبة
    await client.send_message(recipient, 'راتب')
    await asyncio.sleep(2)
    await client.send_message(recipient, 'بخشيش')
    await asyncio.sleep(2)
    
    # إرسال فلوسي وانتظار الرد الذي يحتوي على الرقم
    await client.send_message(recipient, 'فلوسي')

    # انتظار الرد من الشخص
    @client.on(events.NewMessage(chats=recipient))
    async def handler(event):
        message = event.message.message

        # التحقق من وجود الرسالة التي تحتوي على "فلوسك" ونسخ الرقم
        match = re.search(r'فلوسك (\d+) ريال', message)
        if match:
            number = match.group(1)
            # إرسال الرسالة "استثمار" مع الرقم
            await client.send_message(recipient, f'استثمار {number}')

        # إلغاء المعالجة بعد نسخ الرقم
        await client.remove_event_handler(handler)

# تشغيل البرنامج الرئيسي
async def main() -> None:
    application = Application.builder().token(bot_token).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
