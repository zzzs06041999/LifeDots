import sqlite3
from kivy.app import App

def init_db():
    try:
        print("[INFO] Запуск создания базы данных...")
        create_user_table()
        create_notes_table()
        update_notes_table()
        create_habits_table()
        create_saved_habits_table()
        print("[INFO] Все таблицы обновлены.")
    except Exception as e:
        print("[ERROR] Ошибка при инициализации БД:", e)

# Функция для создания таблицы пользовательских привычек
def create_habits_table():
    """Создает таблицу с пользовательскими привычками."""
    try:
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                buttons TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        connection.commit()
    except sqlite3.Error as e:
        print("[ERROR] Ошибка при создании таблицы habits:", e)
    finally:
        connection.close()

def create_saved_habits_table():
    """Создает таблицу для сохраненных привычек."""
    try:
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()
        print("[INFO] Создание таблицы saved_habits...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                habit_name TEXT NOT NULL,
                selected_buttons TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        connection.commit()
        print("[INFO] Таблица saved_habits создана или уже существует.")
    except sqlite3.Error as e:
        print("[ERROR] Ошибка при создании таблицы saved_habits:", e)
    finally:
        connection.close()


# Функция для создания таблицы пользователей
def create_user_table():
    try:
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)
        connection.commit()
    except sqlite3.Error as e:
        print("Ошибка при подключении к базе данных:", e)
    finally:
        connection.close()

# Функция для добавления пользователя
def save_user_to_db(username, password):
    try:
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            if existing_user[0] == password:
                return "Пользователь уже существует с этим паролем."
            else:
                return "Пользователь существует, но пароль не совпадает."
        else:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            connection.commit()
            return "Пользователь успешно зарегистрирован!"
    except sqlite3.Error as e:
        print("Ошибка при добавлении пользователя:", e)
        return "Ошибка при добавлении пользователя."
    finally:
        connection.close()

# Функция для создания таблицы заметок
def create_notes_table():
    """Создает таблицу заметок, если она еще не существует."""
    try:
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                date TEXT NOT NULL,
                note TEXT,
                user_id INTEGER NOT NULL,
                day_rating TEXT,
                emotions TEXT,
                people TEXT,
                weather TEXT,
                PRIMARY KEY (user_id, date),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        connection.commit()
    except sqlite3.Error as e:
        print("Ошибка при создании таблицы заметок:", e)
    finally:
        connection.close()

# Функция для обновления таблицы заметок, добавляя недостающие колонки
def update_notes_table():
    """Обновляет таблицу заметок, добавляя недостающие колонки."""
    connection = sqlite3.connect("app_data.db")
    cursor = connection.cursor()

    # Проверяем и добавляем колонку day_rating
    try:
        cursor.execute("ALTER TABLE notes ADD COLUMN day_rating TEXT")
    except sqlite3.OperationalError:
        print("Колонка 'day_rating' уже существует.")

    # Проверяем и добавляем колонку emotions
    try:
        cursor.execute("ALTER TABLE notes ADD COLUMN emotions TEXT")
    except sqlite3.OperationalError:
        print("Колонка 'emotions' уже существует.")

    # Проверяем и добавляем колонку people
    try:
        cursor.execute("ALTER TABLE notes ADD COLUMN people TEXT")
    except sqlite3.OperationalError:
        print("Колонка 'people' уже существует.")

    # Проверяем и добавляем колонку weather
    try:
        cursor.execute("ALTER TABLE notes ADD COLUMN weather TEXT")
    except sqlite3.OperationalError:
        print("Колонка 'weather' уже существует.")

    connection.commit()
    connection.close()

def save_note_to_db(date, note, user_id, day_rating=None, emotions=None, people=None, weather=None):
    """Сохраняет или обновляет данные заметки."""
    if user_id is None:
        print("Ошибка: текущий пользователь не установлен.")
        return

    connection = sqlite3.connect("app_data.db")
    cursor = connection.cursor()
    try:
        # Запрос с заменой данных, если уже существует запись для этой даты и пользователя
        cursor.execute("""
            INSERT OR REPLACE INTO notes (user_id, date, note, day_rating, emotions, people, weather)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, date, note, day_rating, emotions, people, weather))

        connection.commit()
        print(f"Данные для {date} пользователя {user_id} сохранены.")
    except sqlite3.Error as e:
        print("Ошибка при сохранении заметки:", e)
    finally:
        connection.close()

def get_note_from_db(date):
    app = App.get_running_app()
    user_id = app.current_user_id
    print(f"[DEBUG] Получение заметки для user_id={user_id}, date={date}")

    if user_id is None:
        print("[ERROR] User is not logged in!")
        return {}

    connection = sqlite3.connect("app_data.db")
    cursor = connection.cursor()
    try:
        cursor.execute(""" 
            SELECT note, day_rating, emotions, people, weather 
            FROM notes 
            WHERE user_id = ? AND date = ? 
        """, (user_id, date))
        result = cursor.fetchone()

        print(f"[DEBUG] Результат запроса: {result}")

        if result:
            return {
                "note": result[0] if result[0] else "",
                "day_rating": result[1] if result[1] else "",
                "emotions": result[2] if result[2] else "",
                "people": result[3] if result[3] else "",
                "weather": result[4] if result[4] else ""
            }
        print(result)
        return {}

    except sqlite3.Error as e:
        print("[ERROR] Ошибка при загрузке заметки:", e)
        return {}
    finally:
        connection.close()

if __name__ == "__main__":
    print("[INFO] Запуск инициализации базы данных...")
    init_db()
    print("[INFO] Скрипт завершил выполнение.")



