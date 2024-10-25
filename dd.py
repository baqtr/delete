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

API_ID = "21669021"
API_HASH = "bcdae25b210b2cbe27c03117328648a2"
admin = 7013440973
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
    accounts = db.get("accounts")
    account_count = len(accounts)

    buttons = [
        [Button.inline("➕ إضافة حساب", data="add")],
        [Button.inline(f"📂 حساباتك ({account_count})", data="account_list")]
    ]
    await event.respond("👋 أهلاً بك! هذا البوت مخصص لإدارة حسابات تيليجرام. اختر من الأزرار أدناه:", buttons=buttons)


@client.on(events.callbackquery.CallbackQuery())
async def callback_handler(event):
    data = event.data.decode('utf-8') if isinstance(event.data, bytes) else str(event.data)
    user_id = event.chat_id

    if data == "add":
        await event.edit("✔️الان ارسل رقمك مع رمز دولتك , مثال :+201000000000")
        txt = await event.get_response()
        phone_number = txt.text.replace("+", "").replace(" ", "")

        accounts = db.get("accounts")
        if any(account['phone_number'] == phone_number for account in accounts):
            await event.edit("- هذا الحساب تم إضافته مسبقًا.")
            return

        app = TelegramClient(StringSession(), API_ID, API_HASH)
        await app.connect()
        password = None
        try:
            await app.send_code_request(phone_number)
        except (ApiIdInvalidError):
            await event.edit("ʏᴏᴜʀ **API_ID** ᴀɴᴅ **API_HASH** ɪs ɪɴᴠᴀʟɪᴅ.")
            return
        except (PhoneNumberInvalidError):
            await event.edit("ᴛʜᴇ **ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ** ʏᴏᴜ'ᴠᴇ sᴇɴᴛ ɪs ɪɴᴠᴀʟɪᴅ.")
            return
        await event.edit("- تم ارسال كود التحقق الخاص بك علي تليجرام. أرسل الكود بالتنسيق التالي : 1 2 3 4 5")
        txt = await event.get_response()
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
            return
        except (PhoneCodeExpiredError):
            await event.edit("الكود المدخل منتهي الصلاحية.")
            return
        except (SessionPasswordNeededError):
            await event.edit("- أرسل رمز التحقق بخطوتين الخاص بحسابك")
            txt = await event.get_response()
            password = txt.text
            try:
                await app.sign_in(password=password)
            except (PasswordHashInvalidError):
                await event.edit("رمز التحقق بخطوتين المدخل غير صحيح.")
                return
            string_session = app.session.save()
            data = {"phone_number": phone_number, "two-step": password, "session": string_session}
            accounts.append(data)
            db.set("accounts", accounts)
            await event.edit("- تم حفظ الحساب بنجاح ✅")

    elif data == "account_list":
        acc = db.get("accounts")
        if len(acc) == 0:
            await event.edit("- لا يوجد حسابات مسجلة.")
            return

        buttons = [[Button.inline(f"📱 {i['phone_number']}", data=f"account_{i['phone_number']}")] for i in acc]
        buttons.append([Button.inline("↩️ رجوع", data="start")])
        await event.edit("- اختر الحساب للتحكم فيه:", buttons=buttons)

    elif data.startswith("account_"):
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
                       f"- التحقق بخطوتين : {i['two-step']}\n"

                buttons = [
                    [Button.inline("🧹 تنظيف المحادثات", data=f"clean_{phone_number}")],
                    [Button.inline("🔒 تسجيل خروج", data=f"logout_{phone_number}")],
                    [Button.inline("📩 جلب الكود", data=f"code_{phone_number}")],
                    [Button.inline("↩️ رجوع", data="account_list")]
                ]
                await event.edit(text, buttons=buttons)
                await app.disconnect()

    elif data.startswith("clean_"):
        phone_number = data.split("_")[1]
        acc = db.get("accounts")
        for i in acc:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()

                deleted_count = 0
                async for dialog in app.iter_dialogs():
                    await app.delete_dialog(dialog.id)
                    deleted_count += 1
                    await event.edit(f"- جاري تنظيف المحادثات... تم حذف {deleted_count}")

                await event.edit(f"- تم تنظيف جميع المحادثات بنجاح ✅\n- المحادثات المحذوفة: {deleted_count}")
                await app.disconnect()

    elif data.startswith("logout_"):
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

    elif data.startswith("code_"):
        phone_number = data.split("_")[1]
        acc = db.get("accounts")
        for i in acc:
            if phone_number == i['phone_number']:
                app = TelegramClient(StringSession(i['session']), API_ID, API_HASH)
                await app.connect()
                code = await app.get_messages(777000, limit=1)
                await event.edit(f"اخر كود تم استلامه: {code[0].message}")
                await app.disconnect()

client.run_until_disconnected()
