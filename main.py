import telebot
import random
from telebot import types
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

bot = telebot.TeleBot('5221238098:AAH-npa53iKoxwghCGNr0IXZsvvwgAVCGJE')

##############################
class DataBase:
        def __init__(self):
            cluster = MongoClient("mongodb+srv://user:12345@cluster0.yatjx.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
            self.db = cluster["bdBot"]
            self.users = self.db["Users"]
            self.questions = self.db["Test"]
            self.questions_count = len(list(self.questions.find({})))

        def get_user(self, chat_id):
            user = self.users.find_one({"chat_id": chat_id})
            if user is not None:
                return user
            user = {
                "chat_id": chat_id,
                "is_passing": False,
                "is_passed": False,
                "question_index": None,
                "answers": []
            }
            self.users.insert_one(user)
            return user

        def set_user(self, chat_id, update):
            self.users.update_one({"chat_id": chat_id}, {"$set": update})

        def get_question(self, index):
            return self.questions.find_one({"id": index})

db = DataBase()



# @bot.message_handler(commands=["start"])
# def start(message):
# 	user = db.get_user(message.chat.id)

# 	if user["is_passed"]:
# 		bot.send_message(message.from_user.id, "Вы уже прошли эту викторину. Второй раз пройти нельзя 😥")
# 		return

# 	if user["is_passing"]:
# 		return

# 	db.set_user(message.chat.id, {"question_index": 0, "is_passing": True})

# 	user = db.get_user(message.chat.id)
# 	post = get_question_message(user)
# 	if post is not None:
# 		bot.send_message(message.from_user.id, post["text"], reply_markup=post["keyboard"])


##########################################

@bot.message_handler(commands=['start'])
def start(message):
    mess = f'Привет, <b>{message.from_user.first_name}</b>, меня создал Леша, потому что ему было очень скучно'

    # keyboard
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Игра в кости")
    item2 = types.KeyboardButton("Правда или ложь: 10 фактов о Леше")
    item3 = types.KeyboardButton("Рассказать анекдот")
    markup.add(item1, item2, item3)
    bot.send_message(message.chat.id, mess, parse_mode='html', reply_markup=markup)

@bot.message_handler(commands=['help'])
def help(message):
    mess = f'На данный момент я умею выполнять две команды(они есть в меню снизу слева), а также два прикола(кнопки которые ты видишь снизу). Если что-то не работает, напишите Леше, скорее всего он сам это сломал'
    bot.send_message(message.chat.id, mess, parse_mode='html')

@bot.message_handler(content_types=['text'])
def get_user_text(message):
    if message.text == 'Игра в кости':
        # keyboard
        markup = types.InlineKeyboardMarkup(row_width=2)
        item1 = types.InlineKeyboardButton("Бросить кости", callback_data='toss')
        item2 = types.InlineKeyboardButton("Не хочу", callback_data='noToss')
        markup.add(item1, item2)
        bot.send_message(message.chat.id,
                         "Игра очень простая, каждый из нас кинет пару игральных костей, у кого сумма очков больше, тот крутой",
                         parse_mode='html', reply_markup=markup)
    elif message.text == 'Правда или ложь: 10 фактов о Леше':
        user = db.get_user(message.chat.id)

        if user["is_passed"]:
            bot.send_message(message.from_user.id, "Вы уже прошли эту викторину. Второй раз пройти нельзя 😥")
            return

        if user["is_passing"]:
            return

        db.set_user(message.chat.id, {"question_index": 0, "is_passing": True})

        user = db.get_user(message.chat.id)
        post = get_question_message(user)
        if post is not None:
            bot.send_message(message.from_user.id, post["text"], reply_markup=post["keyboard"])



    elif message.text == 'Рассказать анекдот':
        #url = 'https://anekdotbar.ru/'
        #response = requests.get(url)
        #soup = BeautifulSoup(response.text, 'lxml')
        #quotes = soup.find_all('div', class_='tecst')
        #randomFun = random.randint(0, len(quotes)-1)
        #mess = quotes[randomFun].text.split("\n")
        #bot.send_message(message.chat.id, mess[1], parse_mode='html')
        bot.send_message(message.chat.id, "Это пока не работает((", parse_mode='html')
    elif message.text == "Ку" or message.text == "Привет":
        bot.send_message(message.chat.id, "Ну привет ", parse_mode='html')
    else:
        bot.send_message(message.chat.id, "Сори, я не понимаю", parse_mode='html')


@bot.callback_query_handler(func=lambda query: query.data.startswith("?ans"))
def answered(query):
    user = db.get_user(query.message.chat.id)

    if user["is_passed"] or not user["is_passing"]:
        return

    user["answers"].append(int(query.data.split("&")[1]))
    db.set_user(query.message.chat.id, {"answers": user["answers"]})

    post = get_answered_message(user)
    if post is not None:
        bot.edit_message_text(post["text"], query.message.chat.id, query.message.id, reply_markup=post["keyboard"])

@bot.callback_query_handler(func=lambda query: query.data == "?next")
def next(query):
    user = db.get_user(query.message.chat.id)

    if user["is_passed"] or not user["is_passing"]:
        return

    user["question_index"] += 1
    db.set_user(query.message.chat.id, {"question_index": user["question_index"]})

    post = get_question_message(user)
    if post is not None:
        bot.edit_message_text(post["text"], query.message.chat.id, query.message.id, reply_markup=post["keyboard"])


def get_question_message(user):
    if user["question_index"] == db.questions_count:
        count = 0
        for question_index, question in enumerate(db.questions.find({})):
            if question["correct"] == user["answers"][question_index]:
                count += 1
        percents = round(100 * count / db.questions_count)

        if percents < 30:
            smile = "😥"
        elif percents < 60:
            smile = "😐"
        elif percents < 85:
            smile = "😀"
        else:
            smile = "😎"

        text = f"Вы ответили правильно на {percents}% вопросов {smile}"

        db.set_user(user["chat_id"], {"is_passed": True, "is_passing": False})

        return {
            "text": text,
            "keyboard": None
        }

    question = db.get_question(user["question_index"])

    if question is None:
        return

    keyboard = telebot.types.InlineKeyboardMarkup()
    for answer_index, answer in enumerate(question["answers"]):
        keyboard.row(telebot.types.InlineKeyboardButton(f"{chr(answer_index + 97)}) {answer}", callback_data=f"?ans&{answer_index}"))

    text = f"Вопрос №{user['question_index'] + 1}\n\n{question['text']}"

    return {
        "text": text,
        "keyboard": keyboard
    }

def get_answered_message(user):
    question = db.get_question(user["question_index"])

    text = f"Вопрос №{user['question_index'] + 1}\n\n{question['text']}\n"

    for answer_index, answer in enumerate(question["answers"]):
        text += f"{chr(answer_index + 97)}) {answer}"

        if answer_index == question["correct"]:
            text += " ✅"
        elif answer_index == user["answers"][-1]:
            text += " ❌"

        text += "\n"

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(telebot.types.InlineKeyboardButton("Далее", callback_data="?next"))

    return {
        "text": text,
        "keyboard": keyboard
    }

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    # answ = 0
    # res = 0
    try:
        if call.message:
            if call.data == 'toss':
                botToss1 = random.randint(0, 100) % 6 + 1
                botToss2 = random.randint(0, 100) % 6 + 1
                yourToss1 = random.randint(0, 100) % 6 + 1
                yourToss2 = random.randint(0, 100) % 6 + 1
                botRes = botToss1 + botToss2
                yourRes = yourToss1 + yourToss2
                if botRes > yourRes:
                    # keyboard
                    markup = types.InlineKeyboardMarkup(row_width=2)
                    item1 = types.InlineKeyboardButton("Давай", callback_data='toss')
                    item2 = types.InlineKeyboardButton("Не хочу", callback_data='noToss')
                    markup.add(item1, item2)
                    mess = f'🎲 У тебя выпало: {yourToss1} и {yourToss2}\n🎲 У меня выпало: {botToss1} и {botToss2} \nЯ победил 😊\n Сыграем еще раз?'
                    bot.send_message(call.message.chat.id, mess, parse_mode='html', reply_markup=markup)
                elif botRes < yourRes:
                    # keyboard
                    markup = types.InlineKeyboardMarkup(row_width=2)
                    item1 = types.InlineKeyboardButton("Давай", callback_data='toss')
                    item2 = types.InlineKeyboardButton("Не хочу", callback_data='noToss')
                    markup.add(item1, item2)
                    mess = f'🎲 У тебя выпало: {yourToss1} и {yourToss2} \n🎲 У меня выпало: {botToss1} и {botToss2} \nТы победил 😊\nСыграем еще раз?'
                    bot.send_message(call.message.chat.id, mess, parse_mode='html', reply_markup=markup)
                elif botRes == yourRes:
                    # keyboard
                    markup = types.InlineKeyboardMarkup(row_width=2)
                    item1 = types.InlineKeyboardButton("Давай", callback_data='toss')
                    item2 = types.InlineKeyboardButton("Не хочу", callback_data='noToss')
                    markup.add(item1, item2)
                    mess = f'🎲 У тебя выпало: {yourToss1} и {yourToss2} \n🎲 У меня выпало: {botToss1} и {botToss2} \nНичья 😊\nСыграем еще раз?'
                    bot.send_message(call.message.chat.id, mess, parse_mode='html', reply_markup=markup)
                # remove inline buttons
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Игра в кости", reply_markup=None)

            elif call.data == 'noToss' or call.data == 'noGo':
                bot.send_message(call.message.chat.id, 'Ну, может в другой раз 😢')
                # remove inline buttons
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text="Отмена действия", reply_markup=None)

            # elif call.data == 'go':
            #     user = db.get_user(message.chat.id)
            #     if user["is_passed"]:
            #         bot.send_message(message.from_user.id, "Вы уже прошли эту викторину. Второй раз пройти нельзя 😥")
            #         return

            #     if user["is_passing"]:
            #         return

            #     db.set_user(message.chat.id, {"question_index": 0, "is_passing": True})
            #     user = db.get_user(message.chat.id)
            #     post = get_question_message(user)
            #     if post is not None:
            #         bot.send_message(message.from_user.id, post["text"], reply_markup=post["keyboard"])
                #bot.send_message(call.message.chat.id, 'Это пока не работает((', parse_mode='html')
                #bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                #                          text="Сорян", reply_markup=None)
                #while answ < 3:
                #    #keyboard
                #    markup = types.InlineKeyboardMarkup(row_width=2)
                #    item1 = types.InlineKeyboardButton("Правда", callback_data='trueAnswer')
                #    item2 = types.InlineKeyboardButton("Ложь", callback_data='falseAnswer')
                #    markup.add(item1, item2)
                #    if answ == 0:
                #        bot.send_message(call.message.chat.id, 'Вопрос 1', parse_mode='html', reply_markup=markup)
                #    elif answ == 1:
                #        bot.send_message(call.message.chat.id, 'Вопрос 2', parse_mode='html', reply_markup=markup)
                #    elif answ == 2:
                #        bot.send_message(call.message.chat.id, 'Вопрос 3', parse_mode='html', reply_markup=markup)
            #elif call.data == 'trueAnswer':
            #    res = res + 1
            #    answ = answ + 1
            #    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
            #                          text="Верно", reply_markup=None)
            #elif call.data == 'falseAnswer':
            #    answ = answ + 1
            #    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
            #                          text="Неверно", reply_markup=None)

            # show alert
            # bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text="ЭТО ТЕСТОВОЕ УВЕДОМЛЕНИЕ!!11")

    except Exception as e:
        print(repr(e))


bot.polling()
