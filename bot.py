import os
import random
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==================================================
# 🔧 НАСТРОЙКИ - ЗАМЕНИТЬ ТОЛЬКО ЭТУ СТРОКУ!
# ==================================================
BOT_TOKEN = ""
PASTA_S_KOTOSTYU = "kotost"  # название папки с фото
# ==================================================

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_random_kotost():
    """Берёт случайную картинку Котости из папки kotost"""
    
    folder_path = os.path.join(os.getcwd(), PASTA_S_KOTOSTYU)
    
    if not os.path.exists(folder_path):
        return None, f"❌ Папка '{PASTA_S_KOTOSTYU}' не найдена!"
    
    images = [f for f in os.listdir(folder_path) 
              if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
    
    if not images:
        return None, f"❌ В папке '{PASTA_S_KOTOSTYU}' нет картинок!"
    
    random_image = random.choice(images)
    return os.path.join(folder_path, random_image), f"✅ Найдено {len(images)} картинок"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🐱 Привет! Я бот-Котость.\n"
        "Просто напиши любое сообщение, и я пришлю случайную Котость.\n\n"
        "Команды:\n/start - приветствие\n/help - помощь\n/count - сколько Котостей в коллекции"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Просто напиши текст, я отвечу картинкой.\n"
        "Чтобы добавить новых Котостей, положи файлы в папку 'kotost' рядом со мной."
    )

async def count_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    folder_path = os.path.join(os.getcwd(), PASTA_S_KOTOSTYU)
    if not os.path.exists(folder_path):
        await update.message.reply_text("❌ Папка kotost не найдена")
        return
    images = [f for f in os.listdir(folder_path) 
              if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))]
    await update.message.reply_text(f"📊 В коллекции {len(images)} Котостей.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action(action="upload_photo")
    image_path, msg = get_random_kotost()
    await update.message.reply_text(msg)
    if image_path:
        with open(image_path, 'rb') as photo:
            await update.message.reply_photo(photo=photo, caption="🐱 Твоя КОТОСТЬ!")
    else:
        await update.message.reply_text("❌ Не могу отправить Котость. Проверь папку kotost.")

def main():
    print("🤖 Бот запускается...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("count", count_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Бот запущен, жду сообщений...")
    app.run_polling()

if __name__ == "__main__":
    main()