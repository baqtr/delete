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

    accounts = db.get("accounts")
    account_count = len(accounts)

    buttons = [
        [Button.inline(f"➕ إضافة حساب ({account_count})", data="add")],
        [Button.inline(f"🔑 جلب آخر كود", data="get_code")],
    ]
    await event.reply(f"👋 مرحبًا بك في بوت إدارة الحسابات.\n🔢 عدد الحسابات: {account_count}", buttons=buttons)

@client.on(events.callbackquery.CallbackQuery())
async def start_lis(event):
    data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
    user_id = event.chat_id

    if user_id != allowed_id:  # Only allow the specified user
        await event.reply("🚫 ليس لديك الصلاحية لاستخدام هذا البوت.")
        return

    if data == "back" or data == "cancel":
        accounts = db.get("accounts")
        account_count = len(accounts)

        buttons = [
            [Button.inline(f"➕ إضافة حساب ({account_count})", data="add")],
            [Button.inline(f"🔑 جلب آخر كود", data="get_code")],
        ]
        await event.edit(f"👋 مرحبًا بك في بوت إدارة الحسابات.\n🔢 عدد الحسابات: {account_count}", buttons=buttons)

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

                await x.send_message("- تم حفظ الحساب بنجاح ✅")
                await asyncio.sleep(2)
                await x.delete_messages([txt.id])
                await x.delete_messages([event.message_id])

                accounts = db.get("accounts")
                account_count = len(accounts)

                buttons = [
                    [Button.inline(f"➕ إضافة حساب ({account_count})", data="add")],
                    [Button.inline(f"🔑 جلب آخر كود", data="get_code")],
                ]
                await x.send_message(f"👋 مرحبًا بك في بوت إدارة الحسابات.\n🔢 عدد الحسابات: {account_count}", buttons=buttons)

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

                await x.send_message("- تم حفظ الحساب بنجاح ✅")
                await asyncio.sleep(2)
                await x.delete_messages([txt.id])
                await x.delete_messages([event.message_id])

                accounts = db.get("accounts")
                account_count = len(accounts)

                buttons = [
                    [Button.inline(f"➕ إضافة حساب ({account_count})", data="add")],
                    [Button.inline(f"🔑 جلب آخر كود", data="get_code")],
                ]
                await x.send_message(f"👋 مرحبًا بك في بوت إدارة الحسابات.\n🔢 عدد الحسابات: {account_count}", buttons=buttons)

    if data == "get_code":
        accounts = db.get("accounts")
        if not accounts:
            await event.edit("🚫 لا يوجد حسابات مضافة.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
            return

        buttons = []
        for account in accounts:
            buttons.append([Button.inline(account['phone_number'], data=f"get_code_{account['phone_number']}")])

        buttons.append([Button.inline("🔙 رجوع", data="back")])
        await event.edit("اختر الحساب لجلب آخر كود:", buttons=buttons)

    if data.startswith("get_code_"):
        phone_number = data.split("_", 2)[-1]
        accounts = db.get("accounts")
        account = next((acc for acc in accounts if acc['phone_number'] == phone_number), None)

        if not account:
            await event.edit("🚫 الحساب غير موجود.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
            return

        app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
        await app.connect()

        # Fetch the latest code sent by Telegram
        async for message in app.iter_messages(777000, limit=1):
            if message.text:
                await event.edit(f"آخر كود وصل للحساب {phone_number}: {message.text}", buttons=[[Button.inline("🔙 رجوع", data="back")]])
            else:
                await event.edit(f"لم يتم العثور على كود للحساب {phone_number}.", buttons=[[Button.inline("🔙 رجوع", data="back")]])

        await app.disconnect()

client.run_until_disconnected()
