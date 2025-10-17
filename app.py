import telebot
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN_BOT')
bot = telebot.TeleBot(TOKEN)

# English - Czech words
english_words = {
    "fish": "ryba",
    "replay": "přehrát",
    "bow": "luk / uklonit se",
    "minute": "minuta",
    "time": "čas",
    "cheese": "sýr"
}

if __name__ == "__main__":
    bot.polling()
