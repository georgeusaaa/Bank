import sys
import json
import os
from random import choices
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt

# Имя файла для хранения данных
DB_FILE = "users.json"

# Дефолтные пользователи, если файл JSON еще не создан
DEFAULT_USERS = {
    "Екатерина": "",
    "Александр": "",
    "Андрей": "",
    "Викрам": "",
    "Арнольда": ""
}


class BankApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_data()
        self.init_ui()

    def init_data(self):
        """Загрузка данных из JSON или создание нового файла."""
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    self.lst_users = json.load(f)
            except Exception:
                self.lst_users = DEFAULT_USERS.copy()
        else:
            self.lst_users = DEFAULT_USERS.copy()
            self.save_data()

    def save_data(self):
        """Сохранение текущего состояния пользователей в JSON."""
        try:
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.lst_users, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить данные: {e}")

    def init_ui(self):
        self.setWindowTitle("Bank.US — Личный Кабинет")
        self.resize(500, 450)

        # Главный контейнер
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Секция приветствия и авторизации ---
        welcome_label = QLabel(
            "<b>Здравствуйте! Программа Bank.US готова к работе!</b><br>"
            "Для новой генерации паролей необходим перезапуск скрипта.<br>"
            "Помните, что пароли можно генерировать раз в 180 секунд."
        )
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(welcome_label)

        # Выбор пользователя
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Выберите пользователя:"))
        self.user_combo = QComboBox()
        self.user_combo.addItems(sorted(self.lst_users.keys()))
        user_layout.addWidget(self.user_combo)
        main_layout.addLayout(user_layout)

        # --- Секция действий ---
        actions_layout = QHBoxLayout()

        self.btn_generate = QPushButton("1. Сгенерировать пароль")
        self.btn_generate.clicked.connect(self.generate_password)
        actions_layout.addWidget(self.btn_generate)

        self.btn_finish = QPushButton("3. Завершить день")
        self.btn_finish.clicked.connect(self.close)
        actions_layout.addWidget(self.btn_finish)

        main_layout.addLayout(actions_layout)

        # --- Секция ввода пароля и входа ---
        login_box = QHBoxLayout()
        login_box.addWidget(QLabel("Введите ваш код:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)  # Скрываем ввод пароля
        login_box.addWidget(self.password_input)

        self.btn_login = QPushButton("2. Войти")
        self.btn_login.clicked.connect(self.login_cabinet)
        login_box.addWidget(self.btn_login)

        main_layout.addLayout(login_box)

        # Переменная для подсчета попыток входа
        self.login_attempts = 0
        self.current_user_for_login = ""

        # --- Лог событий (вместо print) ---
        main_layout.addWidget(QLabel("Лог системы:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output)

        self.log_message("Система инициализирована. Выберите пользователя.")

    def log_message(self, text, color="black"):
        """Вспомогательный метод для вывода цветных логов в интерфейс."""
        self.log_output.append(f"<font color='{color}'>{text}</font>")

    def generate_password(self):
        name = self.user_combo.currentText()

        if self.lst_users.get(name) == "":
            lst_alphab = ["A", "B", "C", "D"]
            lst_num = ["0", "1", "2", "3", "4", "5", "6", "7"]

            generation_p = "".join(choices(lst_alphab, k=2)) + "".join(choices(lst_num, k=4))
            self.lst_users[name] = generation_p
            self.save_data()  # Сохраняем изменения в JSON

            self.log_message(f"[{name}] Код успешно сгенерирован!", "green")
            QMessageBox.information(self, "Новый код", f"Ваш код: {generation_p}")
        else:
            self.log_message(f"[{name}] Лимит исчерпан! Пароль уже существует в базе JSON.", "red")
            QMessageBox.warning(self, "Ошибка", "Лимит исчерпан! Перезапустите программу.")

    def login_cabinet(self):
        name = self.user_combo.currentText()
        entered_password = self.password_input.text().strip()

        if not entered_password:
            QMessageBox.warning(self, "Внимание", "Поле ввода пароля пустое!")
            return

        # Если переключили пользователя, сбрасываем счетчик попыток
        if self.current_user_for_login != name:
            self.current_user_for_login = name
            self.login_attempts = 0

        user_password = self.lst_users.get(name, "")

        if user_password != "":
            self.login_attempts += 1
            if entered_password == user_password:
                self.log_message(f"Добро пожаловать, {name}! Хорошего дня! (С {self.login_attempts} попытки)", "green")
                QMessageBox.information(self, "Успех", f"Добро пожаловать, {name}! Вход выполнен.")
                self.login_attempts = 0  # Сброс после успешного входа
                self.password_input.clear()
            else:
                self.log_message(f"[{name}] Неверный пароль. Попытка {self.login_attempts} из 3.", "orange")

                if self.login_attempts >= 3:
                    self.log_message(f"[{name}] Все 3 попытки исчерпаны. Доступ временно заблокирован!", "red")
                    QMessageBox.critical(self, "Блокировка", "Все 3 попытки исчерпаны. Окно ввода будет очищено.")
                    self.password_input.clear()
                    self.login_attempts = 0  # Сброс счетчика блокировки для интерфейса
                else:
                    QMessageBox.warning(self, "Ошибка", f"Пароль неверный! Осталось попыток: {3 - self.login_attempts}")
        else:
            self.log_message(f"[{name}] Пароль еще не сгенерирован!", "red")
            QMessageBox.warning(self, "Ошибка", "Пользователь найден, но пароль еще не сгенерирован!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    bank_window = BankApp()
    bank_window.show()
    sys.exit(app.exec())
