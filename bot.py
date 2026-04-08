import os
import io
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

# ============================================
# НАСТРОЙКИ
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан")
if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY не задан")

# API DeepSeek для генерации изображений
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/images/generations"
# ============================================

logging.basicConfig(level=logging.INFO)

def generate_kotost(user_prompt: str):
    """
    Генерирует картинку Котости через DeepSeek API
    """
    # Промпт с описанием Котости
    full_prompt = (
        f"Создай изображение персонажа Котость. "
        f"Котость — это антропоморфный серый пушистый кот с длинными свисающими ушами, "
        f"стоит на двух лапах. У него грустные/уставшие глаза и лохматая шерсть. "
        f"Сцена: {user_prompt}. "
        f"Стиль: мультяшный, качественный, детализированный."
    )

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "dall-e-3",  # DeepSeek использует совместимый с OpenAI API
        "prompt": full_prompt,
        "n": 1,
        "size": "1024x1024",
        "quality": "standard"
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=90)
        
        if response.status_code == 200:
            data = response.json()
            image_url = data['data'][0]['url']
            # Скачиваем картинку по URL
            img_response = requests.get(image_url, timeout=30)
            return img_response.content, None
        else:
            return None, f"Ошибка API: {response.status_code} - {response.text[:200]}"
    except Exception as e:
        return None, str(e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🐱 **Генератор Котости через DeepSeek**\n\n"
        "Просто опиши, где и что должна делать Котость:\n"
        "• котость на пляже с мухомором\n"
        "• котость в космосе\n"
        "• котость-программист за ноутбуком\n\n"
        "Нейросеть DeepSeek нарисует!"
    )

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    if not prompt:
        return

    await update.message.chat.send_action(action="upload_photo")
    status_msg = await update.message.reply_text(
        f"🎨 Генерирую Котость через DeepSeek:\n«{prompt}»\n⏳ Обычно 10-20 секунд..."
    )

    img_bytes, error = generate_kotost(prompt)

    if img_bytes:
        await update.message.reply_photo(
            photo=io.BytesIO(img_bytes),
            caption=f"🐱 Твоя КОТОСТЬ (DeepSeek): «{prompt}»"
        )
        await status_msg.delete()
    else:
        await status_msg.edit_text(
            f"❌ Ошибка: {error}\n\n"
            "Проверь API ключ DeepSeek или попробуй другой запрос."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Просто напиши описание:\n"
        "котость на пляже\nкотость в лесу\nкотость с пиццей\n\n"
        "DeepSeek нарисует Котость в этой сцене!"
    )

def main():
    print("🤖 Бот-генератор Котости (DeepSeek) запускается...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt))
    print("✅ Бот запущен, жду сообщений...")
    app.run_polling()

if __name__ == "__main__":
    main()
