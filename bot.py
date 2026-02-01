import os
import telebot
import requests
from fastapi import FastAPI
import uvicorn

# Получаем токен бота из переменных окружения Render
TOKEN = os.getenv("TG_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Инициализируем FastAPI приложение
app = FastAPI()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "Привет! В этом боте ты можешь моментально конвертировать валюту.\\nНапиши количество и валюту (пример: 100 RUB)"
    )

def get_exchange_rate(base_currency, target_currency):
    """Получение курса обмена валют."""
    api_key = os.getenv("EXCHANGE_RATE_API_KEY")
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if 'conversion_rates' in data:
            return data['conversion_rates'].get(target_currency)
    return None

@bot.message_handler(func=lambda m: True)
def handle_currency(message):
    try:
        # Получаем количество и валюту
        amount, base_currency = message.text.split()
        amount = float(amount)
        
        # Отправляем промежуточное сообщение о запросе валюты
        temp_msg = bot.send_message(message.chat.id, "Введите валюту, в которую хотите конвертировать (например: USD)")
        
        # Регистрируем следующий шаг для получения целевой валюты
        bot.register_next_step_handler(message, convert_currency, amount, base_currency, temp_msg)
    except Exception as e:
        print(e)
        bot.reply_to(message, "Что-то пошло не так при обработке вашего запроса :(")

def convert_currency(message, amount, base_currency, temp_msg):
    try:
        target_currency = message.text.strip().upper()
        
        # Получаем курс обмена
        exchange_rate = get_exchange_rate(base_currency, target_currency)
        if exchange_rate is None:
            bot.reply_to(message, "Не удалось получить курс обмена.")
            return
        
        # Рассчитываем сумму в целевой валюте
        converted_amount = amount * exchange_rate
        
        # Удаляем промежуточное сообщение
        bot.delete_message(temp_msg.chat.id, temp_msg.message_id)
        
        # Отправляем результат
        bot.send_message(message.chat.id, f"{amount} {base_currency} = {converted_amount:.2f} {target_currency}")
        
        # Завершаем обработку сообщением благодарности
        bot.send_message(message.chat.id, "Спасибо за использование нашего бота!")
    except Exception as e:
        print(e)
        bot.reply_to(message, "Что-то пошло не так при обработке вашего запроса :(")

# Запускаем бота
bot.infinity_polling()

# Настройка FastAPI для прослушивания порта
@app.get("/")
async def root():
    return {"message": "Telegram Currency Converter Bot is running!"}

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 0))  # Автоматический выбор порта
    uvicorn.run(app, host="0.0.0.0", port=PORT)
