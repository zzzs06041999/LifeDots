import kivy
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
import sqlite3
from db_manager import get_note_from_db, save_note_to_db
import re
import locale
from kivy.properties import StringProperty, ObjectProperty
import hashlib
from datetime import datetime, timedelta
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.animation import Animation
from kivy.lang import Builder
from kivy.uix.slider import Slider
from functools import partial

locale.setlocale(locale.LC_TIME, 'Russian_Russia.1251')

def init_db():
    connection = sqlite3.connect("app_data.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
        """)

    # Таблица заметок с уникальным сочетанием user_id и date
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        note TEXT,
        UNIQUE(user_id, date),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

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
    connection.close()

# Экран входа
class LoginScreen(Screen):
    error_message = StringProperty("")  # Создаём переменную для текста ошибки

    def register(self):
        self.manager.current = 'registration'

    def handle_login(self):
        """Обрабатывает процесс входа в систему."""
        username = self.ids.username_input.text.strip()
        password = self.ids.password_input.text.strip()

        if not username or not password:
            self.show_error("Пожалуйста, заполните все поля.")
            return

        # Проверка существования пользователя и правильности пароля
        if not self.validate_user(username, password):
            self.show_error("Неверное имя пользователя или пароль.")
            return

        # Успешный вход
        self.show_success("Вход успешен!")

        # Устанавливаем current_user_id
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        connection.close()

        if result:
            user_id = result[0]
            App.get_running_app().on_user_login(user_id)  # Устанавливаем ID пользователя в приложении

        # Переход на экран календаря
        self.manager.current = 'calendar'

    def validate_user(self, username, password):
        """Проверка существования пользователя и пароля в базе данных."""
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        connection.close()

        if result:
            stored_password = result[0]
            # Сравниваем введённый пароль с хэшированным паролем в базе
            return self.check_password(stored_password, password)
        return False

    def check_password(self, stored_password, password):
        """Проверка правильности пароля."""
        return stored_password == self.hash_password(password)

    def hash_password(self, password):
        """Хэширование пароля с использованием SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def show_error(self, message):
        """Показывает окно ошибки с кастомным стилем."""
        popup = self.create_popup("ErrorPopup", message)
        popup.open()

    def show_success(self, message):
        """Показывает окно успеха с кастомным стилем."""
        popup = self.create_popup("SuccessPopup", message)
        popup.open()

    def create_popup(self, popup_class, message):
        """Создаёт окно с уведомлением и применяет стили."""

        # Цвета из палитры
        light_brown = (0.949, 0.808, 0.635, 1)  # светлый бежевый
        dark_brown = (0.251, 0.161, 0.078, 1)  # темно-коричневый
        button_brown = (0.451, 0.298, 0.161, 1)  # коричневый
        light_brown_button = (0.851, 0.675, 0.510, 1)  # светлый оттенок коричневого

        if popup_class == "ErrorPopup":
            popup = Popup(title="Ошибка", size_hint=(0.8, 0.4), background_color=light_brown)
            content = BoxLayout(orientation="vertical", padding=10, spacing=20)

            # Создание и стилизация текста сообщения
            label = Label(
                text=message,
                color=(1, 1, 1, 1),
                font_size='18sp',
                halign='center',
                valign='middle'
            )
            content.add_widget(label)

            # Кнопка закрытия попапа
            close_button = Button(text="Закрыть", background_normal='', background_color=dark_brown,
                                  color=(1, 1, 1, 1))
            close_button.bind(on_press=popup.dismiss)
            content.add_widget(close_button)

            popup.content = content

        elif popup_class == "SuccessPopup":
            popup = Popup(title="Успех", size_hint=(0.8, 0.4), background_color=light_brown)
            content = BoxLayout(orientation="vertical", padding=10, spacing=20)

            # Создание и стилизация текста сообщения
            label = Label(
                text=message,
                color=(1, 1, 1, 1),
                font_size='18sp',
                halign='center',
                valign='middle'
            )
            content.add_widget(label)

            # Кнопка закрытия попапа
            close_button = Button(text="Закрыть", background_normal='', background_color=dark_brown,
                                  color=(1, 1, 1, 1))
            close_button.bind(on_press=popup.dismiss)
            content.add_widget(close_button)

            popup.content = content

        return popup

# Экран регистрации
class RegistrationScreen(Screen):
    error_message = StringProperty("")  # Создаём переменную для текста ошибки

    def handle_register(self):
        """Обрабатывает регистрацию нового пользователя."""
        username = self.ids.username_input.text.strip()
        password = self.ids.password_input.text.strip()

        if not self.validate_username(username):
            self.show_error(
                "Имя пользователя должно быть длиной от 3 до 20 символов, содержать только буквы или цифры."
            )
            return

        if not self.validate_password(password):
            self.show_error(
                "Пароль должен быть длиной от 6 до 20 символов, содержать только буквы, цифры или символы, без пробелов."
            )
            return

        # Сохраняем нового пользователя в базу данных
        hashed_password = self.hash_password(password)
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            connection.commit()

            # Получаем ID нового пользователя и устанавливаем current_user_id
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            if result:
                App.get_running_app().current_user_id = result[0]  # Устанавливаем ID нового пользователя
                print(f"Регистрация успешна. ID пользователя: {result[0]}")

            # Очищаем поля ввода
            self.ids.username_input.text = ""
            self.ids.password_input.text = ""

            # Переходим на экран календаря
            self.manager.current = 'calendar'
        except sqlite3.IntegrityError:
            self.show_error("Имя пользователя уже занято.")
        finally:
            connection.close()

    def validate_username(self, username):
        # Проверка имени пользователя с использованием букв латиницы и кириллицы
        return bool(re.match(r'^[A-Za-zА-Яа-я0-9]{3,20}$', username))

    def validate_password(self, password):
        # Проверка пароля с поддержкой кириллицы и специальных символов
        return bool(
            re.match(
                r'^[A-Za-zА-Яа-я0-9!@#$%^&*()_+=\-{}\[\]:;"\'<>,.?/~`|]{6,20}$',
                password
            )
        )

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def save_to_db(self, username, password):
        """Сохраняет пользователя в базу данных с хэшированным паролем."""
        hashed_password = self.hash_password(password) # Хэшируем пароль перед сохранением
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            connection.commit()
            self.show_success("Регистрация прошла успешно!")
            return True
        except sqlite3.IntegrityError:
            self.show_error("Имя пользователя уже занято.")
            return False
        finally:
            connection.close()

    def show_error(self, message):
        """Показывает окно ошибки с кастомным стилем."""
        popup = self.create_popup("ErrorPopup", message)
        popup.open()

    def show_success(self, message):
        """Показывает окно успеха с кастомным стилем."""
        popup = self.create_popup("SuccessPopup", message)
        popup.open()

    def create_popup(self, popup_class, message):
        """Создаёт окно с уведомлением и применяет стили."""

        # Цвета из палитры
        light_brown = (0.949, 0.808, 0.635, 1)  # светлый бежевый
        dark_brown = (0.251, 0.161, 0.078, 1)  # темно-коричневый
        button_brown = (0.451, 0.298, 0.161, 1)  # коричневый
        light_brown_button = (0.851, 0.675, 0.510, 1)  # светлый оттенок коричневого

        if popup_class == "ErrorPopup":
            popup = Popup(title="Ошибка", size_hint=(0.8, 0.4), background_color=light_brown)
            content = BoxLayout(orientation="vertical", padding=10, spacing=20)

            # Создание и стилизация текста сообщения
            label = Label(
                text=message,
                color=(1, 1, 1, 1),  # Белый цвет текста для ошибок
                font_size='18sp',
                halign='center',
                valign='middle'
            )
            content.add_widget(label)

            # Кнопка закрытия попапа
            close_button = Button(text="Закрыть", background_normal='', background_color=dark_brown,
                                  color=(1, 1, 1, 1))
            close_button.bind(on_press=popup.dismiss)
            content.add_widget(close_button)

            popup.content = content

        elif popup_class == "SuccessPopup":
            popup = Popup(title="Успех", size_hint=(0.8, 0.4), background_color=light_brown)
            content = BoxLayout(orientation="vertical", padding=10, spacing=20)

            # Создание и стилизация текста сообщения
            label = Label(
                text=message,
                color=(1, 1, 1, 1),  # Белый цвет текста для успеха
                font_size='18sp',
                halign='center',
                valign='middle'
            )
            content.add_widget(label)

            # Кнопка закрытия попапа
            close_button = Button(text="Закрыть", background_normal='', background_color=button_brown,
                                  color=(1, 1, 1, 1))
            close_button.bind(on_press=popup.dismiss)
            content.add_widget(close_button)

            popup.content = content

        return popup


# Экран главного окна с календарем
class CalendarScreen(Screen):
    current_date = ObjectProperty(datetime.today().strftime('%d %B %Y'))  # Текущая дата

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_date = datetime.today()
        self.display_calendar(self.current_date)

    def display_calendar(self, date):
        """Отображает дни текущего месяца."""
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d")  # Преобразуем строку в datetime

        calendar_grid = self.ids.calendar_grid  # Сетка календаря
        calendar_grid.clear_widgets()

        # Обновляем название месяца
        self.ids.month_label.text = date.strftime("%B %Y")  # Например, "Февраль 2025"

        # Определяем первый и последний день месяца
        first_day_of_month = date.replace(day=1)
        last_day_of_month = (first_day_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        start_day = first_day_of_month.weekday()  # День недели первого дня месяца (0 — понедельник)

        # Пустые ячейки до первого дня месяца
        for _ in range(start_day):
            calendar_grid.add_widget(Label())

        # Дни месяца
        today = datetime.today()
        for day in range(1, last_day_of_month.day + 1):
            day_date = first_day_of_month.replace(day=day)
            day_button = Button(
                text=str(day),
                size_hint_y=None,
                height=50,
                background_color=(0.851, 0.675, 0.510, 1) if day_date.date() != today.date() else (
                    0.451, 0.298, 0.161, 1),  # светло-коричневый фон для дней, кроме сегодняшнего
                color=(1, 1, 1, 1),
            )
            day_button.bind(on_press=self.on_day_selected)
            calendar_grid.add_widget(day_button)

    def show_prev_month(self, instance=None):
        """Переход на предыдущий месяц."""
        self.current_date = (self.current_date.replace(day=1) - timedelta(days=1)).replace(day=1)
        self.display_calendar(self.current_date)

    def show_next_month(self, instance=None):
        """Переход на следующий месяц."""
        self.current_date = (self.current_date + timedelta(days=32)).replace(day=1)
        self.display_calendar(self.current_date)

    def on_day_selected(self, instance):
        """Обработка выбора дня."""
        day = int(instance.text)
        selected_date = self.current_date.replace(day=day)
        print(f"Переход на экран заметок для даты: {selected_date.strftime('%Y-%m-%d')}")
        self.manager.current = 'note'
        self.manager.get_screen('note').set_date(selected_date.strftime("%Y-%m-%d"))


class NoteScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.saved_blocks_layout = None
        self.layout = BoxLayout(orientation='vertical')
        self.date = None
        self.day_rating = None
        self.emotions = set()
        self.people = set()
        self.weather = None
        self.add_widget(self.layout)

    def go_back(self, instance=None):
        """Переход на экран календаря."""
        self.manager.current = 'calendar'

    def set_date(self, date):
        """Устанавливает дату и загружает данные из БД."""
        self.date = date
        note_data = get_note_from_db(self.date)  # Должна быть функция получения данных
        if note_data:
            self.ids.note_input.text = note_data.get('note', '')
            self.day_rating = note_data.get('day_rating')
            self.emotions = set(note_data.get('emotions', '').split(',')) if note_data.get('emotions') else set()
            self.people = set(note_data.get('people', '').split(',')) if note_data.get('people') else set()
            self.weather = note_data.get('weather')
        else:
            self.ids.note_input.text = ""
            self.day_rating = None
            self.emotions = set()
            self.people = set()
            self.weather = None
        self.update_buttons()

    def add_day_buttons(self):
        """Добавляет кнопки для рейтинга дня в day_buttons."""
        ratings = ["Замечательно", "Хорошо", "Обычно", "Грустно", "Плохо"]
        for rating in ratings:
            button = Button(text=rating)
            button.bind(on_press=self.set_day_rating)  # Привязываем обработчик для кнопок
            self.ids.day_buttons.add_widget(button)  # Добавляем кнопку в контейнер day_buttons

    def update_buttons(self):
        """Обновляет цвет кнопок на основе сохраненных данных."""
        brown_color = (0.451, 0.298, 0.161, 1)
        gray_color = (0.949, 0.808, 0.635, 1)

        self.ids.day_buttons.clear_widgets()  # Очистка существующих кнопок

        # Добавляем кнопки заново с обновленным состоянием
        self.add_day_buttons()

        # Проверка наличия id в kv-файле
        if 'day_buttons' in self.ids:
            for btn in self.ids.day_buttons.children:
                btn.background_color = brown_color if btn.text == self.day_rating else gray_color

        if 'emotion_buttons' in self.ids:
            for btn in self.ids.emotion_buttons.children:
                btn.background_color = brown_color if btn.text in self.emotions else gray_color

        if 'people_buttons' in self.ids:
            for btn in self.ids.people_buttons.children:
                btn.background_color = brown_color if btn.text in self.people else gray_color

        if 'weather_container' in self.ids:
            for btn in self.ids.weather_container.children:
                btn.background_color = brown_color if btn.text == self.weather else gray_color

        self.canvas.ask_update()
        print([btn.text for btn in self.ids.day_buttons.children])

    def save_note(self, instance=None):
        """Сохраняет заметку в БД."""
        if not self.date:
            self.show_popup("Ошибка", "Дата не установлена!")
            return

        note = self.ids.note_input.text.strip()
        save_note_to_db(
            self.date,
            note,
            App.get_running_app().current_user_id,
            day_rating=self.day_rating,
            emotions=",".join(self.emotions),
            people=",".join(self.people),
            weather=self.weather
        )
        self.show_popup("Успех", "Данные успешно сохранены!")

    def set_day_rating(self, button):
        """Устанавливает рейтинг дня (одна кнопка)."""
        self.day_rating = button.text
        self.update_buttons()

    def toggle_emotion(self, button):
        """Добавляет или удаляет эмоцию."""
        if button.text in self.emotions:
            self.emotions.remove(button.text)
        else:
            self.emotions.add(button.text)
        self.update_buttons()

    def toggle_people(self, button):
        """Добавляет или удаляет человека."""
        if button.text in self.people:
            self.people.remove(button.text)
        else:
            self.people.add(button.text)
        self.update_buttons()

    def set_weather(self, button):
        """Устанавливает погоду (одна кнопка)."""
        self.weather = button.text
        self.update_buttons()

    def go_to_user_habits(self):
        """Переход на экран пользовательских привычек."""
        self.manager.current = 'user_habits'

    def load_habits(self):
        user_id = App.get_running_app().current_user_id
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()

        cursor.execute("SELECT name, buttons FROM habits WHERE user_id = ?", (user_id,))
        habits = cursor.fetchall()

        connection.close()

        self.saved_blocks_layout.clear_widgets()

        for name, buttons in habits:
            block_label = Label(text=f"Привычка: {name}", font_size='18sp')
            self.saved_blocks_layout.add_widget(block_label)

            button_names = buttons.split(',')
            for btn_name in button_names:
                btn = Button(text=btn_name, size_hint_y=None, height=50)
                self.saved_blocks_layout.add_widget(btn)

    def show_popup(self, title, message):
        """Показывает всплывающее окно с кастомным стилем."""

        # Цвета из вашей палитры
        light_brown = (0.949, 0.808, 0.635, 1)  # светлый бежевый
        dark_brown = (0.251, 0.161, 0.078, 1)  # темно-коричневый
        button_brown = (0.451, 0.298, 0.161, 1)  # коричневый
        light_brown_button = (0.851, 0.675, 0.510, 1)  # светлый оттенок коричневого

        # Контент для попапа
        content = BoxLayout(orientation='vertical', padding=10, spacing=20)

        # Создание и стилизация текста сообщения
        label = Label(
            text=message,
            color=(1, 1, 1, 1),  # Белый цвет текста для контраста
            font_size='18sp',  # Увеличиваем размер шрифта
            halign='center',  # Центрируем текст
            valign='middle'  # Центрируем по вертикали
        )
        content.add_widget(label)

        # Кнопка закрытия попапа
        close_button = Button(text="Закрыть", background_normal='', background_color=dark_brown, color=(1, 1, 1, 1))
        close_button.bind(on_press=lambda x: self.dismiss_popup())
        content.add_widget(close_button)

        # Попап с настроенным стилем
        self.popup = Popup(
            title=title,
            content=content,
            size_hint=(0.6, 0.4),
            background_color=light_brown,
            auto_dismiss=True
        )
        self.popup.open()

    def dismiss_popup(self):
        """Закрывает всплывающее окно и возвращает на экран NoteScreen."""
        if hasattr(self, 'popup') and self.popup:
            self.popup.dismiss()
            # Переключаемся на экран календаря или другой экран
            self.manager.current = 'calendar'  # Или на нужный экран

class UserHabitsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self.create_button = self.ids.get("create_button", None)
        print(f"Create button найден: {self.create_button}")  # Проверка

    def show_delete_confirmation(self, habit_id):
        """Показывает окно подтверждения для удаления привычки."""
        # Создаем окно подтверждения
        popup_content = BoxLayout(orientation='vertical', padding=10)

        confirmation_label = Label(text="Вы уверены, что хотите удалить эту привычку?", size_hint_y=None, height=40)
        popup_content.add_widget(confirmation_label)

        # Кнопка "Да"
        yes_button = Button(text="Да", size_hint_y=None, height=40)
        yes_button.bind(on_press=lambda instance: self.confirm_delete_habit(habit_id))

        # Кнопка "Нет"
        no_button = Button(text="Нет", size_hint_y=None, height=40)
        no_button.bind(on_press=self.close_popup)

        popup_content.add_widget(yes_button)
        popup_content.add_widget(no_button)

        # Создаем popup
        self.delete_popup = Popup(title="Подтвердите удаление", content=popup_content, size_hint=(None, None),
                                  size=(400, 200))
        self.delete_popup.open()

    def confirm_delete_habit(self, habit_id, instance=None):
        """Подтверждает удаление привычки из БД."""
        user_id = App.get_running_app().current_user_id
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()

        cursor.execute("DELETE FROM habits WHERE user_id = ? AND id = ?", (user_id, habit_id))

        connection.commit()
        connection.close()

        self.load_user_habits()  # Обновляем список привычек
        self.close_popup()  # Закрываем окно подтверждения

    def close_popup(self, instance=None):
        """Закрывает окно подтверждения."""
        self.delete_popup.dismiss()

    def load_user_habits(self):
        """Загружает пользовательские привычки из БД."""
        user_id = App.get_running_app().current_user_id
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()

        cursor.execute("SELECT id, name, buttons FROM habits WHERE user_id = ?", (user_id,))
        habits = cursor.fetchall()

        # Загружаем сохраненные привычки и их состояния
        cursor.execute("SELECT habit_name, selected_buttons FROM saved_habits WHERE user_id = ?", (user_id,))
        saved_habits = cursor.fetchall()

        connection.close()

        # Преобразуем сохраненные привычки в словарь для быстрого доступа
        saved_habits_dict = {}
        for habit_name, selected_buttons in saved_habits:
            saved_habits_dict[habit_name] = set(selected_buttons.split(','))

        habits_layout = self.ids.user_habits_layout
        habits_layout.clear_widgets()

        self.selected_habits = {}  # Очистка состояния

        for habit_id, name, buttons in habits:
            print(f"[DEBUG] Добавляем привычку: {name} с кнопками {buttons}")
            habit_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)

            habit_label = Label(text=f"[b]{name}[/b]", markup=True, font_size='18sp', size_hint_x=0.6)
            delete_button = Button(text="Удалить", size_hint_x=0.4, background_color=(1, 0, 0, 1))
            delete_button.bind(on_press=lambda instance: self.show_delete_confirmation(habit_id))

            habit_box.add_widget(habit_label)
            habit_box.add_widget(delete_button)

            habits_layout.add_widget(habit_box)

            button_names = buttons.split(',')
            self.selected_habits[name] = {btn_name: btn_name in saved_habits_dict.get(name, []) for btn_name in
                                          button_names}

            for btn_name in button_names:
                btn = Button(text=btn_name, size_hint_y=None, height=40)
                btn.background_color = (0, 1, 0, 1) if self.selected_habits[name][btn_name] else (1, 1, 1, 1)
                btn.bind(on_press=partial(self.toggle_habit, btn, name))  # Исправлено
                habits_layout.add_widget(btn)

    def delete_habit(self, habit_id):
        """Удаляет привычку из БД."""
        user_id = App.get_running_app().current_user_id
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()

        cursor.execute("DELETE FROM habits WHERE user_id = ? AND id = ?", (user_id, habit_id))

        connection.commit()
        connection.close()

        self.load_user_habits()  # Обновляем список привычек

    def on_pre_enter(self):
        """Автоматически загружает привычки при входе в экран."""
        self.load_user_habits()

    def toggle_habit(self, button, habit, *args):
        """Переключает состояние кнопки (выбрана/не выбрана)."""
        if habit not in self.selected_habits:
            print(f"[ERROR] Habit '{habit}' не найден в self.selected_habits")
            return

        if button.text not in self.selected_habits[habit]:
            print(f"[ERROR] Кнопка '{button.text}' отсутствует в self.selected_habits[{habit}]")
            return

        print(f"[DEBUG] self.selected_habits = {self.selected_habits}")
        print(f"[DEBUG] habit = {habit}, button.text = {button.text}")

        current_state = self.selected_habits[habit][button.text]
        button.background_color = (0, 1, 0, 1) if not current_state else (1, 1, 1, 1)
        self.selected_habits[habit][button.text] = not current_state

    def save_selected_habits(self):
        """Сохраняет выбранные кнопки в БД."""
        user_id = App.get_running_app().current_user_id
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()

        cursor.execute("DELETE FROM saved_habits WHERE user_id = ?", (user_id,))

        for habit, buttons in self.selected_habits.items():
            selected_buttons = [btn for btn, selected in buttons.items() if selected]
            if selected_buttons:
                cursor.execute("INSERT INTO saved_habits (user_id, habit_name, selected_buttons) VALUES (?, ?, ?)",
                               (user_id, habit, ",".join(selected_buttons)))

        connection.commit()
        connection.close()

        self.load_user_habits()  # Обновляем UI после сохранения

        # Показываем сообщение об успешном сохранении
        self.show_popup("Успех", "Выбранные привычки сохранены!")

        print("Выбранные привычки сохранены!")

    def show_popup(self, title, message):
        """Показывает всплывающее окно с сообщением."""
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=message))

        close_button = Button(text="Закрыть", size_hint=(1, 0.3))
        content.add_widget(close_button)

        popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))
        close_button.bind(on_press=popup.dismiss)

        popup.open()

    def go_back_note_habit_form(self):
        """Переход на экран создания привычки."""
        self.manager.current = 'habit_form'

    def go_back(self):
        """Возвращение в NoteScreen."""
        self.manager.current = 'note'

class HabitFormScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.buttons = []
        self.create_button = None

    def on_kv_post(self, base_widget):
        super().on_kv_post(base_widget)
        self.create_button = self.ids.get("create_button", None)

    def create_block(self, block_name, button_count):
        if 4 <= button_count <= 16:
            self.ids.button_box.clear_widgets()
            self.buttons = []

            for i in range(button_count):
                button_name_input = TextInput(hint_text=f"Button {i + 1} name", multiline=False)
                self.ids.button_box.add_widget(button_name_input)
                self.buttons.append(button_name_input)

            if self.create_button:
                self.create_button.text = "Save Block"
                self.create_button.on_press = self.save_block
            else:
                print("Ошибка: self.create_button не инициализирован!")

    def save_block(self):
        block_name = self.ids.block_name_input.text.strip()
        button_names = [button.text.strip() for button in self.buttons]

        if not block_name or any(not name for name in button_names):
            self.show_popup("Ошибка", "Заполните все поля!")
            return

        user_id = App.get_running_app().current_user_id
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()

        # Проверяем, есть ли уже такая привычка у пользователя
        cursor.execute("SELECT id FROM habits WHERE user_id = ? AND name = ?", (user_id, block_name))
        existing_habit = cursor.fetchone()

        if existing_habit:
            self.show_popup("Ошибка", "Такая привычка уже существует!")
            connection.close()
            return

        # Сохраняем новую привычку
        cursor.execute("INSERT INTO habits (user_id, name, buttons) VALUES (?, ?, ?)",
                       (user_id, block_name, ",".join(button_names)))

        connection.commit()
        connection.close()

        # Обновляем UserHabitsScreen
        self.manager.get_screen('user_habits').load_user_habits()

        self.manager.current = 'user_habits'

    def show_popup(self, title, message):
        """Показывает всплывающее окно с ошибкой"""
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=message))

        close_button = Button(text="Закрыть", size_hint=(1, 0.3))
        content.add_widget(close_button)

        popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))
        close_button.bind(on_press=popup.dismiss)

        popup.open()

    def go_back_note_screen(self):
        self.manager.current = 'note'

# Главное приложение
class LifeDotsApp(App):
    def build(self):
        self.saved_blocks = []
        self.current_user_id = None
        init_db()

        # Создаем экземпляр ScreenManager
        sm = ScreenManager()

        # Создаем экраны
        login_screen = LoginScreen(name='login', on_user_login=self.on_user_login)
        registration_screen = RegistrationScreen(name='registration')
        calendar_screen = CalendarScreen(name='calendar')
        note_screen = NoteScreen(name='note')
        user_habits = UserHabitsScreen(name='user_habits')
        habit_form = HabitFormScreen(name='habit_form')

        # Добавляем экраны в ScreenManager
        sm.add_widget(login_screen)
        sm.add_widget(registration_screen)
        sm.add_widget(calendar_screen)
        sm.add_widget(note_screen)
        sm.add_widget(user_habits)
        sm.add_widget(habit_form)

        # Устанавливаем экран по умолчанию
        sm.current = 'login'

        return sm

    def save_block(self, block_name, button_names):
        """Сохраняет новый блок с кнопками"""
        new_block = {'name': block_name, 'buttons': button_names}
        self.saved_blocks.append(new_block)
        # Обновить экран NoteScreen
        note_screen = self.root.get_screen('note')
        note_screen.update_saved_blocks()

    def on_user_login(self, user_id):
        self.current_user_id = user_id
        print(f"Пользователь {user_id} вошел в систему.")


if __name__ == "__main__":
    LifeDotsApp().run()





