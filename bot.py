import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

# ============================================
# ТОКЕНЫ
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROK_API_KEY = os.getenv("GROK_API_KEY")  # API ключ от xAI

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан")
if not GROK_API_KEY:
    raise ValueError("GROK_API_KEY не задан")

# xAI / Grok API
GROK_API_URL = "https://api.x.ai/v1/chat/completions"
# ============================================

logging.basicConfig(level=logging.INFO)

def ask_grok(question: str) -> str:
    """Отправляет вопрос в Grok и возвращает ответ"""
    
    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "grok-beta",  # или "grok-vision-beta" если нужны картинки
        "messages": [
            {"role": "system", "content": "Ты — Grok, дружелюбный и остроумный помощник от xAI. Отвечай кратко, понятно и с юмором."},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    try:
        response = requests.post(GROK_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            return f"❌ Ошибка API: {response.status_code} - {response.text[:200]}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Grok в Telegram!**\n\n"
        "Я — нейросеть от xAI (Илона Маска).\n"
        "Отвечаю на вопросы, шучу и помогаю.\n\n"
        "Просто напиши мне что угодно!\n\n"
        "Чем могу помочь?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    if not user_message:
        return
    
    await update.message.chat.send_action(action="typing")
    answer = ask_grok(user_message)
    
    if len(answer) > 4000:
        for i in range(0, len(answer), 4000):
            await update.message.reply_text(answer[i:i+4000])
    else:
        await update.message.reply_text(answer)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **Как пользоваться:**\n\n"
        "Просто напиши любой вопрос:\n"
        "• Что ты умеешь?\n"
        "• Расскажи шутку\n"
        "• Как работает ИИ?\n"
        "• Помоги с кодом\n\n"
        "Я — Grok, нейросеть от xAI!"
    )

def main():
    print("🤖 Бот с Grok (xAI) запускается...")
    print("Модель: grok-beta")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот запущен, жду сообщений...")
    app.run_polling()

if __name__ == "__main__":
    main()
