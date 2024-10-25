import os
from telethon.tl import functions
from telethon.sessions import StringSession
import asyncio
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

# إعدادات Telegram API
API_ID = "21669021"
API_HASH = "bcdae25b210b2cbe27c03117328648a2"
admin = 7013440973
token = "7464446606:AAFb6FK5oAwLEiuDCftx2cA2jfSBPsyJjj8"

client = TelegramClient('BotSession', API_ID, API_HASH).start(bot_token=token)
db = uu('database/elhakem.ss', 'bot')

if not db.exists("accounts"):
    db.set("accounts", [])

async def update_buttons(event, text, buttons):
    await event.edit(text, buttons=buttons)

@client.on(events.NewMessage(pattern="/start", func=lambda x: x.is_private))
async def start(event):
    accounts = db.get("accounts")
    account_count = len(accounts)
    buttons = [
        [Button.inline("➕ إضافة حساب", data="add")],
        [Button.inline(f"📂 حساباتك ({account_count})", data="account_list")]
    ]
    await event.respond("👋 أهلاً بك! هذا البوت مخصص لإدارة حسابات تيليجرام. اختر من الأزرار أدناه:", buttons=buttons)

@client.on(events.callbackquery.CallbackQuery())
async def handle_callback(event):
    data = event.data.decode('utf-8')
    user_id = event.chat_id

    if data == "add":
        async with bot.conversation(event.chat_id) as conv:
            msg = await update_buttons(event, "✔️الآن أرسل رقمك مع رمز الدولة، مثال: +201000000000", [])
            phone_number = (await conv.get_response()).text.replace("+", "").replace(" ", "")
            accounts = db.get("accounts")
            
            if any(account['phone_number'] == phone_number for account in accounts):
                await msg.edit("- هذا الحساب تم إضافته مسبقًا.")
                await asyncio.sleep(2)
                await start(event)
                return

            app = TelegramClient(StringSession(), API_ID, API_HASH)
            await app.connect()

            try:
                await app.send_code_request(phone_number)
                await msg.edit("- تم إرسال كود التحقق، أرسل الكود بالتنسيق: 1 2 3 4 5")
            except (ApiIdInvalidError, PhoneNumberInvalidError):
                await msg.edit("❌ خطأ: API_ID أو رقم الهاتف غير صحيح.")
                await asyncio.sleep(2)
                await start(event)
                return

            code = (await conv.get_response()).text.replace(" ", "")
            try:
                await app.sign_in(phone_number, code)
                string_session = app.session.save()
                data = {"phone_number": phone_number, "two-step": "لا يوجد", "session": string_session}
                accounts.append(data)
                db.set("accounts", accounts)
                await msg.edit("- تم حفظ الحساب بنجاح ✅")
            except PhoneCodeInvalidError:
                await msg.edit("❌ الكود المدخل غير صحيح.")
                await asyncio.sleep(2)
                await start(event)
                return
            except PhoneCodeExpiredError:
                await msg.edit("❌ الكود المدخل منتهي الصلاحية.")
                await asyncio.sleep(2)
                await start(event)
                return
            except SessionPasswordNeededError:
                await msg.edit("- أرسل رمز التحقق بخطوتين الخاص بحسابك")
                password = (await conv.get_response()).text
                try:
                    await app.sign_in(password=password)
                except PasswordHashInvalidError:
                    await msg.edit("❌ رمز التحقق بخطوتين غير صحيح.")
                    await asyncio.sleep(2)
                    await start(event)
                    return
                string_session = app.session.save()
                data["two-step"] = password
                db.set("accounts", accounts)
                await msg.edit("- تم حفظ الحساب بنجاح ✅")

            await asyncio.sleep(2)
            await start(event)

    elif data == "account_list":
        accounts = db.get("accounts")
        if not accounts:
            await update_buttons(event, "- لا يوجد حسابات مسجلة.", [])
            await asyncio.sleep(2)
            await start(event)
            return
        buttons = [[Button.inline(f"📱 {acc['phone_number']}", data=f"account_{acc['phone_number']}")] for acc in accounts]
        await update_buttons(event, "- اختر الحساب للتحكم فيه:", buttons)

    elif data.startswith("account_"):
        phone_number = data.split("_")[1]
        account = next((acc for acc in db.get("accounts") if acc['phone_number'] == phone_number), None)
        if account:
            app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
            await app.connect()
            me = await app.get_me()
            sessions = await app(functions.account.GetAuthorizationsRequest())
            device_count = len(sessions.authorizations)
            text = (f"• رقم الهاتف : {phone_number}\n"
                    f"- الاسم : {me.first_name} {me.last_name or ''}\n"
                    f"- عدد الاجهزة المتصلة : {device_count}\n"
                    f"- التحقق بخطوتين : {account['two-step']}\n"
                    f"- الجلسة : `{account['session']}`")
            buttons = [
                [Button.inline("🧹 تنظيف المحادثات", data=f"clean_{phone_number}")],
                [Button.inline("🔒 تسجيل خروج", data=f"logout_{phone_number}")],
                [Button.inline("📩 جلب الكود", data=f"code_{phone_number}")]
            ]
            await update_buttons(event, text, buttons)
            await app.disconnect()

    elif data.startswith("clean_"):
        phone_number = data.split("_")[1]
        account = next((acc for acc in db.get("accounts") if acc['phone_number'] == phone_number), None)
        if account:
            app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
            await app.connect()
            deleted_count = 0
            msg = await event.edit(f"🔄 جارٍ الحذف، العدد الحالي: {deleted_count}")
            async for dialog in app.iter_dialogs():
                await app.delete_dialog(dialog.id)
                deleted_count += 1
                await msg.edit(f"🔄 جارٍ الحذف، العدد الحالي: {deleted_count}")
            await msg.edit("✅ تم تنظيف جميع المحادثات بنجاح.")
            await app.disconnect()

    elif data.startswith("logout_"):
        phone_number = data.split("_")[1]
        accounts = db.get("accounts")
        account = next((acc for acc in accounts if acc['phone_number'] == phone_number), None)
        if account:
            app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
            await app.connect()
            await app.log_out()
            await app.disconnect()
            accounts.remove(account)
            db.set("accounts", accounts)
            await event.edit(f"✅ تم تسجيل الخروج من الحساب: {phone_number}")
            await asyncio.sleep(2)
            await start(event)

    elif data.startswith("code_"):
        phone_number = data.split("_")[1]
        account = next((acc for acc in db.get("accounts") if acc['phone_number'] == phone_number), None)
        if account:
            app = TelegramClient(StringSession(account['session']), API_ID, API_HASH)
            await app.connect()
            code = await app.get_messages(777000, limit=1)
            await event.edit(f"📩 آخر كود تم استلامه: {code[0].message}")
            await app.disconnect()

client.run_until_disconnected()
