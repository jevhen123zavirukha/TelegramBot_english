import telebot
import os
from dotenv import load_dotenv
import random
import schedule
import time
import threading

load_dotenv()
TOKEN = os.getenv('TOKEN_BOT')
bot = telebot.TeleBot(TOKEN)


# Function to load words from file
def load_words_from_file(filename):
    words = {}
    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or "=" not in line:
                continue
            eng, cz = line.split("=", 1)
            words[eng.strip()] = cz.strip()
    return words


# English - Czech words from file
english_words = load_words_from_file("words.txt")
subscribers = set()  # All users
user_tests = {}  # Data tests


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
    btn4 = telebot.types.KeyboardButton("Leave feedback❓")
    markup.add(btn1, btn2, btn3, btn4)

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

    if message.text.startswith("Leave feedback"):
        bot.send_message(message.chat.id, "Have you already completed a course with us? If yes, we would be glad to"
                                          " receive your feedback on our website EXAMPLE-WEB! "
                                          "https://github.com/jevhen123zavirukha/TelegramBot_english")

    elif message.text.startswith("Teach new word"):
        word = random.choice(list(english_words.keys()))
        translation = english_words[word]
        bot.send_message(message.chat.id, f"🧠 New word: {word}\n💬 Translation: {translation}")
    elif message.text.startswith("English test"):
        start_test(message)


# Start test
def start_test(message):
    """
    Initializes a new English test for the user.
    Creates a dictionary in `user_tests` to store score and number of asked questions.
    Sends a message to start the test and calls `ask_question`.

    :param message: Telegram message object
    """

    user_tests[message.chat.id] = {
        "score": 0,
        "asked": 0
    }
    bot.send_message(message.chat.id, "🎯 English test started! You will get 5 questions.")
    ask_question(message)


# Ask question
def ask_question(message):
    """
    Sends a random English word to the user as a question.
    Generates 4 answer options (1 correct + 3 wrong) and registers
    the next step handler to `check_answer`.

    :param message: Telegram message object
    """

    user_data = user_tests[message.chat.id]
    user_data["asked"] += 1

    word = random.choice(list(english_words.keys()))
    correct = english_words[word]

    wrong_answers = random.sample(
        [t for t in english_words.values() if t != correct], 3)
    options = wrong_answers + [correct]
    random.shuffle(options)

    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for opt in options:
        markup.add(opt)

    bot.send_message(
        message.chat.id,
        f"Translate the word: **{word}**",
        reply_markup=markup,
        parse_mode="Markdown"
    )

    bot.register_next_step_handler(message, check_answer, word, correct)


# Check answer
def check_answer(message, word, correct):
    """
    Checks the user's answer to a question.
    Updates the user's score if correct.
    Either asks the next question or finishes the test after 5 questions.

    :param message: Telegram message object
    :param word: The English word asked
    :param correct: Correct Czech translation
    """

    user_data = user_tests.get(message.chat.id)
    if not user_data:
        bot.send_message(message.chat.id, "Please start the test again with 'English test 🤓'.")
        return

    if message.text == correct:
        bot.send_message(message.chat.id, f"✅ Correct! '{word}' = {correct}")
        user_data["score"] += 1
    else:
        bot.send_message(message.chat.id, f"❌ Wrong! '{word}' = {correct}")

    if user_data["asked"] < 5:
        ask_question(message)
    else:
        # Making again panel
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            telebot.types.KeyboardButton("Teach new word 🧑‍🏫"),
            telebot.types.KeyboardButton("English test 🤓"),
            telebot.types.KeyboardButton("Information ℹ️"),
            telebot.types.KeyboardButton("Leave feedback❓"),
        )

        bot.send_message(
            message.chat.id,
            f"🎓 Test finished!\nYour score: {user_data['score']}/5 ✅",
            reply_markup=markup
        )
        del user_tests[message.chat.id]


# Daily word sending
def send_daily_word():
    """
    Sends a daily English word to all subscribed users.
    Chooses a random word from the dictionary.
    """

    if not subscribers:
        return
    word = random.choice(list(english_words.keys()))
    for user_id in subscribers:
        bot.send_message(user_id, f"🌞 Word of the day:\n🧠 {word} — {english_words[word]}")


# Schedule task at 9:00 AM
schedule.every().day.at("09:00").do(send_daily_word)


def scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)


# Run schedule in background
threading.Thread(target=scheduler, daemon=True).start()

print("Bot is running!")
bot.polling()

if __name__ == "__main__":
    bot.polling()
