import random
from pyrogram.types import InlineKeyboardMarkup as Markup, InlineKeyboardButton as Button

@app.on_callback_query(filters.regex("^account_settings$"))
async def select_account(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    
    # تأكد من أن المستخدم لديه حسابات مخزنة
    if str(user_id) in users and "session" in users[str(user_id)]:
        # عرض الحسابات للمستخدم لاختيار واحد منها
        accounts = users[str(user_id)]["accounts"]
        
        if len(accounts) == 0:
            await callback.message.edit_text(
                "لا يوجد حسابات مسجلة.",
                reply_markup=Markup([[Button("- رجوع -", callback_data="toHome")]])
            )
            return
        
        buttons = [[Button(f"ترتيب حساب {acc['phone']}", callback_data=f"account_settings_{acc['phone']}")] for acc in accounts]
        buttons.append([Button("- رجوع -", callback_data="toHome")])
        
        await callback.message.edit_text(
            "اختر الحساب الذي تود ترتيبه:",
            reply_markup=Markup(buttons)
        )
    else:
        await callback.message.edit_text(
            "لا يوجد حسابات متاحة.",
            reply_markup=Markup([[Button("- رجوع -", callback_data="toHome")]])
        )

@app.on_callback_query(filters.regex("^account_settings_"))
async def toHome(client: Client, callback: CallbackQuery):
    user_id = callback.from_user.id
    phone = callback.data.split("_")[2]  # استخراج رقم الهاتف من زر الحساب المختار
    
    # الحصول على session المرتبطة بالحساب المختار
    session_string = users[str(user_id)]["accounts"][phone]["session"]
    
    client = Client(
        str(user_id),
        api_id=app.api_id,
        api_hash=app.api_hash,
        session_string=session_string
    )
    await client.start()
    
    try:
        # اختيار قيم عشوائية لتحديث الحساب
        photo = random.randint(2, 41)
        name = random.randint(2, 41)
        bio = random.randint(1315, 34171)
        username = get_random_username()

        # جلب البيانات من القنوات
        msg = await client.get_messages("botnasheravtar", photo)
        msg1 = await client.get_messages("botnashername", name)
        file = await client.download_media(msg)
        msg3 = await client.get_messages("UURRCC", bio)

        # تحديث الملف الشخصي بالبيانات الجديدة
        await client.set_profile_photo(photo=file)
        await client.update_profile(first_name=msg1.text)
        await client.update_profile(bio=msg3.text)

        # إرسال رسالة نجاح
        await callback.message.edit_text(
            "- تم ترتيب الحساب بنجاح -",
            reply_markup=Markup([[Button("- رجوع -", callback_data="toHome")]])
        )
        await client.stop()
        return True
    
    except Exception as e:
        # معالجة الأخطاء إن وجدت
        print(e)
        await client.stop()
        await callback.message.edit_text(
            "حدث خطأ أثناء ترتيب الحساب.",
            reply_markup=Markup([[Button("- رجوع -", callback_data="toHome")]])
        )
        return False
