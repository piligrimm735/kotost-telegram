import os
import io
import base64
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

# ============================================
# ТОКЕНЫ И НАСТРОЙКИ
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN не задан")

# !!! ИСПРАВЛЕННЫЙ URL и МОДЕЛЬ !!!
# Используем официальный Inference Client от Hugging Face
# Модель FLUX.1-Kontext-dev идеально подходит для редактирования изображений.
MODEL_ID = "black-forest-labs/FLUX.1-Kontext-dev"

# Папка с эталонной картинкой
REFERENCE_PATH = os.path.join(os.getcwd(), "reference", "kotost.png")
# ============================================

logging.basicConfig(level=logging.INFO)

def get_reference_bytes():
    """Читает эталонную картинку и возвращает байты"""
    if not os.path.exists(REFERENCE_PATH):
        return None
    with open(REFERENCE_PATH, "rb") as f:
        return f.read()

def generate_kotost(user_prompt: str):
    """
    Генерирует изображение, используя Hugging Face Inference API (официальный клиент).
    """
    image_bytes = get_reference_bytes()
    if not image_bytes:
        return None, "❌ Нет эталонной картинки. Положите файл reference/kotost.png"

    # Формируем четкую инструкцию для модели
    full_prompt = f"Transform the given cat into the character Kotost. Make the cat have long droopy ears and stand on two legs, then place this character in the following scene: {user_prompt}. Keep the character's features consistent."

    # Импортируем официальный клиент Hugging Face
    from huggingface_hub import InferenceClient
    
    try:
        # Создаем клиент с нашим токеном
        client = InferenceClient(token=HF_TOKEN)
        
        # Вызываем метод image_to_image с правильными параметрами
        # Параметр provider="fal-ai" указывает на использование одного из Inference Providers
        output_image = client.image_to_image(
            image=image_bytes,
            prompt=full_prompt,
            model=MODEL_ID,
            provider="fal-ai"  # Используем провайдера для ускорения
        )
        
        # Сохраняем результат в BytesIO
        img_byte_arr = io.BytesIO()
        output_image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue(), None
        
    except Exception as e:
        return None, str(e)

# --- ОСТАЛЬНЫЕ ФУНКЦИИ (start, handle_prompt, help_command, main) ОСТАЮТСЯ БЕЗ ИЗМЕНЕНИЙ ---
# ...

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
