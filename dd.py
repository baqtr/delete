import os
import logging
import requests
from github import Github
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "7105215342:AAG4XYWMw1twnP69cEgGxHLCQKlo2527FnY"
GITHUB_TOKEN = "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"
HEROKU_API_KEY = "HRKU-354b0fc4-1af5-4c26-91a5-9c09166d5eee"
HEROKU_API_KEY = "HRKU-5e86e90f-8222-40b2-9b54-302d63a73e32"
HEROKU_API_KEY = "HRKU-adaf6ee5-26b0-451f-8425-327ad117b05a"
ADMIN_ID = "7013440973"

def start(update: Update, context: CallbackContext) -> None:
    # Get current Heroku apps count and GitHub repositories count
    heroku_apps_count = get_heroku_apps_count()
    github_repos_count = get_github_repositories_count()

    # Prepare welcome message
    welcome_message = (
        f"مرحبًا {update.message.from_user.first_name}!\n\n"
        f"عدد الخوادم التي يتم تشغيلها ✅ حاليًا على VPS:{heroku_apps_count}\n"
        f"عدد المستودعات ✅ حاليًا على GitHub:{github_repos_count}\n\n"
        "يمكنك حذف مستودع أو خادم عن طريق إرسال اسمه."
    )

    # Add Telegram link button
    inline_keyboard = [[InlineKeyboardButton("المطور موهان ♨️", url="https://t.me/XX44G")]]
    reply_markup = InlineKeyboardMarkup(inline_keyboard)

    # Send welcome message with current counts and Telegram link button
    update.message.reply_text(welcome_message, reply_markup=reply_markup)

def delete_repository_or_app(update: Update, context: CallbackContext) -> None:
    # Get the name to delete
    name_to_delete = update.message.text.strip()

    # Check if it's a repository or an app
    if is_heroku_app(name_to_delete):
        # Delete Heroku app
        result = delete_heroku_app(name_to_delete)
        if result:
            update.message.reply_text(f"تم حذف الخادم {name_to_delete} بنجاح ✅")
        else:
            update.message.reply_text(f"تم حذف الخادم {name_to_delete} بنجاح ✅")
    elif is_github_repository(name_to_delete):
        # Delete GitHub repository
        result = delete_github_repository(name_to_delete)
        if result:
            update.message.reply_text(f"تم حذف المستودع '{name_to_delete}' بنجاح ✅")
        else:
            update.message.reply_text(f"تعذر حذف المستودع '{name_to_delete}' ⚠️")
    else:
        update.message.reply_text(" لم يتم العثور على مستودع أو خادم بهذا الاسم. يرجى التأكد من الاسم وإعادة المحاولة.")

def is_heroku_app(name: str) -> bool:
    # Check if the app exists on Heroku
    headers = {
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.get(f"https://api.heroku.com/apps/{name}", headers=headers)
    return response.status_code == 200

def is_github_repository(name: str) -> bool:
    # Check if the repository exists on GitHub
    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    try:
        user.get_repo(name)
        return True
    except Exception:
        return False

def delete_heroku_app(name: str) -> bool:
    # Delete the Heroku app
    headers = {
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.delete(f"https://api.heroku.com/apps/{name}", headers=headers)
    return response.status_code == 202

def delete_github_repository(name: str) -> bool:
    # Delete the GitHub repository
    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    try:
        repo = user.get_repo(name)
        repo.delete()
        return True
    except Exception:
        return False

def get_heroku_apps_count() -> int:
    # Get the count of Heroku apps
    headers = {
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3"
    }
    response = requests.get("https://api.heroku.com/apps", headers=headers)
    if response.status_code == 200:
        return len(response.json())
    return 0

def get_github_repositories_count() -> int:
    # Get the count of GitHub repositories
    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    repos = user.get_repos()
    return repos.totalCount

def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & Filters.private & ~Filters.command, delete_repository_or_app))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
