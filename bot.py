import telebot
from telebot import types
import requests
import random
import re
import os
from flask import Flask, request

bot.set_webhook(url="https://https://friendly-octo-disco-1.onrender.com" + TOKEN)

API_KEY = "NSE56XN-SQXM40Q-NBR3AXV-K4CRCGN"
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# обработчик команд
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я готов работать через Webhook.")

# обработка входящих обновлений от Telegram
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_str = request.stream.read().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# установка webhook при запуске
@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://<your-app-name>.onrender.com/" + TOKEN)
    return "Webhook set", 200



user_poisk = {}
user_sled = {}
user_look = {}
user_results = {}
user_index = {}

def keyboard_glavn():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Поиск фильма по описанию", "Подбор фильма по жанру")
    markup.add("Случайный фильм")
    return markup

def keyboard_search():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Добавить информацию о фильме", "Дополнительный 1 фильм")
    markup.add("Вернуться на главную")
    return markup

def keyboard_zanr():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Выбрать другой жанр", "Дополнительный 1 фильм")
    markup.add("Вернуться на главную")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    name = message.from_user.first_name
    bot.send_message(message.chat.id, f"Привет {name}, рад Вас видеть!\nЧто Вы сегодня будете смотреть?", reply_markup=keyboard_glavn())

def extract_keywords(text):
    word = re.findall(r'\b\w+\b', text.lower())
    stop_word = {
        'и', 'в', 'на', 'про', 'о', 'фильм', 'фильма', 'это', 'тот', 'там', 'что',
        'хочу', 'посмотреть', 'буду', 'есть', 'быть', 'можно', 'нужно', 'по', 'типа', 'типо'
    }
    return [w for w in word if w not in stop_word and len(w) > 2]

@bot.message_handler(func=lambda m: m.text == "Вернуться на главную")
def go_to_back(message):
    bot.send_message(message.chat.id, "Вы вернулись на главную", reply_markup=keyboard_glavn())

@bot.message_handler(func=lambda m: m.text == "Дополнительный 1 фильм")
def more_one_film(message):
    send_next_film(message.chat.id)

@bot.message_handler(func=lambda m: m.text == "Выбрать другой жанр")
def choose_another_genre(message):
    genre_selection(message)

@bot.message_handler(func=lambda m: m.text == "Поиск фильма по описанию")
def fraza(message):
    bot.send_message(message.chat.id, "Введите описание фильма, я попробую его найти", reply_markup=keyboard_search())
    user_poisk[message.chat.id] = ""

@bot.message_handler(func=lambda m: m.chat.id in user_poisk and user_poisk[m.chat.id] == "")
def poisk_po_fraze(message):
    chat_id = message.chat.id
    user_sled.setdefault(chat_id, []).append(message.text)
    query = " ".join(extract_keywords(" ".join(user_sled[chat_id])))

    headers = {"X-API-KEY": API_KEY}
    user_look.setdefault(chat_id, set())
    found = False

    # Поиск по описанию
    response_keywords = requests.get(
        "https://api.kinopoisk.dev/v1.4/movie/search-by-keywords",
        headers=headers,
        params={"keywords": query}
    ).json()

    # Поиск по названию
    response_title = requests.get(
        "https://api.kinopoisk.dev/v1.4/movie/search",
        headers=headers,
        params={"query": query}
    ).json()

    results = []
    if response_keywords.get("docs"):
        results.extend(response_keywords["docs"])
    if response_title.get("docs"):
        results.extend(response_title["docs"])

    shown_ids = set()
    for film in results:
        film_id = film.get("id")
        if not film_id or film_id in user_look[chat_id] or film_id in shown_ids:
            continue
        shown_ids.add(film_id)
        user_look[chat_id].add(film_id)

        title = film.get("name", "Без названия")
        year = film.get("year", "Год неизвестен")
        poster = film.get("poster", {}).get("url", "")
        description = film.get("description", "Нет описания")
        link = f"https://www.kinopoisk.ru/film/{film_id}"

        if len(description) > 800:
            description = description[:800] + "..."

        vivod = f"<b>{title}</b>\nГод: {year}\n{description}\nСсылка на фильм:\n{link}"

        if poster:
            bot.send_photo(chat_id, poster, caption=vivod, parse_mode="HTML", reply_markup=keyboard_search())
        else:
            bot.send_message(chat_id, vivod, parse_mode="HTML", reply_markup=keyboard_search())
        found = True

    if not found:
        bot.send_message(chat_id, "Фильм не найден. Попробуйте изменить описание.", reply_markup=keyboard_search())
    user_poisk[chat_id] = None

@bot.message_handler(func=lambda m: m.text == "Добавить информацию о фильме")
def insert(message):
    chat_id = message.chat.id
    if chat_id in user_sled:
        bot.send_message(chat_id, "Добавьте больше данных о фильме, который Вы ищите", reply_markup=keyboard_search())
        user_poisk[chat_id] = "add_info"
    else:
        bot.send_message(chat_id, "Сначала введите описание фильма через 'Поиск фильма по описанию'.", reply_markup=keyboard_search())

@bot.message_handler(func=lambda m: user_poisk.get(m.chat.id) == "add_info")
def add_info(message):
    chat_id = message.chat.id
    user_sled.setdefault(chat_id, []).append(message.text)
    user_poisk[chat_id] = ""
    poisk_po_fraze(message)

@bot.message_handler(func=lambda m: m.text == "Подбор фильма по жанру")
def genre_selection(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Комедия", "Драма", "Фантастика")
    markup.add("Триллер", "Боевик", "Вернуться на главную")
    bot.send_message(message.chat.id, "Выберите жанр:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["Комедия", "Драма", "Фантастика", "Триллер", "Боевик"])
def genre_search(message):
    chat_id = message.chat.id
    genre = message.text.lower()
    headers = {"X-API-KEY": API_KEY}
    params = {"query": genre}
    response = requests.get("https://api.kinopoisk.dev/v1.4/movie/search", headers=headers, params=params).json()

    if response.get("docs"):
        user_results[chat_id] = response["docs"]
        user_index[chat_id] = 0
        send_next_film(chat_id)
    else:
        bot.send_message(chat_id, "Фильмы не найдены. Попробуйте другой жанр.", reply_markup=keyboard_zanr())

def send_next_film(chat_id):
    if chat_id not in user_results or user_index[chat_id] >= len(user_results[chat_id]):
        bot.send_message(chat_id, "Больше фильмов нет. Выберите другой жанр.", reply_markup=keyboard_zanr())
        return

    film = user_results[chat_id][user_index[chat_id]]
    user_index[chat_id] += 1
    film_id = film.get("id")
    title = film.get("name", "Без названия")
    year = film.get("year", "Год неизвестен")
    poster = film.get("poster", {}).get("url", "")
    description = film.get("description", "Нет описания")
    link = f"https://www.kinopoisk.ru/film/{film_id}"
    if len(description) > 800:
        description = description[:800] + "..."
    caption = f"<b>{title}</b>\nГод: {year}\n{description}\nСсылка на фильм:\n{link}"
    if poster:
        bot.send_photo(chat_id, poster, caption=caption, parse_mode="HTML", reply_markup=keyboard_zanr())
    else:
        bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=keyboard_zanr())

@bot.message_handler(func=lambda m: m.text == "Случайный фильм")
def rand_film(message):
    chat_id = message.chat.id
    random_word = random.choice(["мечта", "любовь", "война", "путь", "время", "семья", "память"])
    headers = {"X-API-KEY": API_KEY}
    params = {"query": random_word}
    response = requests.get("https://api.kinopoisk.dev/v1.4/movie/search", headers=headers, params=params).json()

    if response.get("docs"):
        for film in response["docs"][:3]:
            film_id = film.get("id")
            title = film.get("name", "Без названия")
            year = film.get("year", "Год неизвестен")
            poster = film.get("poster", {}).get("url", "")
            description = film.get("description", "Нет описания")
            link = f"https://www.kinopoisk.ru/film/{film_id}"
            if len(description) > 800:
                description = description[:800] + "..."
            caption = f"<b>{title}</b>\nГод: {year}\n{description}\nСсылка на фильм:\n{link}"
            if poster:
                bot.send_photo(chat_id, poster, caption=caption, parse_mode="HTML", reply_markup=keyboard_glavn())
            else:
                bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=keyboard_glavn())
    else:
        bot.send_message(chat_id, "Фильм не найден. Попробуйте изменить запрос.", reply_markup=keyboard_glavn())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)





