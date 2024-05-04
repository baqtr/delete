import os
import logging
import requests
from github import Github
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, ConversationHandler, MessageHandler, Filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TELEGRAM_TOKEN = "7105215342:AAG4XYWMw1twnP69cEgGxHLCQKlo2527FnY"
GITHUB_TOKEN = "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"
HEROKU_API_KEY = "HRKU-354b0fc4-1af5-4c26-91a5-9c09166d5eee"
ADMIN_ID = "7013440973"

PASSWORD, MAIN_MENU = range(2)

def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("الرجاء إدخال كلمة المرور للمتابعة كل مره تبدا محادثه جديد مع البوت ساطلبه منك ♾️")
    return PASSWORD

def verify_password(update: Update, context: CallbackContext) -> int:
    password = update.message.text.strip()
    if password == "محمد تناحه":
        heroku_apps_count = get_heroku_apps_count()
        github_repos_count = get_github_repositories_count()

        update.message.reply_text(
            f"مرحبًا {update.message.from_user.first_name}!\n\n"
            f"الخوادم التي يتم تشغيلها ✅ حاليًا على VPS: {heroku_apps_count}\n"
            f"المستودعات ✅ حاليًا على GitHub: {github_repos_count}\n\n"
            "يمكنك حذف مستودع أو خادم عن طريق النقر على الزر المناسب.",
            reply_markup=get_main_keyboard()
        )
        return MAIN_MENU
    else:
        update.message.reply_text("كلمة المرور غير صحيحة. يرجى المحاولة مرة أخرى.")
        return PASSWORD

def get_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("عرض الخوادم VPS", callback_data='heroku_apps')],
        [InlineKeyboardButton("عرض مستودعات GitHub", callback_data='github_repos')],
    ]
    return InlineKeyboardMarkup(keyboard)

def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == 'heroku_apps':
        apps_list = get_heroku_apps()
        if apps_list:
            buttons = [[InlineKeyboardButton(app, callback_data=f'heroku_app_{app}')] for app in apps_list]
            buttons.append([InlineKeyboardButton("رجوع", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(buttons)
            query.edit_message_text("الرجاء اختيار الخادم الذي تريد حذفه:", reply_markup=reply_markup)
        else:
            query.edit_message_text("لا توجد خوادم متاحة حاليًا على VPS.")

    elif query.data == 'github_repos':
        repos_list = get_github_repos()
        if repos_list:
            buttons = [[InlineKeyboardButton(repo, callback_data=f'github_repo_{repo}')] for repo in repos_list]
            buttons.append([InlineKeyboardButton("رجوع", callback_data='back')])
            reply_markup = InlineKeyboardMarkup(buttons)
            query.edit_message_text("الرجاء اختيار المستودع الذي تريد حذفه:", reply_markup=reply_markup)
        else:
            query.edit_message_text("لا توجد مستودعات متاحة حاليًا على GitHub.")

    elif query.data.startswith('heroku_app_'):
        app_name = query.data[len('heroku_app_'):]
        result = delete_heroku_app(app_name)
        if result:
            query.edit_message_text(f"تم حذف الخادم {app_name} بنجاح ✅")
        else:
            query.edit_message_text(f"تم حذف الخادم {app_name} ⚠️")

    elif query.data.startswith('github_repo_'):
        repo_name = query.data[len('github_repo_'):]
        result = delete_github_repository(repo_name)
        if result:
            query.edit_message_text(f"تم حذف المستودع '{repo_name}' بنجاح ✅")
        else:
            query.edit_message_text(f"فشل في حذف المستودع '{repo_name}' ⚠️")

    elif query.data == 'back':
        start(update.callback_query.message, context)

def get_heroku_apps_count() -> int:
    headers = {
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.get("https://api.heroku.com/apps", headers=headers)
    if response.status_code == 200:
        return len(response.json())
    return 0

def get_github_repositories_count() -> int:
    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    repos = user.get_repos()
    return repos.totalCount

def get_heroku_apps() -> list:
    headers = {
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.get("https://api.heroku.com/apps", headers=headers)
    if response.status_code == 200:
        return [app['name'] for app in response.json()]
    return []

def get_github_repos() -> list:
    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    repos = user.get_repos()
    return [repo.name for repo in repos]

def delete_heroku_app(name: str) -> bool:
    headers = {
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.delete(f"https://api.heroku.com/apps/{name}", headers=headers)
    return response.status_code == 202

def delete_github_repository(name: str) -> bool:
    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    try:
        repo = user.get_repo(name)
        repo.delete()
        return True
    except Exception:
        return False

def main() -> None:
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_click))
    dp.add_handler(MessageHandler(Filters.text & Filters.private & ~Filters.command, verify_password))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
