
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from deep_translator import GoogleTranslator
import time
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ConversationHandler
from concurrent.futures import ThreadPoolExecutor
import json
import os
import logging
import requests
from bs4 import BeautifulSoup
import sys

TOKEN = 'YOUR_BOT_TOKEN'


TRANSLATE, ARTICLE, WAIT_FOR_ACTION, TRANSLATE_FA2DE = range(4)

ARTICLE_CACHE_FILE = 'article_cache.json'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_user_activity(user_id, username, activity_type, message_text):
    with open("user_activities.log", "a", encoding='utf-8') as file:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp} - UserID: {user_id} - Username: {username} - Activity: {activity_type} - Message: {message_text}\n"
        file.write(log_entry)

def load_article_cache():
    if os.path.exists(ARTICLE_CACHE_FILE):
        with open(ARTICLE_CACHE_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def save_article_cache(data):
    with open(ARTICLE_CACHE_FILE, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

article_cache = load_article_cache()

def search_word_in_website(search_term):
    """جستجو و استخراج نتایج از وب‌سایت بدون نیاز به ChromeDriver."""
    url = "https://der-artikel.de/der/Finder.html"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    }

    try:
        response = requests.post(url, headers=headers, data={'word': search_term})
        response.raise_for_status()  

        soup = BeautifulSoup(response.text, 'html.parser')

        results = {}
        rows = soup.select('.table tbody tr')

        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                type_of_case = cells[0].get_text(strip=True)
                singular = cells[1].get_text(strip=True)
                plural = cells[2].get_text(strip=True)
                if type_of_case in ['NOMINATIV', 'GENITIV', 'DATIV', 'AKKUSATIV']:
                    results[type_of_case] = {
                        'Singular': singular,
                        'Plural': plural
                    }

        return results

    except requests.exceptions.RequestException as e:
        logging.error(f"خطا در جستجو: {e}")
        return {}

ARTICLE_CACHE_FILE = 'article_cache.json'

article_cache = load_article_cache()

async def start(update: Update, context):
    """ارسال پیام با دکمه‌های متعدد هنگام اجرای دستور /start"""
    try:
        keyboard = [
            [KeyboardButton('ترجمه کلمه یا متن ( DE به IR )'), KeyboardButton('ترجمه کلمه یا متن ( IR به DE )')],
            [KeyboardButton('آرتیکل کلمات')],
            [KeyboardButton('ترجمه صدا'), KeyboardButton('ترجمه عکس')],
            [KeyboardButton('پشتیبانی'), KeyboardButton('آپدیت ربات')]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text('یکی از گزینه‌ها را انتخاب کنید:', reply_markup=reply_markup)
        return ConversationHandler.END
    except Exception as e:
        logging.error(f"خطا در شروع: {e}")


async def handle_reply(update: Update, context):
    """مدیریت پاسخ‌های کاربر براساس دکمه فشرده شده"""
    try:
        text = update.message.text
        user_id = update.message.from_user.id
        username = update.message.from_user.username

        log_user_activity(user_id, username, 'User Reply', text)

        if text == 'ترجمه کلمه یا متن ( DE به IR )':
            await update.message.reply_text("لطفاً کلمه یا متنی را که می‌خواهید ترجمه شود وارد کنید:")
            return TRANSLATE
        elif text == 'ترجمه کلمه یا متن ( IR به DE )':
            await update.message.reply_text("لطفاً کلمه یا متنی را که می‌خواهید ترجمه شود وارد کنید:")
            return TRANSLATE_FA2DE
        elif text == 'ترجمه عکس':
            await update.message.reply_text("در حال حاضر ربات در حال تکمیل می‌باشد و این امکان در دسترس نیست.برروی استارت زیر کلیلک کنید.")
            await update.message.reply_text("/start")
            return ConversationHandler.END
        elif text == 'ترجمه صدا':
            await update.message.reply_text("در حال حاضر ربات در حال تکمیل می‌باشد و این امکان در دسترس نیست. برروی استارت زیر کلیلک کنید.")
            await update.message.reply_text("/start")
            return ConversationHandler.END
        elif text == 'آرتیکل کلمات':
            await update.message.reply_text("لطفاً کلمه‌ای را که می‌خواهید آرتیکل آن نمایش داده شود وارد کنید:")
            return ARTICLE
        elif text == 'پشتیبانی':
            await update.message.reply_text("منتظر نظرات و پیشنهادات شما هستیم: https://t.me/Mehranmoradi13")
        elif text == 'آپدیت ربات':
            await update.message.reply_text("ربات شما به جدیدترین نسخه به روز رسانی شد ♥")
            await start(update, context)  
        return ConversationHandler.END
    except Exception as e:
        logging.error(f"خطا در مدیریت پاسخ: {e}")


TRANSLATION_CACHE_FILE = 'translation_cache.json'

translation_cache = {}

def load_translation_cache():
    if os.path.exists(TRANSLATION_CACHE_FILE):
        with open(TRANSLATION_CACHE_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def save_translation_cache(data):
    with open(TRANSLATION_CACHE_FILE, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

translation_cache = load_translation_cache()

async def handle_translation(update: Update, context):
    """مدیریت ترجمه آلمانی به فارسی با استفاده از کش"""
    try:
        user_text = update.message.text
        user_id = update.message.from_user.id
        username = update.message.from_user.username

        log_user_activity(user_id, username, 'Translation Request (DE to FA)', user_text)

        if user_text in translation_cache:
            translated_text = translation_cache[user_text]
            logging.info(f"ترجمه از کش برای '{user_text}' بارگذاری شد.")
        else:
            translated_text = GoogleTranslator(source='de', target='fa').translate(user_text)
            translation_cache[user_text] = translated_text  
            save_translation_cache(translation_cache) 
            logging.info(f"ترجمه جدید برای '{user_text}' ذخیره شد.")

        await update.message.reply_text(f"ترجمه: {translated_text}")

        context.user_data['current_state'] = 'TRANSLATE'

        keyboard = [
            [KeyboardButton('بله'), KeyboardButton('خیر')]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("نیاز به ترجمه کلمه یا متن دیگری دارید؟", reply_markup=reply_markup)
        return WAIT_FOR_ACTION
    except Exception as e:
        await update.message.reply_text(f"خطا در ترجمه: {str(e)}")
        return ConversationHandler.END


async def handle_translation_fa2de(update: Update, context):
    """مدیریت ترجمه فارسی به آلمانی با استفاده از کش"""
    try:
        user_text = update.message.text
        user_id = update.message.from_user.id
        username = update.message.from_user.username

        log_user_activity(user_id, username, 'Translation Request (FA to DE)', user_text)

        if user_text in translation_cache:
            translated_text = translation_cache[user_text]
            logging.info(f"ترجمه از کش برای '{user_text}' بارگذاری شد.")
        else:
            translated_text = GoogleTranslator(source='fa', target='de').translate(user_text)
            translation_cache[user_text] = translated_text 
            save_translation_cache(translation_cache)  
            logging.info(f"ترجمه جدید برای '{user_text}' ذخیره شد.")

        await update.message.reply_text(f"ترجمه: {translated_text}")

        context.user_data['current_state'] = 'TRANSLATE_FA2DE'

        keyboard = [
            [KeyboardButton('بله'), KeyboardButton('خیر')]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("نیاز به ترجمه کلمه یا متن دیگری دارید؟", reply_markup=reply_markup)
        return WAIT_FOR_ACTION
    except Exception as e:
        await update.message.reply_text(f"خطا در ترجمه: {str(e)}")
        return ConversationHandler.END


async def handle_article(update: Update, context):
    """مدیریت جستجوی آرتیکل کلمات"""
    try:
        search_term = update.message.text
        user_id = update.message.from_user.id
        username = update.message.from_user.username

        log_user_activity(user_id, username, 'Article Search', search_term)

        context.user_data['current_state'] = 'ARTICLE'

        if search_term in article_cache:
            results = article_cache[search_term]
            logging.info(f"نتایج از کش برای {search_term} بارگذاری شد.")
        else:
            logging.info(f"جستجو برای {search_term} در حال انجام است.")
            with ThreadPoolExecutor(max_workers=4) as executor:
                future = executor.submit(search_word_in_website, search_term)
                results = future.result()

            if results:
                article_cache[search_term] = results
                save_article_cache(article_cache)
                logging.info(f"نتایج جدید برای {search_term} ذخیره شد.")

        if results:
            if any(data['Singular'] == 'der Finder' for data in results.values()):
                await update.message.reply_text(
                    "کلمه‌ی مورد نظر آرتیکل ندارد. لطفاً در تایپ یا نوع کلمه‌ی مورد نظر دقت نمایید.")
            else:
                order = ['NOMINATIV', 'AKKUSATIV', 'DATIV', 'GENITIV']
                response = ""
                for case in order:
                    if case in results:
                        data = results[case]
                        response += f"{case}:\n  Singular: {data['Singular']}\n  Plural: {data['Plural']}\n\n"
                await update.message.reply_text(response or "هیچ نتیجه‌ای یافت نشد.")
        else:
            await update.message.reply_text(
                "کلمه‌ی مورد نظر آرتیکل ندارد. لطفاً در تایپ یا نوع کلمه‌ی مورد نظر دقت نمایید.")

        keyboard = [
            [KeyboardButton('بله'), KeyboardButton('خیر')]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("آیا نیاز به پیدا کردن آرتیکل کلمه‌ی دیگری دارید؟", reply_markup=reply_markup)
        return WAIT_FOR_ACTION
    except Exception as e:
        await update.message.reply_text(f"خطا در جستجوی آرتیکل: {str(e)}")
        return ConversationHandler.END



async def handle_action(update: Update, context):
    """مدیریت پاسخ‌های بله و خیر پس از ترجمه یا جستجو"""
    try:
        text = update.message.text
        current_state = context.user_data.get('current_state')

        if text == 'بله':
            if current_state == 'TRANSLATE_FA2DE':
                await update.message.reply_text("لطفاً کلمه یا متنی را که می‌خواهید ترجمه شود وارد کنید:")
                return TRANSLATE_FA2DE
            elif current_state == 'TRANSLATE':
                await update.message.reply_text("لطفاً کلمه یا متنی را که می‌خواهید ترجمه شود وارد کنید:")
                return TRANSLATE
            elif current_state == 'ARTICLE':
                await update.message.reply_text("لطفاً کلمه‌ای را که می‌خواهید آرتیکل آن نمایش داده شود وارد کنید:")
                return ARTICLE
        elif text == 'خیر':
            await start(update, context)
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"خطا در مدیریت عمل: {str(e)}")
        return ConversationHandler.END

def main():
    """تابع اصلی برای راه‌اندازی ربات"""
    app = Application.builder().token(TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply)],
        states={
            TRANSLATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_translation)],
            ARTICLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_article)],
            WAIT_FOR_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_action)],
            TRANSLATE_FA2DE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_translation_fa2de)],
        },
        fallbacks=[],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conversation_handler)

    max_retries = 5000
    retries = 0

    while retries < max_retries:
        try:
            app.run_polling()
            break  
        except Exception as e:
            logging.error(f"خطا در اجرای برنامه: {e}")
            retries += 1
            time.sleep(10) 

    if retries == max_retries:
        logging.error("تعداد تلاش‌های راه‌اندازی برنامه به پایان رسید. لطفاً بررسی کنید.")
        sys.exit(1)



if __name__ == '__main__':
    main()
