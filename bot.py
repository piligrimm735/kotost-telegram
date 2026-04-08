import os
import io
import base64
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загружаем переменные из .env (если файл существует)
load_dotenv()

# ============================================
# ТОКЕНЫ И НАСТРОЙКИ
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# Проверяем, что оба токена заданы
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN не задан")

# !!! ИСПРАВЛЕННЫЙ URL: используем специальную модель для редактирования изображений !!!
API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-Kontext-dev"

# Папка с эталонной картинкой
REFERENCE_PATH = os.path.join(os.getcwd(), "reference", "kotost.png")
# ============================================

logging.basicConfig(level=logging.INFO)

def get_reference_base64():
    """Читает эталонную картинку и возвращает base64"""
    if not os.path.exists(REFERENCE_PATH):
        return None
    with open(REFERENCE_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def generate_kotost(user_prompt: str):
    """
    Генерирует изображение на основе эталона и текста.
    """
    ref_b64 = get_reference_base64()
    if not ref_b64:
        return None, "❌ Нет эталонной картинки. Положите файл reference/kotost.png"

    # Формируем промпт для модели FLUX.1-Kontext-dev
    # Она ожидает четкую инструкцию, что именно нужно изменить в изображении.
    full_prompt = f"Transform the given cat into the character Kotost. Make the cat have long droopy ears and stand on two legs, then place this character in the following scene: {user_prompt}. Keep the character's features consistent."

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    # Для модели Kontext параметр "inputs" — это промпт, а "image" — это сама картинка.
    payload = {
        "inputs": full_prompt,
        "image": ref_b64,
        "parameters": {
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=90)
        if response.status_code == 200:
            return response.content, None
        else:
            return None, f"Ошибка API: {response.status_code} - {response.text[:200]}"
    except Exception as e:
        return None, str(e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🐱 **Генератор Котости (по эталону)**\n\n"
        "Просто напиши, где или как должен быть Котость:\n"
        "• котость на пляже с мухомором\n"
        "• котость в космосе\n"
        "• котость-программист\n\n"
        "Нейросеть сохранит внешность эталона из папки reference/"
    )

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    if not prompt:
        return

    await update.message.chat.send_action(action="upload_photo")
    status_msg = await update.message.reply_text(
        f"🎨 Генерирую: «{prompt}»\n⏳ Обычно 20-40 секунд..."
    )

    img_bytes, error = generate_kotost(prompt)

    if img_bytes:
        await update.message.reply_photo(
            photo=io.BytesIO(img_bytes),
            caption=f"🐱 Твоя КОТОСТЬ: «{prompt}»"
        )
        await status_msg.delete()
    else:
        await status_msg.edit_text(
            f"❌ Ошибка: {error}\n\nПопробуй другой запрос или позже."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Просто напиши текст, например:\n"
        "котость на пляже\nкотость в лесу\nкотость с пиццей"
    )

def main():
    print("🤖 Бот-генератор Котости запускается...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt))
    print("✅ Бот запущен, жду сообщений...")
    app.run_polling()

if __name__ == "__main__":
    main()
