\import os
import logging
import requests
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============================================
# ТВОИ ДАННЫЕ
BOT_TOKEN = "BOT_TOKEN"  # вставь сюда
GEMINI_API_KEY = "GEMINI_API_KEY"
# ============================================

GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

logging.basicConfig(level=logging.INFO)

def ask_gemini(question: str) -> str:
    """Отправляет вопрос в Gemini и возвращает ответ"""
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": question}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1000,
            "topP": 0.95
        }
    }
    
    try:
        response = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            # Извлекаем текст ответа
            try:
                answer = data['candidates'][0]['content']['parts'][0]['text']
                return answer
            except (KeyError, IndexError):
                return "❌ Не удалось получить ответ от Gemini"
        else:
            return f"❌ Ошибка API: {response.status_code} - {response.text[:200]}"
    except Exception as e:
        return f"❌ Ошибка: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Gemini в Telegram!**\n\n"
        "Я — нейросеть от Google.\n"
        "Отвечаю на вопросы, помогаю, объясняю.\n\n"
        "Просто напиши мне что угодно!\n\n"
        "Чем могу помочь?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()
    if not user_message:
        return
    
    # Показываем, что бот печатает
    await update.message.chat.send_action(action="typing")
    
    # Получаем ответ от Gemini
    answer = ask_gemini(user_message)
    
    # Отправляем ответ (если длинный — разбиваем)
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
        "Я — Gemini от Google!"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ **О боте:**\n\n"
        "• Нейросеть: Gemini 1.5 Flash\n"
        "• От: Google\n"
        "• Бесплатно: 60 запросов/минуту\n"
        "• Поддерживает русский язык\n\n"
        "Просто задавай вопросы!"
    )

def main():
    print("🤖 Бот с Gemini запускается...")
    print("Модель: Gemini 1.5 Flash")
    print("API: Google Generative AI")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот запущен, жду сообщений...")
    app.run_polling()

if __name__ == "__main__":
    main()
