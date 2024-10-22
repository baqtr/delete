import random
from telethon import Button

@client.on(events.callbackquery.CallbackQuery(data="account_settings"))
async def select_account(event):
    user_id = event.chat_id
    
    # جلب الحسابات من قاعدة البيانات
    accounts = db.get("accounts")
    
    if len(accounts) == 0:
        await event.edit("لا يوجد حسابات مسجلة.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
        return

    buttons = [[Button.inline(f"ترتيب حساب {acc['phone_number']}", data=f"account_settings_{acc['phone_number']}")] for acc in accounts]
    buttons.append([Button.inline("🔙 رجوع", data="back")])
    
    await event.edit("اختر الحساب الذي تود ترتيبه:", buttons=buttons)

@client.on(events.callbackquery.CallbackQuery(data=re.compile(r"account_settings_")))
async def arrange_account(event):
    user_id = event.chat_id
    phone_number = event.data.split("_")[1]  # استخراج رقم الهاتف من زر الحساب المختار
    
    # جلب session المرتبطة بالحساب المختار من قاعدة البيانات
    accounts = db.get("accounts")
    session_string = None
    for acc in accounts:
        if acc["phone_number"] == phone_number:
            session_string = acc["session"]
            break
    
    if session_string is None:
        await event.edit("لم يتم العثور على هذا الحساب.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
        return

    app = TelegramClient(StringSession(session_string), API_ID, API_HASH)
    await app.connect()

    try:
        # اختيار قيم عشوائية لتحديث الحساب
        photo = random.randint(2, 41)
        name = random.randint(2, 41)
        bio = random.randint(1315, 34171)

        # جلب البيانات من القنوات
        msg = await app.get_messages("botnasheravtar", photo)
        msg1 = await app.get_messages("botnashername", name)
        file = await app.download_media(msg)
        msg3 = await app.get_messages("UURRCC", bio)

        # تحديث الملف الشخصي بالبيانات الجديدة
        await app.set_profile_photo(photo=file)
        await app.update_profile(first_name=msg1.text)
        await app.update_profile(about=msg3.text)

        # إرسال رسالة نجاح
        await event.edit("- تم ترتيب الحساب بنجاح -", buttons=[[Button.inline("🔙 رجوع", data="back")]])
        await app.disconnect()
    
    except Exception as e:
        # معالجة الأخطاء إن وجدت
        print(e)
        await event.edit("حدث خطأ أثناء ترتيب الحساب.", buttons=[[Button.inline("🔙 رجوع", data="back")]])
        await app.disconnect()
