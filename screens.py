from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from datetime import datetime, timedelta
import sqlite3
from db_manager import get_note_from_db, save_note_to_db
from kivy.uix.gridlayout import GridLayout

# Экран входа
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.username_input = TextInput(hint_text="Введите имя пользователя", multiline=False)
        self.password_input = TextInput(hint_text="Введите пароль", password=True, multiline=False)
        login_button = Button(text="Войти", on_press=self.login)
        registration_button = Button(text="Регистрация", on_press=self.go_to_registration)

        self.layout.add_widget(Label(text="Вход", font_size=24))
        self.layout.add_widget(self.username_input)
        self.layout.add_widget(self.password_input)
        self.layout.add_widget(login_button)
        self.layout.add_widget(registration_button)
        self.add_widget(self.layout)

    def login(self, instance):
        username = self.username_input.text
        password = self.password_input.text
        if self.check_credentials(username, password):
            self.manager.current = 'calendar'  # Переключаемся на экран календаря
        else:
            self.show_popup("Ошибка", "Неверное имя пользователя или пароль.")

    def check_credentials(self, username, password):
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        connection.close()
        if result and result[0] == password:
            return True
        return False

    def go_to_registration(self, instance):
        self.manager.current = 'registration'  # Переключаемся на экран регистрации

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=message))
        close_button = Button(text="Закрыть")
        close_button.bind(on_press=lambda x: self.dismiss_popup())
        content.add_widget(close_button)

        self.popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))
        self.popup.open()

    def dismiss_popup(self):
        self.popup.dismiss()

# Экран регистрации
class RegistrationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.username_input = TextInput(hint_text="Введите имя пользователя", multiline=False)
        self.password_input = TextInput(hint_text="Введите пароль", password=True, multiline=False)
        register_button = Button(text="Зарегистрироваться", on_press=self.register)
        back_button = Button(text="Назад", on_press=self.go_back)

        self.layout.add_widget(Label(text="Регистрация", font_size=24))
        self.layout.add_widget(self.username_input)
        self.layout.add_widget(self.password_input)
        self.layout.add_widget(register_button)
        self.layout.add_widget(back_button)
        self.add_widget(self.layout)

    def register(self, instance):
        username = self.username_input.text
        password = self.password_input.text
        if self.check_user_exists(username):
            self.show_popup("Ошибка", "Пользователь с таким именем уже существует.")
        else:
            self.save_to_db(username, password)
            self.manager.current = 'calendar'  # Переход к экрану календаря после регистрации

    def check_user_exists(self, username):
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        connection.close()
        return result is not None

    def save_to_db(self, username, password):
        connection = sqlite3.connect("app_data.db")
        cursor = connection.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        connection.commit()
        connection.close()

    def go_back(self, instance):
        self.manager.current = 'login'  # Переход на экран входа

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=message))
        close_button = Button(text="Закрыть")
        close_button.bind(on_press=lambda x: self.dismiss_popup())
        content.add_widget(close_button)

        self.popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))
        self.popup.open()

    def dismiss_popup(self):
        self.popup.dismiss()

# Экран календаря
class CalendarScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.grid_layout = GridLayout(cols=7, size_hint_y=None)
        self.grid_layout.bind(minimum_height=self.grid_layout.setter('height'))
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        for day in days:
            self.grid_layout.add_widget(Label(text=day, size_hint_y=None, height=40))
        self.display_calendar()
        self.layout.add_widget(self.grid_layout)
        self.add_widget(self.layout)

    def display_calendar(self):
        today = datetime.today()
        first_day_of_month = today.replace(day=1)
        last_day_of_month = (first_day_of_month.replace(month=today.month + 1) - timedelta(days=1)).day
        start_day = first_day_of_month.weekday()
        for _ in range(start_day):
            self.grid_layout.add_widget(Label())
        for day in range(1, last_day_of_month + 1):
            day_button = Button(text=str(day))
            day_button.bind(on_press=self.on_day_selected)
            self.grid_layout.add_widget(day_button)

    def on_day_selected(self, instance):
        day = instance.text
        today = datetime.today()
        selected_date = today.replace(day=int(day))
        formatted_date = selected_date.strftime("%Y-%m-%d")
        self.manager.current = 'note'  # Переход на экран заметок
        self.manager.get_screen('note').set_date(formatted_date)

# Экран заметок
class NoteScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.note_input = TextInput(hint_text="Введите заметку", multiline=True, size_hint_y=0.7)
        self.layout.add_widget(self.note_input)
        save_button = Button(text="Сохранить заметку", size_hint_y=0.1)
        save_button.bind(on_press=self.save_note)
        self.layout.add_widget(save_button)
        self.add_widget(self.layout)

    def set_date(self, date):
        self.date = date
        note = get_note_from_db(date)
        self.note_input.text = note

    def save_note(self, instance):
        note = self.note_input.text
        if note.strip():
            save_note_to_db(self.date, note)
            self.show_popup("Успех", "Заметка успешно сохранена!")

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=message))
        close_button = Button(text="Закрыть")
        close_button.bind(on_press=lambda x: self.dismiss_popup())
        content.add_widget(close_button)
        self.popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))
        self.popup.open()

    def dismiss_popup(self):
        self.popup.dismiss()

