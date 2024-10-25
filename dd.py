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

if not os.path.isdir('database'):
    os.mkdir('database')

API_ID = "21669021"
API_HASH = "bcdae25b210b2cbe27c03117328648a2"
admin = 7013440973
token = "7464446606:AAFb6FK5oAwLEiuDCftx2cA2jfSBPsyJjj8"
client = TelegramClient('BotSession', API_ID, API_HASH).start(bot_token=token)
bot = client

db = uu('database/elhakem.ss', 'bot')

if not db.exists("accounts"):
    db.set("accounts", [])

@client.on(events.NewMessage(pattern="/start", func=lambda x: x.is_private))
async def start(event):
    user_id = event.chat_id
    accounts = db.get("accounts")
    account_count = len(accounts)
    buttons = [
        [Button.inline("➕ إضافة حساب", data="add")],
        [Button.inline(f"📂 حساباتك ({account_count})", data="account_list")]
    ]
    await event.reply("👋 أهلاً بك! هذا البوت مخصص لإدارة حسابات تيليجرام. اختر من الأزرار أدناه:", buttons=buttons)

@client.on(events.callbackquery.CallbackQuery())
async def handle_event(event):
    data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
    user_id = event.chat_id

    if data == "add":
        await event.edit("✔️الان ارسل رقمك مع رمز دولتك , مثال :+201000000000", buttons=[[Button.inline("🔙 رجوع", data="start")]])
        async with bot.conversation(event.chat_id) as conv:
            phone_number = (await conv.get_response()).text.replace("+", "").replace(" ", "")
            accounts = db.get("accounts")
            if any(account['phone_number'] == phone_number for account in accounts):
                await event.edit("- هذا الحساب تم إضافته مسبقًا.", buttons=[[Button.inline("🔙 رجوع", data="start")]])
                return
            app = TelegramClient(StringSession(), API_ID, API_HASH)
            await app.connect()
            try:
                await app.send_code_request(phone_number)
                await event.edit("تم ارسال كود التحقق. أرسل الكود بالتنسيق التالي : 1 2 3 4 5", buttons=[[Button.inline("🔙 رجوع", data="start")]])
                code = (await conv.get_response()).text.replace(" ", "")
                await app.sign_in(phone_number, code)
                string_session = app.session.save()
                accounts.append({"phone_number": phone_number, "two-step": "لا يوجد", "session": string_session})
                db.set("accounts", accounts)
                await event.edit("- تم حفظ الحساب بنجاح ✅", buttons=[[Button.inline("🔙 رجوع", data="start")]])
            except (ApiIdInvalidError, PhoneNumberInvalidError, PhoneCodeInvalidError, PhoneCodeExpiredError, SessionPasswordNeededError, PasswordHashInvalidError):
                await event.edit("حدث خطأ في تسجيل الدخول. تأكد من التفاصيل.", buttons=[[Button.inline("🔙 رجوع", data="start")]])

    elif data == "account_list":
        acc = db.get("accounts")
        if not acc:
            await event.edit("- لا يوجد حسابات مسجلة.", buttons=[[Button.inline("🔙 رجوع", data="start")]])
            return
        buttons = [[Button.inline(f"📱 {i['phone_number']}", data=f"account_{i['phone_number']}")] for i in acc]
        buttons.append([Button.inline("🔙 رجوع", data="start")])
        await event.edit("- اختر الحساب للتحكم فيه:", buttons=buttons)

    elif data.startswith("account_"):
        phone_number = data.split("_")[1]
        account = next((acc for acc in db.get("accounts") if acc['phone_number'] == phone_number), None)
        if account:
            app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
            await app.connect()
            me = await app.get_me()
            sessions = await app(functions.account.GetAuthorizationsRequest())
            device_count = len(sessions.authorizations)
            text = f"• رقم الهاتف : {phone_number}\n" \
                   f"- الاسم : {me.first_name} {me.last_name or ''}\n" \
                   f"- عدد الاجهزة المتصلة : {device_count}\n" \
                   f"- التحقق بخطوتين : {account['two-step']}\n" \
                   f"- الجلسة : `{account['session']}`"
            buttons = [
                [Button.inline("🧹 تنظيف المحادثات", data=f"clean_{phone_number}")],
                [Button.inline("🔒 تسجيل خروج", data=f"logout_{phone_number}")],
                [Button.inline("📩 جلب الكود", data=f"code_{phone_number}")],
                [Button.inline("🔙 رجوع", data="account_list")]
            ]
            await event.edit(text, buttons=buttons)
            await app.disconnect()

    elif data.startswith("clean_"):
        phone_number = data.split("_")[1]
        account = next((acc for acc in db.get("accounts") if acc['phone_number'] == phone_number), None)
        if account:
            app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
            await app.connect()
            count_deleted = 0
            async for dialog in app.iter_dialogs():
                await app.delete_dialog(dialog.id)
                count_deleted += 1
                await event.edit(f"جاري حذف المحادثات. تم حذف ({count_deleted}) حتى الآن.", buttons=[[Button.inline("🔙 رجوع", data=f"account_{phone_number}")]])
            await event.edit(f"✅ تم تنظيف جميع المحادثات بنجاح! العدد الإجمالي: {count_deleted}", buttons=[[Button.inline("🔙 رجوع", data=f"account_{phone_number}")]])
            await app.disconnect()

    elif data.startswith("logout_"):
        phone_number = data.split("_")[1]
        account = next((acc for acc in db.get("accounts") if acc['phone_number'] == phone_number), None)
        if account:
            app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
            await app.connect()
            await app.log_out()
            await app.disconnect()
            db.set("accounts", [acc for acc in db.get("accounts") if acc['phone_number'] != phone_number])
            await event.edit(f"- تم تسجيل الخروج من الحساب: {phone_number}", buttons=[[Button.inline("🔙 رجوع", data="account_list")]])

    elif data.startswith("code_"):
        phone_number = data.split("_")[1]
        account = next((acc for acc in db.get("accounts") if acc['phone_number'] == phone_number), None)
        if account:
            app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
            await app.connect()
            code = await app.get_messages(777000, limit=1)
            await event.edit(f"اخر كود تم استلامه: {code[0].message}", buttons=[[Button.inline("🔙 رجوع", data=f"account_{phone_number}")]])
            await app.disconnect()

    elif data == "start":
        await start(event)

client.run_until_disconnected()
