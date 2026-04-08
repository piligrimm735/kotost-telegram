import os
import io
import base64
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загружаем переменные окружения из файла .env (если есть)
load_dotenv()

# ==================================================
# Токены и настройки - берутся из окружения
# ==================================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в переменных окружения")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN не задан в переменных окружения")

# Модель на Hugging Face, которая поддерживает img2img (сохраняет персонажа)
MODEL_ID = "stabilityai/stable-diffusion-2-1"

# Путь к эталонной картинке Котости (лежит в папке reference)
REFERENCE_PATH = os.path.join(os.getcwd(), "reference", "kotost.png")
# ==================================================

logging.basicConfig(level=logging.INFO)

def get_reference_image_b64():
    """Читает эталонную картинку и возвращает base64"""
    if not os.path.exists(REFERENCE_PATH):
        return None
    with open(REFERENCE_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def generate_kotost(user_prompt: str):
    """
    Отправляет запрос в Hugging Face API с текстом + эталоном.
    Возвращает байты картинки или (None, ошибка)
    """
    ref_b64 = get_reference_image_b64()
    if not ref_b64:
        return None, "❌ Нет эталонной картинки Котости. Положите файл reference/kotost.png"

    # Промпт, усиливающий узнаваемость персонажа
    full_prompt = (
        f"anthropomorphic fluffy gray cat with long droopy ears, standing on two legs, "
        f"cartoon style, {user_prompt}, high quality, detailed, no text, no watermark"
    )

    API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    # Для img2img передаём эталон как init_image
    payload = {
        "inputs": full_prompt,
        "parameters": {
            "init_image": ref_b64,
            "strength": 0.75,      # 0.7-0.8 – меняем фон/позу, сохраняем лицо
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
            "width": 768,
            "height": 768
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
        "🐱 **Генератор Котости**\n\n"
        "Просто опишите, что должна делать Котость.\n"
        "Например:\n"
        "• котость на пляже с мухомором\n"
        "• котость в космосе\n"
        "• котость-программист за ноутбуком\n\n"
        "Нейросеть нарисует нового Котость в этой ситуации.\n"
        "Обычно 20–40 секунд."
    )

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text.strip()
    if not prompt:
        return

    await update.message.chat.send_action(action="upload_photo")
    status_msg = await update.message.reply_text(
        f"🎨 Генерирую Котость по запросу:\n«{prompt}»\n⏳ Пожалуйста, подождите..."
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
            f"❌ Не удалось сгенерировать :(\nОшибка: {error}\n\n"
            "Попробуйте другой запрос или позже."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Просто напишите любое описание.\n"
        "Я отправлю сгенерированную картинку с Котостью.\n\n"
        "Примеры:\n"
        "котость на пляже\n"
        "котость в лесу с грибами\n"
        "котость с пиццей"
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
