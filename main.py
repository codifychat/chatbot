# Стандартна бібліотека
import asyncio
import datetime
import logging
import os
import sqlite3

from contextlib import contextmanager
from logging.handlers import TimedRotatingFileHandler

# Сторонні бібліотеки
import colorama
import nest_asyncio
from colorama import Fore, Style
from dotenv import load_dotenv

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

load_dotenv()  # Завантажуємо змінні середовища
colorama.init()  # Запускаємо colorama для кольорового виведення в консоль

# Власний рівень логування для успішних операцій (між INFO та WARNING)
SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


# Кастомний хендлер для виведення в консоль з кольорами
# Маю сказати, що цей клас дуже корисний, цікаво було писати його
class ColoredConsoleHandler(logging.StreamHandler):
    def emit(self, record):
        # Визначаємо колір залежно від рівня логування
        if record.levelno >= logging.ERROR:
            color = Fore.RED
        elif record.levelno == SUCCESS_LEVEL:
            color = Fore.GREEN
        elif record.levelno >= logging.WARNING:
            color = Fore.YELLOW
        else:
            color = Fore.WHITE

        # Додаємо колір до повідомлення
        record.msg = f"{color}{record.msg}{Style.RESET_ALL}"
        super().emit(record)


# Метод для створення логу з рівнем SUCCESS
def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL):
        self._log(SUCCESS_LEVEL, message, args, **kwargs)


# Додаємо метод success до Logger
logging.Logger.success = success


def setup_logging():
    # Створюємо папку для логів
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    # Сьогоднішня дата для імені файлу
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(logs_dir, f"{today}.log")

    # Формат логів: коли вони відбуваються і що саме сталося
    log_format = "%(asctime)s - [%(levelname)s] - %(message)s"
    date_format = "%d-%m-%Y, %H:%M:%S"

    # Налаштовуємо логер
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Видаляємо старі хендлери, якщо є
    if logger.handlers:
        logger.handlers.clear()

    # Додаємо ротацію файлів логів
    # Буде створювати новий файл щодня і зберігати їх за останні 30 днів
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(file_handler)

    # Додаємо наш красивий кольоровий вивід в консоль
    console_handler = ColoredConsoleHandler()
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(console_handler)

    return logger


# Ініціалізуємо логер
logger = setup_logging()

from contextlib import contextmanager

def connect_db():
    try:
        # Підключення до бази даних, результати як словники
        conn = sqlite3.connect("data/codify.db")
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Помилка підключення до БД: {e}")
        raise

@contextmanager
def db_connection():
    conn = connect_db()
    try:
        yield conn
    finally:
        conn.close()

def initialize_db():
    try:
        # Якщо БД немає, створюємо її
        if not os.path.exists("DB_PATH"):
            os.makedirs("data", exist_ok=True)
            conn = connect_db()
            cursor = conn.cursor()

            # Виконуємо скрипт створення схеми з файлу
            with open("sql/schema.sql", "r", encoding="utf-8") as f:
                cursor.executescript(f.read())
            conn.commit()
            conn.close()
            logger.success("Базу даних створено та ініціалізовано")
        else:
            logger.success("База даних вже існує")
    except Exception as e:
        logger.error(f"Помилка ініціалізації БД: {e}")


def seed_db():
    try:
        # Заповнюємо БД початковими даними курсів
        conn = connect_db()
        cursor = conn.cursor()
        with open("sql/seed_courses.sql", "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
        conn.commit()
        conn.close()
        logger.success("Дані курсів додано")
    except Exception as e:
        logger.error(f"Помилка заповнення БД: {e}")


def register_user(telegram_id, username):
    try:
        # Реєструємо користувача в базі або ігноруємо, якщо вже є
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO users (telegram_id, username)
            VALUES (?, ?)
        """, (telegram_id, username))
        conn.commit()
        conn.close()
        logger.info(f"Користувач зареєстрований: {username} ({telegram_id})")
    except Exception as e:
        logger.error(f"Помилка реєстрації: {e}")


def get_course_names():
    try:
        # Отримуємо список активних курсів
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM courses WHERE active = 1")
        courses = cursor.fetchall()
        conn.close()
        return [course["name"] for course in courses]
    except sqlite3.Error as e:
        logger.error(f"Помилка отримання курсів: {e}")
        return []


# Додано словники для контенту курсів
from data.course_data import COURSE_CONTENT

# Функція для кнопок навігації у курсі
def get_navigation_keyboard():
    # Ні, треба докинути ще кнопку "до змісту"... треба це запам'ятати на майбутнє
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◀️ Назад", callback_data="prev"),
         InlineKeyboardButton("▶️ Вперед", callback_data="next")],
        [InlineKeyboardButton("🔙 Вийти до меню Курси", callback_data="exit_course")]
    ])


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Головне меню з основними опціями
    keyboard = [
        ["📚 Курси", "👤 Профіль"],
        ["ℹ️ Про нас"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Будь ласка, виберіть опцію з меню:", reply_markup=reply_markup)
    logger.info(f"Користувач {update.effective_user.id} відкрив головне меню")


async def courses_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Меню розділу курсів
    keyboard = [
        ["📥 Вибір курсів", "▶️ Продовжити/Розпочати навчання"],
        ["🔙 Назад до головного меню"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    # Якщо функція викликана через callback_query
    if update.callback_query:
        await update.callback_query.message.reply_text("Оберіть дію для курсу:", reply_markup=reply_markup)
        logger.info(f"Користувач {update.effective_user.id} повернувся до меню курсів через callback")
    else:
        await update.message.reply_text("Оберіть дію для курсу:", reply_markup=reply_markup)
        logger.info(f"Користувач {update.effective_user.id} зайшов у меню курсів")


async def start_course_learning(update: Update, context: ContextTypes.DEFAULT_TYPE, course_name: str):
    # Запам'ятовуємо, де зараз користувач в курсі
    context.user_data["course_position"] = 0
    context.user_data["course_name"] = course_name

    if course_name in COURSE_CONTENT:
        try:
            conn = connect_db()
            cursor = conn.cursor()
            # Перевіряємо, чи є картинка до курсу
            cursor.execute("SELECT image_url FROM courses WHERE name = ?", (course_name,))
            row = cursor.fetchone()
            conn.close()

            image_url = row["image_url"] if row else None

            # Беремо перший розділ курсу
            text = COURSE_CONTENT[course_name][0]

            if image_url:
                # Фото курсу окремо надсилаємо
                await update.message.reply_photo(photo=image_url)

            # Текст з кнопками навігації
            await update.message.reply_text(
                text,
                parse_mode="Markdown",
                reply_markup=get_navigation_keyboard()
            )
            logger.info(f"Користувач {update.effective_user.id} почав вивчення курсу: {course_name}")

        except Exception as e:
            logger.error(f"Помилка при старті курсу: {e}")
            await update.message.reply_text("🚫 Сталася помилка при завантаженні курсу.")
    else:
        logger.warning(f"Курс {course_name} ще не реалізований")
        await update.message.reply_text("⛔ Навчання для цього курсу ще не реалізовано.")


# Обробник для кнопок навігації в курсі
async def handle_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Перевіряємо, чи вибрано курс
    if "course_name" not in context.user_data:
        await query.edit_message_text("Помилка: курс не вибрано")
        logger.error(f"Помилка навігації: курс не вибрано для користувача {update.effective_user.id}")
        return

    course_name = context.user_data["course_name"]
    position = context.user_data.get("course_position", 0)
    old_position = position

    # Обробляємо натискання різних кнопок
    if query.data == "next":
        # Перехід вперед, але не далі останнього розділу
        position = min(position + 1, len(COURSE_CONTENT[course_name]) - 1)
    elif query.data == "prev":
        # Перехід назад, але не раніше першого розділу
        position = max(position - 1, 0)
    elif query.data == "exit_course":
        # Вихід з курсу
        await query.message.delete()
        await courses_menu(update, context)
        logger.info(f"Користувач {update.effective_user.id} вийшов з курсу: {course_name}")
        return

    # Якщо позиція змінилася, оновлюємо вміст
    if position != old_position:
        context.user_data["course_position"] = position
        text = COURSE_CONTENT[course_name][position]

        # Оновлюємо повідомлення з новим вмістом і тими ж кнопками
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=get_navigation_keyboard()
        )
        logger.info(f"Користувач {update.effective_user.id} перейшов до розділу {position} у курсі {course_name}")


async def manage_courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Отримуємо список активних курсів із БД
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM courses WHERE active = 1")
        courses = cursor.fetchall()

        if courses:
            # Формуємо клавіатуру зі списком курсів і кнопкою "Назад"
            keyboard = [[course["name"]] for course in courses] + [["🔙 Назад до меню Курси"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Оберіть курс зі списку:", reply_markup=reply_markup)
            logger.info(f"Користувач {update.effective_user.id} відкрив вибір курсів")
        else:
            await update.message.reply_text("Наразі немає доступних курсів.")
            logger.warning("Нема доступних курсів для вибору")

        conn.close()
    except Exception as e:
        logger.error(f"Помилка при керуванні курсами: {e}")


async def continue_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Знаходимо курси, на які підписаний користувач
        user_id = update.effective_user.id
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.name
            FROM user_courses uc
            JOIN courses c ON uc.course_id = c.id
            JOIN users u ON uc.user_id = u.id
            WHERE u.telegram_id = ?
        """, (user_id,))
        subscriptions = cursor.fetchall()
        conn.close()

        # Якщо ще нема підписок, пропонуємо вибрати курс
        if not subscriptions:
            await update.message.reply_text("Немає підписок. 📥 Спочатку оберіть курс.")
            logger.info(f"Користувач {user_id} не має підписок на курси")
            return

        # Якщо є лише один курс, відразу переходимо до нього
        if len(subscriptions) == 1:
            course_name = subscriptions[0][0]
            await update.message.reply_text(f"🔁 Ви продовжуєте курс: {course_name}")
            await start_course_learning(update, context, course_name)
            return

        # Якщо користувач підписаний на кілька курсів, даємо вибір
        keyboard = [[course[0]] for course in subscriptions] + [["🔙 Назад до меню Курси"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Оберіть курс для продовження:", reply_markup=reply_markup)
        logger.info(f"Користувач {user_id} обирає з кількох курсів")

    except Exception as e:
        logger.error(f"Помилка продовження навчання: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Початковий хендлер при запуску бота
        user_id = update.effective_user.id
        username = update.effective_user.username
        register_user(user_id, username)  # Реєструємо в базі

        await update.message.reply_text("Ласкаво просимо до Codify!")
        await main_menu(update, context)
        logger.success(f"Новий користувач запустив бота: {username} ({user_id})")
    except Exception as e:
        logger.error(f"Помилка команди /start: {e}")


async def about_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Простий розділ "Про нас" з кнопкою на веб-сайт
    text = "Codify — освітня платформа для вивчення програмування 🎓"
    button = [[InlineKeyboardButton("🌐 Вебсайт", url="https://github.com/codifychat/chatbot")]]
    reply_markup = InlineKeyboardMarkup(button)
    await update.message.reply_text(text, reply_markup=reply_markup)
    logger.info(f"Користувач {update.effective_user.id} відкрив розділ 'Про нас'")


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Отримуємо дані профілю з БД
        user_id = update.effective_user.id
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
        user = cursor.fetchone()

        if user:
            # Формуємо текст профілю з даними
            profile_text = (
                f"ID: {user_id}\n"
            )
            await update.message.reply_text(profile_text)
            logger.info(f"Користувач {user_id} переглянув профіль")
        else:
            await update.message.reply_text("Профіль не знайдено.")
            logger.warning(f"Профіль не знайдено для користувача {user_id}")

        conn.close()
    except Exception as e:
        logger.error(f"Помилка показу профілю: {e}")


async def subscribe_to_course(telegram_id, course_name):
    try:
        # Підписуємо користувача на курс
        conn = connect_db()
        cursor = conn.cursor()

        # Отримуємо ID користувача
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
        # Отримуємо ID курсу
        cursor.execute("SELECT id FROM courses WHERE name = ?", (course_name,))
        course = cursor.fetchone()

        # Якщо знайшли і користувача і курс, створюємо зв'язок
        if user and course:
            cursor.execute("""
                INSERT OR IGNORE INTO user_courses (user_id, course_id)
                VALUES (?, ?)
            """, (user["id"], course["id"]))
            conn.commit()
            logger.success(f"Користувач {telegram_id} підписався на курс: {course_name}")
        conn.close()
    except Exception as e:
        logger.error(f"Помилка підписки: {e}")


# Заглушка для next_lesson, якщо потрібна
async def next_lesson(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ця функція поки не реалізована. Скористайтесь режимом читання курсу.")
    logger.info(f"User {update.effective_user.id} attempted to use next_lesson function")


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        user_id = update.effective_user.id
        logger.info(f"Button pressed by user {user_id}: {text}")

        if text == "📚 Курси":
            await courses_menu(update, context)
        elif text == "👤 Профіль":
            await show_profile(update, context)
        elif text == "📥 Вибір курсів":
            await manage_courses(update, context)
        elif text == "▶️ Продовжити/Розпочати навчання":
            await continue_learning(update, context)
        elif text == "🔙 Назад до меню Курси":
            await courses_menu(update, context)
        elif text == "🔙 Назад до головного меню":
            await main_menu(update, context)
        elif text == "ℹ️ Про нас":
            await about_us(update, context)
        elif text in get_course_names():
            await subscribe_to_course(user_id, text)
            context.user_data["selected_course"] = text
            await update.message.reply_text(f"✅ Ви підписались на курс: {text}")
            # Додаємо опцію для запуску курсу відразу після підписки
            keyboard = [
                ["▶️ Розпочати курс зараз"],
                ["🔙 Назад до меню Курси"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("Бажаєте розпочати навчання зараз?", reply_markup=reply_markup)
        elif text == "▶️ Розпочати курс зараз":
            if "selected_course" in context.user_data:
                course_name = context.user_data["selected_course"]
                await start_course_learning(update, context, course_name)
            else:
                await update.message.reply_text("❓ Курс не вибрано. Спочатку виберіть курс.")
                logger.warning(f"User {user_id} tried to start course without selecting one")
        elif text == "➡️ Наступний урок":
            await next_lesson(update, context)
        else:
            await update.message.reply_text("❓ Команду не розпізнано. Будь ласка, скористайтесь меню.")
            logger.warning(f"Unknown command from user {user_id}: {text}")
    except Exception as e:
        logger.error(f"Handle Buttons Error: {e}")


async def main():
    try:
        initialize_db()
        seed_db()

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            logger.error("TELEGRAM_BOT_TOKEN відсутній!")
            return

        app = ApplicationBuilder().token(bot_token).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
        # Додаємо обробник для кнопок навігації
        app.add_handler(CallbackQueryHandler(handle_navigation))

        logger.success("Application started successfully")
        await app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Main Bot Error: {e}")


if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
