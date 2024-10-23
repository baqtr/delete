import os
from telethon.tl import functions
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
        [Button.inline(f"🛠 ترتيب حساب", data="manage_accounts")],
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
    await event.reply("👋 مرحبًا بك في بوت إدارة الحسابات.", buttons=buttons)

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
        await event.edit("👋 مرحبًا بك في بوت إدارة الحسابات.", buttons=buttons)

    elif data == "add":
        await add_account(event)

    elif data == "get_code":
        await get_code(event)

    elif data == "manage_accounts":
        await manage_accounts(event)

    elif data.startswith("manage_"):
        phone_number = data.split("_", 2)[-1]
        await show_account_options(event, phone_number)

    elif data.startswith("get_code_"):
        phone_number = data.split("_", 2)[-1]
        await fetch_code(event, phone_number)

    elif data.startswith("set_photo_"):
        phone_number = data.split("_", 2)[-1]
        await set_account_photo(event, phone_number)

    elif data.startswith("set_bio_"):
        phone_number = data.split("_", 2)[-1]
        await set_account_bio(event, phone_number)

    elif data.startswith("set_username_"):
        phone_number = data.split("_", 2)[-1]
        await set_account_username(event, phone_number)

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

            await conv.send_message(f"✅ تم حفظ الحساب بنجاح!", buttons=build_main_buttons(len(accounts)))

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
        buttons.append([Button.inline(f"📱 {account['phone_number']}", data=f"get_code_{account['phone_number']}")])

    buttons.append([Button.inline("🔙 رجوع", data="back")])
    await event.edit("اختر الحساب لجلب آخر كود:", buttons=buttons)

# وظيفة ترتيب الحسابات
async def manage_accounts(event):
    accounts = db.get("accounts")
    if not accounts:
        await event.edit("🚫 لا توجد حسابات مضافة.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
        return

    buttons = []
    for account in accounts:
        buttons.append([Button.inline(f"⚙️ {account['phone_number']}", data=f"manage_{account['phone_number']}")])

    buttons.append([Button.inline("🔙 رجوع", data="back")])
    await event.edit("اختر الحساب لترتيبه:", buttons=buttons)

# وظيفة عرض خيارات الحساب
async def show_account_options(event, phone_number):
    buttons = [
        [Button.inline("🖼 وضع صورة", data=f"set_photo_{phone_number}")],
        [Button.inline("📄 وضع نبذة", data=f"set_bio_{phone_number}")],
        [Button.inline("✏️ وضع اسم مستخدم", data=f"set_username_{phone_number}")],
        [Button.inline("🔙 رجوع", data="manage_accounts")]
    ]
    await event.edit(f"⚙️ إعدادات الحساب {phone_number}:", buttons=buttons)

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
                code = ''.join(filter(str.isdigit, message.text))
                await event.edit(f"📩 آخر كود للحساب {phone_number}: (`{code}`)\n\n(يمكنك نسخه)", parse_mode="md", buttons=[[Button.inline("🔙 رجوع", data="back")]])
            else:
                await event.edit(f"⚠️ لم يتم العثور على كود للحساب {phone_number}.", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    finally:
        await app.disconnect()

# وظيفة وضع صورة للحساب
async def set_account_photo(event, phone_number):
    app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
    await app.connect()

    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("📷 من فضلك أرسل الصورة التي تريد وضعها:")
        response = await conv.get_response()
        if response.photo:
            await app(functions.photos.UploadProfilePhotoRequest(file=await app.upload_file(response.photo)))
            await conv.send_message("✅ تم تحديث صورة الحساب بنجاح!")
        else:
            await conv.send_message("🚫 يجب عليك إرسال صورة.", buttons=[[Button.inline("🔙 رجوع", data=f"manage_{phone_number}")]])

    await app.disconnect()

# وظيفة وضع نبذة للحساب
async def set_account_bio(event, phone_number):
    app = TelegramClient(StringSession(account['session']), API_ID,API_HASH)
    await app.connect()

    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("📝 من فضلك أرسل النبذة التي تريد وضعها:")
        response = await conv.get_response()
        bio = response.text

        try:
            await app(functions.account.UpdateProfileRequest(about=bio))
            await conv.send_message("✅ تم تحديث النبذة بنجاح!")
        except Exception as e:
            await conv.send_message(f"🚫 حدث خطأ أثناء تحديث النبذة: {str(e)}", buttons=[[Button.inline("🔙 رجوع", data=f"manage_{phone_number}")]])

    await app.disconnect()

# وظيفة وضع اسم مستخدم للحساب
async def set_account_username(event, phone_number):
    app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
    await app.connect()

    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("✏️ من فضلك أرسل اسم المستخدم الذي تريد وضعه:")
        response = await conv.get_response()
        username = response.text

        try:
            await app(functions.account.UpdateUsernameRequest(username=username))
            await conv.send_message("✅ تم تحديث اسم المستخدم بنجاح!")
        except Exception as e:
            await conv.send_message(f"🚫 حدث خطأ أثناء تحديث اسم المستخدم: {str(e)}", buttons=[[Button.inline("🔙 رجوع", data=f"manage_{phone_number}")]])

    await app.disconnect()

client.run_until_disconnected()
