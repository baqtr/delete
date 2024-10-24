import os
from telethon.tl import functions
from telethon.sessions import StringSession
import asyncio, json, shutil
from kvsqlite.sync import Client as uu
from telethon import TelegramClient, events, Button
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
        [Button.inline("📦 نسخ احتياطي", data="backup")],
        [Button.inline("📤 رفع نسخة احتياطية", data="restore")],
        [Button.inline("🧹 تنظيف الحسابات", data="clean_accounts")],
        [Button.inline("🚪 تسجيل الخروج من حساب", data="logout_account")],
        [Button.inline("ℹ️ جلب معلومات الحساب", data="account_info")]
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

    elif data == "backup":
        await backup_data(event)

    elif data == "restore":
        await restore_data(event)

    elif data == "clean_accounts":
        await choose_account_to_clean(event)

    elif data == "logout_account":
        await choose_account_to_logout(event)

    elif data == "account_info":
        await choose_account_to_get_info(event)

    elif data.startswith("get_code_"):
        phone_number = data.split("_", 2)[-1]
        await fetch_code(event, phone_number)

    elif data.startswith("clean_"):
        phone_number = data.split("_", 2)[-1]
        await clean_account(event, phone_number)

    elif data.startswith("logout_"):
        phone_number = data.split("_", 2)[-1]
        await logout_account(event, phone_number)

    elif data.startswith("info_"):
        phone_number = data.split("_", 2)[-1]
        await get_account_info(event, phone_number)

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
                # استخراج فقط الكود من الرسالة
                code = ''.join(filter(str.isdigit, message.text))
                await event.edit(f"📩 آخر كود للحساب {phone_number}: (`{code}`)\n\n(يمكنك نسخه)", parse_mode="md", buttons=[[Button.inline("🔙 رجوع", data="back")]])
            else:
                await event.edit(f"⚠️ لم يتم العثور على كود للحساب {phone_number}.", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    finally:
        await app.disconnect()

# وظيفة النسخ الاحتياطي
async def backup_data(event):
    backup_file = 'backup/backup_data.json'
    
    if not os.path.isdir('backup'):
        os.mkdir('backup')
    
    data = {
        "accounts": db.get("accounts")
    }

    with open(backup_file, 'w') as f:
        json.dump(data, f)

    await bot.send_file(event.chat_id, backup_file, caption="📦 النسخة الاحتياطية تم إنشاؤها بنجاح.")
    shutil.rmtree('backup')

# وظيفة استعادة النسخة الاحتياطية
async def restore_data(event):
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("📤 من فضلك أرسل ملف النسخة الاحتياطية:")
        response = await conv.get_response()
        
        if not response.file or not response.file.name.endswith('.json'):
            await conv.send_message("🚫 الملف غير صحيح، يرجى إرسال ملف JSON.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
            return
        
        backup_file = 'backup/restore_data.json'
        
        if not os.path.isdir('backup'):
            os.mkdir('backup')

        await bot.download_media(response, backup_file)

        with open(backup_file, 'r') as f:
            data = json.load(f)

        db.set("accounts", data.get("accounts", []))

        await conv.send_message("✅ تم استعادة البيانات بنجاح.", buttons=build_main_buttons(len(data.get("accounts", []))))
        shutil.rmtree('backup')

# وظيفة اختيار الحساب لتنظيف المحادثات
async def choose_account_to_clean(event):
    accounts = db.get("accounts")
    if not accounts:
        await event.edit("🚫 لا توجد حسابات مضافة.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
        return

    buttons = []
    for account in accounts:
        buttons.append([Button.inline(f"🧹 {account['phone_number']}", data=f"clean_{account['phone_number']}")])

    buttons.append([Button.inline("🔙 رجوع", data="back")])
    await event.edit("اختر الحساب لتنظيف المحادثات:", buttons=buttons)

# وظيفة تنظيف المحادثات لحساب معين
async def clean_account(event, phone_number):
    accounts = db.get("accounts")
    account = next((acc for acc in accounts if acc['phone_number'] == phone_number), None)

    if not account:
        await event.edit("🚫 الحساب غير موجود.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
        return

    app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
    await app.connect()

    try:
        async for dialog in app.iter_dialogs():
            if dialog.is_user or dialog.is_group or dialog.is_channel:
                await app.delete_dialog(dialog.id)
        await event.edit(f"🧹 تم تنظيف المحادثات للحساب {phone_number}.", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    finally:
        await app.disconnect()

# وظيفة اختيار الحساب لتسجيل الخروج
async def choose_account_to_logout(event):
    accounts = db.get("accounts")
    if not accounts:
        await event.edit("🚫 لا توجد حسابات مضافة.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
        return

    buttons = []
    for account in accounts:
        buttons.append([Button.inline(f"🚪 {account['phone_number']}", data=f"logout_{account['phone_number']}")])

    buttons.append([Button.inline("🔙 رجوع", data="back")])
    await event.edit("اختر الحساب لتسجيل الخروج:", buttons=buttons)

# وظيفة تسجيل الخروج من حساب معين
async def logout_account(event, phone_number):
    accounts = db.get("accounts")
    account = next((acc for acc in accounts if acc['phone_number'] == phone_number), None)

    if not account:
        await event.edit("🚫 الحساب غير موجود.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
        return

    app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
    await app.connect()

    try:
        await app.log_out()
        accounts.remove(account)
        db.set("accounts", accounts)
        await event.edit(f"🚪 تم تسجيل الخروج من الحساب {phone_number}.", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    finally:
        await app.disconnect()

# وظيفة اختيار الحساب لجلب معلوماته
async def choose_account_to_get_info(event):
    accounts = db.get("accounts")
    if not accounts:
        await event.edit("🚫 لا توجد حسابات مضافة.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
        return

    buttons = []
    for account in accounts:
        buttons.append([Button.inline(f"ℹ️ {account['phone_number']}", data=f"info_{account['phone_number']}")])

    buttons.append([Button.inline("🔙 رجوع", data="back")])
    await event.edit("اختر الحساب لجلب المعلومات:", buttons=buttons)

# وظيفة جلب معلومات الحساب
async def get_account_info(event, phone_number):
    accounts = db.get("accounts")
    account = next((acc for acc in accounts if acc['phone_number'] == phone_number), None)

    if not account:
        await event.edit("🚫 الحساب غير موجود.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
        return

    app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
    await app.connect()

    try:
        me = await app.get_me()
        if await app.is_user_authorized():
            two_step_status = "مفعل" if await app(functions.account.GetPasswordRequest()) else "غير مفعل"
            await event.edit(
                f"ℹ️ معلومات الحساب {phone_number}:\n\n"
                f"🆔 المعرف: {me.id}\n"
                f"👤 الاسم: {me.first_name or ''} {me.last_name or ''}\n"
                f"📧 البريد الإلكتروني: {me.username}\n"
                f"🗝 التحقق بخطوتين: {two_step_status}",
                buttons=[[Button.inline("🔙 رجوع", data="back")]]
            )
        else:
            await event.edit(f"🚫 الحساب {phone_number} غير مسجل الدخول.", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    finally:
        await app.disconnect()

# بدء تشغيل البوت
client.start()
client.run_until_disconnected()
