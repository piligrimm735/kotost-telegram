import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

# ============================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан")
if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY не задан")

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
# ============================================

logging.basicConfig(level=logging.INFO)

def ask_deepseek(question: str) -> str:
    """Отправляет вопрос в DeepSeek и возвращает ответ"""
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ты — дружелюбный помощник. Отвечай кратко и по делу."},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            return f"❌ Ошибка API: {response.status_code}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Нейросеть DeepSeek в Telegram!**\n\n"
        "Просто напиши мне любой вопрос, и я отвечу.\n"
        "Работаю на нейросети DeepSeek (аналог ChatGPT).\n\n"
        "Чем могу помочь?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    if not user_message:
        return
    
    # Показываем, что бот печатает
    await update.message.chat.send_action(action="typing")
    
    # Отправляем запрос в DeepSeek
    answer = ask_deepseek(user_message)
    
    # Отправляем ответ (если длинный — разбиваем)
    if len(answer) > 4000:
        for i in range(0, len(answer), 4000):
            await update.message.reply_text(answer[i:i+4000])
    else:
        await update.message.reply_text(answer)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Просто напиши мне вопрос, например:\n"
        "• Что такое чёрная дыра?\n"
        "• Напиши стих про кота\n"
        "• Как приготовить пиццу?\n\n"
        "Я отвечу текстом через нейросеть DeepSeek."
    )

def main():
    print("🤖 Нейросеть DeepSeek запускается...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Бот запущен, жду сообщений...")
    app.run_polling()

if __name__ == "__main__":
    main()
