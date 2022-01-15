from telegram.ext import Updater, CommandHandler, CallbackContext
from decouple import config
import random


def load_jokes() -> None:
    with open('jokes.txt', 'r', encoding='UTF-8') as JokesFile:
        jokes = JokesFile.read().split('~')
        global Jokes
        Jokes = list(jokes)


channel_interval = dict()


def set_interval(chat_id, interval = 7200) -> None:
    channel_interval[chat_id] = interval


def get_interval(chat_id) -> int:
    if chat_id in channel_interval:
        return channel_interval[chat_id]
    return config('DEFAULT_INTERVAL')


# Команда interval
def interval(update, context) ->None:
    chat_id = update.message.chat_id
    try:
        interval = int(context.args[0])
    except IndexError:
        update.message.reply_text('Передайте интервал в секундах!')
        return

    if interval < 0:
        update.message.reply_text('В прошлое шутить я пока не умею...')
        return

    update.message.reply_text(f'Буду присылать шутки каждые {interval} секунд.')
    channel_interval[chat_id] = interval


# Команда start
def start(update, context) -> None:
    chat_id = update.message.chat_id
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if current_jobs:
        update.message.reply_text("Уже готовлю вам шутки.")
    else:
        create_job(chat_id, context)


def create_job(chat_id, context) -> None:
    context.job_queue.run_repeating(joke_job, get_interval(chat_id), context=chat_id, name=str(chat_id))


# Команда joke
def joke(update, context) -> None:
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    make_joke(chat_id, context)
    if job_removed:
        create_job(chat_id, context)


def make_joke(chat_id, context) -> None:
    joke = get_random_joke()
    context.bot.send_message(chat_id, text=joke)


# Команда stop
def stop(update, context) -> None:
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = 'Понял умолкаю...' if job_removed else 'А я и не собирался шутить!'
    update.message.reply_text(text)
    del channel_interval[chat_id]


def get_random_joke() -> str:
    ri = random.choice(Jokes)
    #ri = random.randrange(0, len(Jokes), 1)
    return ri

# Команда update
def update(update, context):
    chat_id = update.message.chat_id
    load_jokes()
    context.bot.send_message(chat_id, text="Обновил шутки.")


def remove_job_if_exists(name, context) -> bool:
    """
       Удаляет задание с заданным именем.
       Возвращает, было ли задание удалено
    """
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def joke_job(context: CallbackContext) -> None:
    chat_id = context.job.context
    make_joke(chat_id, context)


def main():
    load_jokes()
    updater = Updater(config('BOT_TOKEN'))
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('stop', stop))
    dp.add_handler(CommandHandler('joke', joke))
    dp.add_handler(CommandHandler('interval', interval))
    dp.add_handler(CommandHandler('update', update))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()