import telebot
import os
from dotenv import load_dotenv
import random

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
subscribers = set()   # All users
user_tests = {}       # Data tests


# Start message
@bot.message_handler(commands=['start'])
def start(message):

    """
    Handles the /start command.
    Adds the user to the subscribers set and sends a welcome message
    with a keyboard for options: Teach new word, English test, Information.

    :param message: Telegram message object
    """

    subscribers.add(message.chat.id)

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton("Teach new word 🧑‍🏫")
    btn2 = telebot.types.KeyboardButton("English test 🤓")
    btn3 = telebot.types.KeyboardButton("Information ℹ️")
    markup.add(btn1, btn2, btn3)

    bot.send_message(
        message.chat.id,
        "👋 Hello! I'm your English learning bot.\nChoose an option below:",
        reply_markup=markup
    )


# The main command handler
@bot.message_handler(func=lambda message: True)
def reply(message):

    """
    Handles all text messages from the user.
    Routes the message to the appropriate functionality based on text:
    - Information
    - Teach new word
    - English test

    :param message: Telegram message object
    """

    if message.text.startswith("Information"):
        bot.send_message(message.chat.id, "ℹ️ This bot helps you learn English words for Czech speakers.")

    elif message.text.startswith("Teach new word"):
        word = random.choice(list(english_words.keys()))
        translation = english_words[word]
        bot.send_message(message.chat.id, f"🧠 New word: {word}\n💬 Translation: {translation}")


if __name__ == "__main__":
    bot.polling()
