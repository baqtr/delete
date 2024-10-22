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
        print('An Error with: ' + str(errors))
        exit(0)

if not os.path.isdir('database'):
    os.mkdir('database')

API_ID = "21669021"
API_HASH = "bcdae25b210b2cbe27c03117328648a2"
admin = 7013440973
allowed_id = 7013440973  # Replace this with the allowed user's Telegram ID
token = "7464446606:AAFb6FK5oAwLEiuDCftx2cA2jfSBPsyJjj8"
client = TelegramClient('BotSession', API_ID, API_HASH).start(bot_token=token)
bot = client

# Create DataBase
db = uu('database/elhakem.ss', 'bot')

if not db.exists("accounts"):
    db.set("accounts", [])

@client.on(events.NewMessage(pattern="/start", func=lambda x: x.is_private))
async def start(event):
    user_id = event.chat_id
    if user_id != allowed_id:  # Only allow the specified user
        await event.reply("🚫 ليس لديك الصلاحية لاستخدام هذا البوت.")
        return

    buttons = [
        [Button.inline("➕ إضافة حساب", data="add")],
        [Button.inline("🔢 عدد الحسابات", data="account_count")],
        [Button.inline("📲 جلب جلسة", data="get_session")],
        [Button.inline("🧹 تنظيف الحسابات", data="clean_accounts")],
        [Button.inline("📦 نسخة احتياطية", data="zip_all")],
        [Button.url("💻 المطور", "https://t.me/xx44g")]
    ]
    await event.reply("👋 مرحبًا بك في بوت إدارة الحسابات، اختر من الأزرار أدناه ما تود فعله.", buttons=buttons)

@client.on(events.callbackquery.CallbackQuery())
async def start_lis(event):
    data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
    user_id = event.chat_id

    if user_id != allowed_id:  # Only allow the specified user
        await event.reply("🚫 ليس لديك الصلاحية لاستخدام هذا البوت.")
        return

    if data == "back" or data == "cancel":
        buttons = [
            [Button.inline("➕ إضافة حساب", data="add")],
            [Button.inline("🔢 عدد الحسابات", data="account_count")],
            [Button.inline("📲 جلب جلسة", data="get_session")],
            [Button.inline("🧹 تنظيف الحسابات", data="clean_accounts")],
            [Button.inline("📦 نسخة احتياطية", data="zip_all")],
            [Button.url("💻 المطور", "https://t.me/xx44g")]
        ]
        await event.edit("👋 مرحبًا بك في بوت إدارة الحسابات، اختر من الأزرار أدناه ما تود فعله.", buttons=buttons)

    if data == "add":
        async with bot.conversation(event.chat_id) as x:
            await x.send_message("✔️الان ارسل رقمك مع رمز دولتك , مثال :+201000000000")
            txt = await x.get_response()
            phone_number = txt.text.replace("+", "").replace(" ", "")

            # Check if the account already exists
            accounts = db.get("accounts")
            if any(account['phone_number'] == phone_number for account in accounts):
                await x.send_message("- هذا الحساب تم إضافته مسبقًا.")
                return

            app = TelegramClient(StringSession(), API_ID, API_HASH)
            await app.connect()
            password = None
            try:
                await app.send_code_request(phone_number)
            except (ApiIdInvalidError):
                await x.send_message("ʏᴏᴜʀ **API_ID** ᴀɴᴅ **API_HASH** ɪs ɪɴᴠᴀʟɪᴅ.")
                return
            except (PhoneNumberInvalidError):
                await x.send_message("ᴛʜᴇ **ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ** ʏᴏᴜ'ᴠᴇ sᴇɴᴛ ɪs ɪɴᴠᴀʟɪᴅ.")
                return
            await x.send_message("- تم ارسال كود التحقق الخاص بك علي تليجرام. أرسل الكود بالتنسيق التالي : 1 2 3 4 5")
            txt = await x.get_response()
            code = txt.text.replace(" ", "")
            try:
                await app.sign_in(phone_number, code, password=None)
                string_session = app.session.save()
                data = {"phone_number": phone_number, "two-step": "لا يوجد", "session": string_session}
                accounts.append(data)
                db.set("accounts", accounts)
                await x.send_message("- تم حفظ الحساب بنجاح ✅", buttons=[[Button.inline("🔙 رجوع", data="back")]])
            except (PhoneCodeInvalidError):
                await x.send_message("الكود المدخل غير صحيح.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
                return
            except (PhoneCodeExpiredError):
                await x.send_message("الكود المدخل منتهي الصلاحية.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
                return
            except (SessionPasswordNeededError):
                await x.send_message("- أرسل رمز التحقق بخطوتين الخاص بحسابك")
                txt = await x.get_response()
                password = txt.text
                try:
                    await app.sign_in(password=password)
                except (PasswordHashInvalidError):
                    await x.send_message("رمز التحقق بخطوتين المدخل غير صحيح.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
                    return
                string_session = app.session.save()
                data = {"phone_number": phone_number, "two-step": password, "session": string_session}
                accounts.append(data)
                db.set("accounts", accounts)
                await x.send_message("- تم حفظ الحساب بنجاح ✅", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    if data == "get_session":
        async with bot.conversation(event.chat_id) as x:
            acc = db.get("accounts")
            if len(acc) == 0:
                await x.send_message("- لا يوجد حسابات مسجلة.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
                return

            buttons = [[Button.inline(f"📱 {i['phone_number']}", data=f"get_{i['phone_number']}")] for i in acc]
            buttons.append([Button.inline("🔙 رجوع", data="back")])
            await x.send_message("- اختر الحساب لجلب الجلسة:", buttons=buttons)

    if data.startswith("get_"):
        phone_number = data.split("_")[1]
        acc = db.get("accounts")
        for i in acc:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()

                # Get account info (name and number of devices)
                me = await app.get_me()
                sessions = await app(functions.account.GetAuthorizationsRequest())
                device_count = len(sessions.authorizations)

                text = f"• رقم الهاتف : {phone_number}\n" \
                       f"- الاسم : {me.first_name} {me.last_name or ''}\n" \
                       f"- عدد الاجهزة المتصلة : {device_count}\n" \
                       f"- التحقق بخطوتين : {i['two-step']}\n" \
                       f"- الجلسة : `{i['session']}`"

                buttons = [
                    [Button.inline("🔒 تسجيل خروج", data=f"logout_{phone_number}")],
                    [Button.inline("📩 جلب الكود", data=f"code_{phone_number}")],
                    [Button.inline("🔙 رجوع", data="back")]
                ]
                await event.edit(text, buttons=buttons)
                await app.disconnect()

    if data.startswith("logout_"):
        phone_number = data.split("_")[1]
        acc = db.get("accounts")
        for i in acc:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()
                await app.log_out()
                await app.disconnect()# Remove the account from the database
                acc.remove(i)
                db.set("accounts", acc)

                await event.edit(f"- تم تسجيل الخروج من الحساب: {phone_number}", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    if data.startswith("code_"):
        phone_number = data.split("_")[1]
        acc = db.get("accounts")
        for i in acc:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()
                code = await app.get_messages(777000, limit=1)
                await event.edit(f"اخر كود تم استلامه: {code[0].message}", buttons=[[Button.inline("🔙 رجوع", data="back")]])
                await app.disconnect()

    if data == "account_count":
        accounts = db.get("accounts")
        count = len(accounts)
        await event.edit(f"🔢 عدد الحسابات المسجلة: {count}", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    if data == 'zip_all':
        folder_path = f"./database"
        zip_file_name = f"database.zip"
        zip_file_nam = f"database"
        try:
            shutil.make_archive(zip_file_nam, 'zip', folder_path)
            with open(zip_file_name, 'rb') as zip_file:
                await client.send_file(user_id, zip_file, attributes=[DocumentAttributeFilename(file_name="database.zip")])
            os.remove(zip_file_name)
            await event.edit("- تم إرسال النسخة الاحتياطية بنجاح ✅", buttons=[[Button.inline("🔙 رجوع", data="back")]])
        except Exception as a:
            await event.edit(f"❌ حدث خطأ أثناء إنشاء النسخة الاحتياطية: {a}", buttons=[[Button.inline("🔙 رجوع", data="back")]])

    if data == "clean_accounts":
        async with bot.conversation(event.chat_id) as x:
            acc = db.get("accounts")
            if len(acc) == 0:
                await x.send_message("- لا يوجد حسابات مسجلة.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
                return

            total_deleted = 0
            progress_message = await x.send_message(f"🧹 جاري حذف المحادثات...\n- المحادثات المحذوفة حتى الآن: {total_deleted}")

            for account in acc:
                app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
                await app.connect()

                dialogs = await app.get_dialogs()
                for dialog in dialogs:
                    try:
                        await app.delete_dialog(dialog.id)
                        total_deleted += 1
                        # تحديث الرسالة مع العدد الحالي
                        await progress_message.edit(f"🧹 جاري حذف المحادثات...\n- المحادثات المحذوفة حتى الآن: {total_deleted}")
                    except Exception as e:
                        await x.send_message(f"حدث خطأ مع الحساب {account['phone_number']}: {e}")

                await app.disconnect()

            # الرسالة النهائية بعد انتهاء الحذف
            await progress_message.edit(f"🧹 تم حذف جميع المحادثات بنجاح.\n- العدد الإجمالي للمحادثات المحذوفة: {total_deleted}", buttons=[[Button.inline("🔙 رجوع", data="back")]])

client.run_until_disconnected()
