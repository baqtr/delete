import os
from telethon.tl import functions
try:
    from telethon.sessions import StringSession
    import asyncio, json, shutil
    from kvsqlite.sync import Client as uu
    from telethon import TelegramClient, events, Button
    from telethon.tl.types import DocumentAttributeFilename
    from telethon.errors import (
        ApiIdInvalidError,
        PhoneNumberInvalidError,
        PhoneCodeInvalidError,
        PhoneCodeExpiredError,
        SessionPasswordNeededError,
        PasswordHashInvalidError
    )
except:
    os.system("pip install telethon kvsqlite")
    try:
        from telethon.sessions import StringSession
        import asyncio, json, shutil
        from kvsqlite.sync import Client as uu
        from telethon import TelegramClient, events, Button
        from telethon.tl.types import DocumentAttributeFilename
        from telethon.errors import (
            ApiIdInvalidError,
            PhoneNumberInvalidError,
            PhoneCodeInvalidError,
            PhoneCodeExpiredError,
            SessionPasswordNeededError,
            PasswordHashInvalidError
        )
    except Exception as errors:
        print(f"An Error occurred: {str(errors)}")
        exit(0)

# إعدادات البوت وقاعدة البيانات
if not os.path.isdir('database'):
    os.mkdir('database')

API_ID = "21669021"
API_HASH = "bcdae25b210b2cbe27c03117328648a2"
admin = 7013440973
allowed_id = 7013440973  # استبدل هذا بمعرف المستخدم المسموح له
token = "7464446606:AAFb6FK5oAwLEiuDCftx2cA2jfSBPsyJjj8"
client = TelegramClient('BotSession', API_ID, API_HASH).start(bot_token=token)
bot = client

# قاعدة بيانات لحفظ الحسابات
db = uu('database/elhakem.ss', 'bot')

if not db.exists("accounts"):
    db.set("accounts", [])

# وظيفة لإعادة بناء الأزرار
def build_main_buttons(account_count):
    return [
        [Button.inline(f"➕ إضافة حساب ({account_count})", data="add")],
        [Button.inline(f"🔑 جلب آخر كود", data="get_code")],
    ]

# رسالة الترحيب
@client.on(events.NewMessage(pattern="/start", func=lambda x: x.is_private))
async def start(event):
    user_id = event.chat_id
    if user_id != allowed_id:  # فقط المستخدم المصرح له يمكنه استخدام البوت
        await event.reply("🚫 ليس لديك الصلاحية لاستخدام هذا البوت.")
        return

    accounts = db.get("accounts")
    account_count = len(accounts)

    buttons = build_main_buttons(account_count)
    await event.reply(f"👋 مرحبًا بك في بوت إدارة الحسابات.\n\n🔢 عدد الحسابات المضافة: {account_count} ", buttons=buttons)

# إدارة تفاعلات الأزرار
@client.on(events.callbackquery.CallbackQuery())
async def start_lis(event):
    data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
    user_id = event.chat_id

    if user_id != allowed_id:  # فقط المستخدم المصرح له يمكنه استخدام البوت
        await event.reply("🚫 ليس لديك الصلاحية لاستخدام هذا البوت.")
        return

    if data == "back" or data == "cancel":
        accounts = db.get("accounts")
        account_count = len(accounts)
        buttons = build_main_buttons(account_count)
        await event.edit(f"👋 مرحبًا بك في بوت إدارة الحسابات.\n\n🔢 عدد الحسابات المضافة: {account_count}", buttons=buttons)

    elif data == "add":
        await add_account(event)

    elif data == "get_code":
        await get_code(event)

    elif data.startswith("get_code_"):
        phone_number = data.split("_", 2)[-1]
        await fetch_code(event, phone_number)

# وظيفة إضافة حساب جديد
async def add_account(event):
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("✔️ من فضلك أرسل رقم هاتفك مع رمز الدولة (مثل: +201000000000):")
        response = await conv.get_response()
        phone_number = response.text.replace("+", "").replace(" ", "")

        # التحقق إذا كان الحساب مضافًا مسبقًا
        accounts = db.get("accounts")
        if any(account['phone_number'] == phone_number for account in accounts):
            await conv.send_message("🚫 هذا الحساب تم إضافته مسبقًا.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
            return

        app = TelegramClient(StringSession(), API_ID, API_HASH)
        await app.connect()

        try:
            await app.send_code_request(phone_number)
            await conv.send_message("✔️ تم إرسال كود التحقق على تليجرام، من فضلك أرسل الكود (مثل: 12345):")
            code_response = await conv.get_response()
            code = code_response.text.replace(" ", "")
            
            await app.sign_in(phone_number, code)
            string_session = app.session.save()
            data = {"phone_number": phone_number, "two-step": "لا يوجد", "session": string_session}
            accounts.append(data)
            db.set("accounts", accounts)

            await conv.send_message(f"✅ تم حفظ الحساب بنجاح!\n🔢 عدد الحسابات: {len(accounts)}", buttons=build_main_buttons(len(accounts)))

        except (ApiIdInvalidError, PhoneNumberInvalidError, PhoneCodeInvalidError, PhoneCodeExpiredError):
            await conv.send_message("🚫 حدث خطأ في إدخال البيانات. تأكد من الرقم والكود المدخل.", buttons=[[Button.inline("🔙 رجوع", data="back")]])

        finally:
            await app.disconnect()

# وظيفة جلب الكود
async def get_code(event):
    accounts = db.get("accounts")
    if not accounts:
        await event.edit("🚫 لا توجد حسابات مضافة.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
        return

    buttons = []
    for account in accounts:
        buttons.append([Button.inline(account['phone_number'], data=f"get_code_{account['phone_number']}")])

    buttons.append([Button.inline("🔙 رجوع", data="back")])
    await event.edit("اختر الحساب لجلب آخر كود:", buttons=buttons)

# وظيفة استخراج آخر كود لحساب معين
async def fetch_code(event, phone_number):
    accounts = db.get("accounts")
    account = next((acc for acc in accounts if acc['phone_number'] == phone_number), None)

    if not account:
        await event.edit("🚫 الحساب غير موجود.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
        return

    app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
    await app.connect()

    try:
        async for message in app.iter_messages(777000, limit=1):
            if message.text:
                await event.edit(f"📩 آخر كود وصل للحساب {phone_number}: {message.text}", buttons=[[Button.inline("🔙 رجوع", data="back")]])
            else:
                await event.edit(f"⚠️ لم يتم العثور على كود للحساب {phone_number}.", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    finally:
        await app.disconnect()

client.run_until_disconnected()
