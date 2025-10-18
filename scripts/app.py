import telebot
import os
from dotenv import load_dotenv
import random
import schedule
import time
import threading
from flask import Flask, request

load_dotenv()
TOKEN = os.getenv('TOKEN_BOT')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)


# Function to load words from file
def load_words_from_file(filename):
    words = {}
    try:
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                eng, cz = line.split("=", 1)
                words[eng.strip()] = cz.strip()
    except FileNotFoundError:
        print(f"File {filename} not found!")
    return words


# English - Czech words from files by levels
words_levels = {
    "Level 1": load_words_from_file("../en-cz-dictionaries/words_level1.txt"),
    "Level 2": load_words_from_file("../en-cz-dictionaries/words_level2.txt"),
    "Level 3": load_words_from_file("../en-cz-dictionaries/words_level3.txt")
}

subscribers = set()  # All users
user_tests = {}  # Data tests
user_level_choice = {}  # Stores user-selected level


# Function to return main keyboard
def main_keyboard():
    """
    Returns the main keyboard with all main bot commands including the new "Set level ⚙️" button.

    :return: ReplyKeyboardMarkup object with main buttons
    """
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        telebot.types.KeyboardButton("Teach new word 🧑‍🏫"),
        telebot.types.KeyboardButton("English test 🤓"),
        telebot.types.KeyboardButton("Information ℹ️"),
        telebot.types.KeyboardButton("Leave feedback❓"),
        telebot.types.KeyboardButton("Set level ⚙️")
    )
    return markup


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

    bot.send_message(
        message.chat.id,
        "👋 Hello! I'm your English learning bot.\nChoose an option below:",
        reply_markup=main_keyboard()
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
    - Set level

    :param message: Telegram message object
    """

    if message.text.startswith("Information"):
        bot.send_message(message.chat.id, "ℹ️ This bot helps you learn English words (for Czech speakers).")

    elif message.text.startswith("Leave feedback"):
        bot.send_message(message.chat.id, "Have you already completed a course with us? If yes, we would be glad to"
                                          " receive your feedback on our website EXAMPLE-WEB! "
                                          "https://github.com/jevhen123zavirukha/TelegramBot_english")

    elif message.text.startswith("Set level ⚙️"):
        choose_level_global(message)

    elif message.text.startswith("Teach new word 🧑‍🏫"):
        teach_word(message)

    elif message.text.startswith("English test 🤓"):
        choose_level_for_test(message)


# Set user level manually
def choose_level_global(message):
    """
    Prompts the user to select a level for their learning.
    After user selection, calls `set_level_global` to save the level.

    :param message: Telegram message object
    """
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for level in words_levels.keys():
        markup.add(level)
    bot.send_message(message.chat.id, "Choose your new level:", reply_markup=markup)
    bot.register_next_step_handler(message, set_level_global)


def set_level_global(message):
    """
    Sets the user's learning level globally and confirms selection.
    Returns the user to the main panel after selection.

    :param message: Telegram message object
    """
    level = message.text
    if level not in words_levels:
        bot.send_message(message.chat.id, "Invalid level, try again.", reply_markup=main_keyboard())
        return
    user_level_choice[message.chat.id] = level
    bot.send_message(message.chat.id, f"✅ Your level is set to {level}", reply_markup=main_keyboard())


# Teach new word
def teach_word(message):
    """
    Sends a random word from the user's selected level to the user.
    After sending the word, returns to the main panel.

    :param message: Telegram message object
    """
    level = user_level_choice.get(message.chat.id, "Level 1")
    word_dict = words_levels[level]
    word = random.choice(list(word_dict.keys()))
    translation = word_dict[word]
    bot.send_message(message.chat.id, f"🧠 New word ({level}): {word}\n💬 Translation: {translation}",
                     reply_markup=main_keyboard())


# Choose level for test
def choose_level_for_test(message):
    """
    Prompts the user to select a level before starting an English test.
    Calls `start_test_by_level` after selection.

    :param message: Telegram message object
    """
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for level in words_levels.keys():
        markup.add(level)
    bot.send_message(message.chat.id, "Choose level for test:", reply_markup=markup)
    bot.register_next_step_handler(message, start_test_by_level)


def start_test_by_level(message):
    """
    Starts the test for the selected level after verifying its validity.
    Sets the level for the user and calls `start_test`.

    :param message: Telegram message object
    """
    level = message.text
    if level not in words_levels:
        bot.send_message(message.chat.id, "Invalid level, try again.", reply_markup=main_keyboard())
        return

    user_level_choice[message.chat.id] = level
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

    level = user_level_choice.get(message.chat.id, "Level 1")
    word_dict = words_levels[level]

    word = random.choice(list(word_dict.keys()))
    correct = word_dict[word]

    wrong_answers = random.sample(
        [t for t in word_dict.values() if t != correct], 3)
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
        bot.send_message(
            message.chat.id,
            f"🎓 Test finished!\nYour score: {user_data['score']}/5 ✅",
            reply_markup=main_keyboard()
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

    for user_id in subscribers:
        # Choose random level
        level = random.choice(list(words_levels.keys()))
        word_dict = words_levels[level]
        word = random.choice(list(word_dict.keys()))
        bot.send_message(user_id, f"🌞 Word of the day ({level}):\n🧠 {word} — {word_dict[word]}")


# Schedule task at 9:00 AM
schedule.every().day.at("09:00").do(send_daily_word)


def scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)


# Run schedule in background
threading.Thread(target=scheduler, daemon=True).start()


# Flask webhook endpoints
@app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200


@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


# Main entrypoint
if __name__ == "__main__":
    bot.remove_webhook()

    RAILWAY_URL = ""
    webhook_url = f"https://{RAILWAY_URL}/{TOKEN}"

    bot.set_webhook(url=webhook_url)

    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Bot webhook set at {webhook_url}, running on port {port}")
    app.run(host="0.0.0.0", port=port)
