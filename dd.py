import os
from telethon.tl import functions
from telethon.sessions import StringSession
import asyncio, json
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
    await event.respond("👋 أهلاً بك! هذا البوت مخصص لإدارة حسابات تيليجرام. اختر من الأزرار أدناه:", buttons=buttons)
    await event.message.delete()

@client.on(events.callbackquery.CallbackQuery())
async def start_lis(event):
    data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
    user_id = event.chat_id

    if data == "add":
        async with bot.conversation(event.chat_id) as x:
            await x.send_message("✔️الان ارسل رقمك مع رمز دولتك , مثال :+201000000000")
            txt = await x.get_response()
            phone_number = txt.text.replace("+", "").replace(" ", "")
            accounts = db.get("accounts")
            
            if any(account['phone_number'] == phone_number for account in accounts):
                await event.edit("- هذا الحساب تم إضافته مسبقًا.")
                await asyncio.sleep(2)
                await event.delete()
                await start(event)
                return

            app = TelegramClient(StringSession(), API_ID, API_HASH)
            await app.connect()
            password = None
            try:
                await app.send_code_request(phone_number)
            except (ApiIdInvalidError):
                await event.edit("ʏᴏᴜʀ **API_ID** ᴀɴᴅ **API_HASH** ɪs ɪɴᴠᴀʟɪᴅ.")
                await asyncio.sleep(2)
                await event.delete()
                await start(event)
                return
            except (PhoneNumberInvalidError):
                await event.edit("ᴛʜᴇ **ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ** ʏᴏᴜ'ᴠᴇ sᴇɴᴛ ɪs ɪɴᴠᴀʟɪᴅ.")
                await asyncio.sleep(2)
                await event.delete()
                await start(event)
                return
            
            await event.edit("- تم ارسال كود التحقق الخاص بك علي تليجرام. أرسل الكود بالتنسيق التالي : 1 2 3 4 5")
            txt = await x.get_response()
            code = txt.text.replace(" ", "")
            try:
                await app.sign_in(phone_number, code, password=None)
                string_session = app.session.save()
                data = {"phone_number": phone_number, "two-step": "لا يوجد", "session": string_session}
                accounts.append(data)
                db.set("accounts", accounts)
                await event.edit("- تم حفظ الحساب بنجاح ✅")
            except (PhoneCodeInvalidError):
                await event.edit("الكود المدخل غير صحيح.")
                await asyncio.sleep(2)
                await event.delete()
                await start(event)
                return
            except (PhoneCodeExpiredError):
                await event.edit("الكود المدخل منتهي الصلاحية.")
                await asyncio.sleep(2)
                await event.delete()
                await start(event)
                return
            except (SessionPasswordNeededError):
                await event.edit("- أرسل رمز التحقق بخطوتين الخاص بحسابك")
                txt = await x.get_response()
                password = txt.text
                try:
                    await app.sign_in(password=password)
                except (PasswordHashInvalidError):
                    await event.edit("رمز التحقق بخطوتين المدخل غير صحيح.")
                    await asyncio.sleep(2)
                    await event.delete()
                    await start(event)
                    return
                string_session = app.session.save()
                data = {"phone_number": phone_number, "two-step": password, "session": string_session}
                accounts.append(data)
                db.set("accounts", accounts)
                await event.edit("- تم حفظ الحساب بنجاح ✅")

            await asyncio.sleep(2)
            await event.delete()
            await start(event)

    if data == "account_list":
        acc = db.get("accounts")
        if len(acc) == 0:
            await event.edit("- لا يوجد حسابات مسجلة.")
            await asyncio.sleep(2)
            await event.delete()
            await start(event)
            return

        buttons = [[Button.inline(f"📱 {i['phone_number']}", data=f"account_{i['phone_number']}")] for i in acc]
        buttons.append([Button.inline("⬅️ رجوع", data="back")])
        await event.edit("- اختر الحساب للتحكم فيه:", buttons=buttons)

    if data.startswith("account_"):
        phone_number = data.split("_")[1]
        acc = db.get("accounts")
        for i in acc:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()

                me = await app.get_me()
                sessions = await app(functions.account.GetAuthorizationsRequest())
                device_count = len(sessions.authorizations)

                text = f"• رقم الهاتف : {phone_number}\n" \
                       f"- الاسم : {me.first_name} {me.last_name or ''}\n" \
                       f"- عدد الاجهزة المتصلة : {device_count}\n" \
                       f"- التحقق بخطوتين : {i['two-step']}\n" \
                       f"- الجلسة : `{i['session']}`"

                buttons = [
                    [Button.inline("🔄 تحديث الجلسة", data=f"refresh_{phone_number}")],
                    [Button.inline("🔒 تسجيل خروج", data=f"logout_{phone_number}")],
                    [Button.inline("📩 جلب الكود", data=f"code_{phone_number}")],
                    [Button.inline("⬅️ رجوع", data="account_list")]
                ]
                await event.edit(text, buttons=buttons)
                await app.disconnect()

    if data.startswith("refresh_"):
        phone_number = data.split("_")[1]
        acc = db.get("accounts")
        for i in acc:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()
                me = await app.get_me()
                await event.edit(f"تم تحديث بيانات الحساب:\n\n- الاسم: {me.first_name} {me.last_name or ''}")
                await app.disconnect()

    if data.startswith("logout_"):
        phone_number = data.split("_")[1]
        acc = db.get("accounts")
        for i in acc:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()
                await app.log_out()
                await app.disconnect()

                acc.remove(i)
                db.set("accounts", acc)

                await event.edit(f"- تم تسجيل الخروج من الحساب: {phone_number}")
                await asyncio.sleep(2)
                await event.delete()
                await start(event)

    if data.startswith("code_"):
        phone_number = data.split("_")[1]
        acc = db.get("accounts")
        for i in acc:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()
                code = await app.get_messages(777000, limit=1)
                await event.edit(f"اخر كود تم استلامه: {code[0].message}", buttons=[[Button.inline("⬅️ رجوع", data=f"account_{phone_number}")]])
                await app.disconnect()

    if data == "back":
        await start(event)

client.run_until_disconnected()
