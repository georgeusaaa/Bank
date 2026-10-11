import os
import sys
import time

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt

from bank_core import GENERATION_COOLDOWN, LOCKOUT_SECONDS, MAX_ATTEMPTS, Bank, load_users, save_users

# Файл с данными лежит рядом со скриптом, а не в текущей рабочей директории
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")

# Дефолтные пользователи, если файл JSON еще не создан
DEFAULT_USERS = ["Екатерина", "Александр", "Андрей", "Викрам", "Арнольда"]


class BankApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.bank = Bank(load_users(DB_FILE, DEFAULT_USERS, time.time()))
        self.save_data()
        self.init_ui()

    def save_data(self):
        """Сохранение текущего состояния пользователей в JSON."""
        try:
            save_users(DB_FILE, self.bank.users)
        except OSError as e:
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
            f"Новый код можно получать раз в {GENERATION_COOLDOWN} секунд.<br>"
            f"После {MAX_ATTEMPTS} неверных попыток вход блокируется на {LOCKOUT_SECONDS} секунд."
        )
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(welcome_label)

        # Выбор пользователя
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Выберите пользователя:"))
        self.user_combo = QComboBox()
        self.user_combo.addItems(sorted(self.bank.users.keys()))
        user_layout.addWidget(self.user_combo)
        main_layout.addLayout(user_layout)

        # --- Секция действий ---
        actions_layout = QHBoxLayout()

        self.btn_generate = QPushButton("1. Сгенерировать код")
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
        self.password_input.returnPressed.connect(self.login_cabinet)
        login_box.addWidget(self.password_input)

        self.btn_login = QPushButton("2. Войти")
        self.btn_login.clicked.connect(self.login_cabinet)
        login_box.addWidget(self.btn_login)

        main_layout.addLayout(login_box)

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

        try:
            code = self.bank.generate(name)
        except ValueError as e:
            self.log_message(f"[{name}] {e}", "red")
            QMessageBox.warning(self, "Подождите", str(e))
            return

        self.save_data()  # В JSON сохраняется только хеш кода
        self.log_message(f"[{name}] Код успешно сгенерирован!", "green")
        QMessageBox.information(self, "Новый код", f"Ваш код: {code}\nЗапомните его — повторно он не показывается.")

    def login_cabinet(self):
        name = self.user_combo.currentText()
        entered_password = self.password_input.text().strip()

        if not entered_password:
            QMessageBox.warning(self, "Внимание", "Поле ввода пароля пустое!")
            return

        result = self.bank.login(name, entered_password)
        self.password_input.clear()

        if result == "ok":
            self.log_message(f"Добро пожаловать, {name}! Хорошего дня!", "green")
            QMessageBox.information(self, "Успех", f"Добро пожаловать, {name}! Вход выполнен.")
        elif result == "no_code":
            self.log_message(f"[{name}] Код еще не сгенерирован!", "red")
            QMessageBox.warning(self, "Ошибка", "Пользователь найден, но код еще не сгенерирован!")
        elif result == "locked":
            wait = self.bank.seconds_locked(name)
            self.log_message(f"[{name}] Вход заблокирован ещё на {wait} сек.", "red")
            QMessageBox.critical(self, "Блокировка", f"Слишком много неверных попыток. Подождите {wait} сек.")
        else:
            left = self.bank.attempts_left(name)
            self.log_message(f"[{name}] Неверный код. Осталось попыток: {left}.", "orange")
            QMessageBox.warning(self, "Ошибка", f"Код неверный! Осталось попыток: {left}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    bank_window = BankApp()
    bank_window.show()
    sys.exit(app.exec())
