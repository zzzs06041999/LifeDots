from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


def show_popup(title, message):
    # Цвета из палитры
    light_brown = (0.949, 0.808, 0.635, 1)  # светлый бежевый
    dark_brown = (0.251, 0.161, 0.078, 1)  # темно-коричневый
    button_brown = (0.451, 0.298, 0.161, 1)  # коричневый
    light_brown_button = (0.851, 0.675, 0.510, 1)  # светлый оттенок коричневого

    # Макет попапа
    popup_layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

    # Создание метки с сообщением
    popup_label = Label(
        text=message,
        size_hint=(1, 0.7),
        color=(1, 1, 1, 1),  # Белый цвет текста
        font_size='18sp',  # Увеличенный размер шрифта
        halign='center',  # Центрирование текста по горизонтали
        valign='middle'  # Центрирование текста по вертикали
    )

    # Кнопка закрытия
    close_button = Button(
        text="Закрыть",
        size_hint=(1, 0.3),
        background_normal='',  # Без фона
        background_color=button_brown,  # Цвет фона кнопки
        color=(1, 1, 1, 1)  # Белый текст на кнопке
    )

    # Добавление виджетов в макет попапа
    popup_layout.add_widget(popup_label)
    popup_layout.add_widget(close_button)

    # Создание попапа
    popup = Popup(
        title=title,
        content=popup_layout,
        size_hint=(0.7, 0.4),
        auto_dismiss=False,  # Попап не будет закрываться автоматически при нажатии за пределы
        background_color=light_brown  # Цвет фона попапа
    )

    # Привязка кнопки закрытия к методу закрытия попапа
    close_button.bind(on_release=popup.dismiss)

    # Открытие попапа
    popup.open()
