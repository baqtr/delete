import os
from telethon.tl import functions
import random
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

    accounts = db.get("accounts")  # Get accounts from database
    num_accounts = len(accounts)

    buttons = [
        [Button.inline(f"➕ إضافة حساب", data="add")],
        [Button.url("💻 المطور", "https://t.me/xx44g")]
    ]
    await event.reply(f"👋 مرحبًا بك في بوت إدارة الحسابات.\n\nعدد الحسابات المضافة حاليًا: {num_accounts}", buttons=buttons)

@client.on(events.callbackquery.CallbackQuery())
async def start_lis(event):
    data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
    user_id = event.chat_id

    if user_id != allowed_id:  # Only allow the specified user
        await event.reply("🚫 ليس لديك الصلاحية لاستخدام هذا البوت.")
        return

    if data == "back" or data == "cancel":
        accounts = db.get("accounts")
        num_accounts = len(accounts)
        buttons = [
            [Button.inline(f"➕ إضافة حساب", data="add")],
            [Button.url("💻 المطور", "https://t.me/xx44g")]
        ]
        await event.edit(f"👋 مرحبًا بك في بوت إدارة الحسابات.\n\nعدد الحسابات المضافة حاليًا: {num_accounts}", buttons=buttons)

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

@client.on(events.NewMessage(func=lambda event: event.is_private and event.sender_id != allowed_id))
async def forward_to_bot(event):
    accounts = db.get("accounts")
    for account in accounts:
        if event.sender_id == account["phone_number"]:  # Forward message to bot if received on the added account
            await bot.send_message(
                allowed_id, 
                f"📨 رسالة جديدة من الحساب {account['phone_number']}:\n\n"
                f"👤 المستخدم: {event.sender_id}\n"
                f"✉️ الرسالة: {event.text}",
                buttons=[Button.inline("✏️ رد", data=f"reply_{event.sender_id}_{account['phone_number']}")]
            )

@client.on(events.callbackquery.CallbackQuery(pattern=r"reply_(\d+)_(\d+)"))
async def reply_to_user(event):
    sender_id = int(event.pattern_match.group(1))
    phone_number = event.pattern_match.group(2)

    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("✏️ اكتب الرسالة التي تود إرسالها:")
        reply_message = await conv.get_response()

        accounts = db.get("accounts")
        account = next(acc for acc in accounts if acc['phone_number'] == phone_number)
        client = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
        await client.start()

        await client.send_message(sender_id, reply_message.text)
        await conv.send_message("✅ تم إرسال الرد بنجاح.")

        await client.disconnect()

client.run_until_disconnected()
