import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QLabel, QComboBox, QStackedWidget)
from PyQt5.QtCore import Qt
from enum import Enum


class UserType(Enum):
    TESTEE = 1  # Испытуемый
    SPECIALIST = 2  # Специалист


class AuthWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Авторизация")
        self.setFixedSize(300, 200)

        central_widget = QWidget()
        layout = QVBoxLayout()

        self.user_combo = QComboBox()
        self.user_combo.addItem("Испытуемый", UserType.TESTEE)
        self.user_combo.addItem("Специалист", UserType.SPECIALIST)

        self.login_btn = QPushButton("Войти")

        layout.addWidget(QLabel("Выберите тип пользователя:"))
        layout.addWidget(self.user_combo)
        layout.addStretch()
        layout.addWidget(self.login_btn)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


class TesteeInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Интерфейс испытуемого")
        self.setFixedSize(400, 500)

        central_widget = QWidget()
        layout = QVBoxLayout()

        # Кнопки тестов
        layout.addWidget(QLabel("Доступные тесты:"))
        self.test_buttons = []
        for i in range(1, 6):
            btn = QPushButton(f"Пройти тест {i}")
            self.test_buttons.append(btn)
            layout.addWidget(btn)

        # Разделитель
        layout.addWidget(QLabel(""))
        layout.addWidget(QLabel("Другие функции:"))

        # Другие кнопки
        self.my_results_btn = QPushButton("Мои результаты")
        self.settings_btn = QPushButton("Настройки")
        self.logout_btn = QPushButton("Выход")

        layout.addWidget(self.my_results_btn)
        layout.addWidget(self.settings_btn)
        layout.addStretch()
        layout.addWidget(self.logout_btn)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


class SpecialistInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Интерфейс специалиста")
        self.setFixedSize(800, 600)

        central_widget = QWidget()
        layout = QVBoxLayout()

        # Кнопки управления
        self.add_user_btn = QPushButton("Добавить нового пользователя")
        self.view_results_btn = QPushButton("Просмотр всех результатов")
        self.settings_btn = QPushButton("Настройки")
        self.logout_btn = QPushButton("Выход")

        # Таблица результатов
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["ID", "Имя", "Тест", "Результат", "Дата"])
        self.results_table.setRowCount(10)
        for i in range(10):
            for j in range(5):
                self.results_table.setItem(i, j, QTableWidgetItem(f"Пример {i + 1}-{j + 1}"))

        # Фильтры
        filters_layout = QVBoxLayout()
        filters_layout.addWidget(QLabel("Фильтры:"))

        self.user_filter = QComboBox()
        self.user_filter.addItems(["Все пользователи", "Пользователь 1", "Пользователь 2"])

        self.test_filter = QComboBox()
        self.test_filter.addItems(["Все тесты", "Тест 1", "Тест 2", "Тест 3"])

        filters_layout.addWidget(self.user_filter)
        filters_layout.addWidget(self.test_filter)

        # Основной layout
        layout.addWidget(self.add_user_btn)
        layout.addWidget(QLabel(""))
        layout.addLayout(filters_layout)
        layout.addWidget(self.view_results_btn)
        layout.addWidget(self.results_table)
        layout.addWidget(self.settings_btn)
        layout.addWidget(self.logout_btn)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)


class DemoApp:
    def __init__(self):
        self.app = QApplication(sys.argv)

        # Создаем все окна
        self.auth_window = AuthWindow()
        self.testee_window = TesteeInterface()
        self.specialist_window = SpecialistInterface()

        # Показываем окно авторизации
        self.auth_window.show()

        # Подключаем кнопки для демонстрации переключения окон
        self.auth_window.login_btn.clicked.connect(self.show_demo_interface)
        self.testee_window.logout_btn.clicked.connect(self.back_to_auth)
        self.specialist_window.logout_btn.clicked.connect(self.back_to_auth)

    def show_demo_interface(self):
        user_type = self.auth_window.user_combo.currentData()
        self.auth_window.hide()

        if user_type == UserType.TESTEE:
            self.testee_window.show()
        else:
            self.specialist_window.show()

    def back_to_auth(self):
        self.testee_window.hide()
        self.specialist_window.hide()
        self.auth_window.show()

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    demo = DemoApp()
    demo.run()