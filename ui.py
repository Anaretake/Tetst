import tkinter as tk
from tkinter import messagebox

class MainScreen(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Главное меню")
        self.geometry("400x350")

        tk.Label(self, text="Главное меню", font=("Arial", 16)).pack(pady=20)

        buttons = [
            ("Адаптивная модель операторской деятельности", lambda: self.show_user_input_window("Адаптивная модель операторской деятельности")),
            ("Тест на сложную зрительно-моторную реакцию", lambda: self.show_user_input_window("Тест на сложную зрительно-моторную реакцию")),
            ("Самочувствие, активность, настроение", lambda: self.show_user_input_window("Самочувствие, активность, настроение")),
            ("Выход", self.quit)
        ]

        for text, command in buttons:
            tk.Button(self, text=text, width=40, command=command).pack(pady=5)

    def show_user_input_window(self, test_name):
        # Окно для ввода данных пользователя
        user_input_window = tk.Toplevel(self)
        user_input_window.title(f"Ввод данных для теста: {test_name}")
        user_input_window.geometry("400x300")

        tk.Label(user_input_window, text=f"Введите данные для теста: {test_name}", font=("Arial", 14)).pack(pady=10)

        tk.Label(user_input_window, text="Имя", font=("Arial", 12)).pack(pady=5)
        name_entry = tk.Entry(user_input_window, font=("Arial", 12))
        name_entry.pack(pady=5)

        tk.Label(user_input_window, text="Фамилия", font=("Arial", 12)).pack(pady=5)
        surname_entry = tk.Entry(user_input_window, font=("Arial", 12))
        surname_entry.pack(pady=5)

        tk.Label(user_input_window, text="Возраст", font=("Arial", 12)).pack(pady=5)
        age_entry = tk.Entry(user_input_window, font=("Arial", 12))
        age_entry.pack(pady=5)

        def start_test():
            name = name_entry.get()
            surname = surname_entry.get()
            age = age_entry.get()

            if not name or not surname or not age.isdigit():
                messagebox.showwarning("Ошибка", "Пожалуйста, заполните все поля корректно.")
                return

            age = int(age)
            user_input_window.destroy()  # Закрыть окно ввода данных
            self.start_test(test_name, name, surname, age)  # Начать тест

        start_button = tk.Button(user_input_window, text="Начать тест", command=start_test)
        start_button.pack(pady=20)

    def start_test(self, test_name, name, surname, age):
        # Запуск теста (для примера, будет просто сообщение)
        test_window = tk.Toplevel(self)
        test_window.title(f"Тест: {test_name}")
        test_window.geometry("400x300")

        tk.Label(test_window, text=f"Тест: {test_name}", font=("Arial", 14)).pack(pady=10)
        tk.Label(test_window, text=f"Имя: {name} {surname}", font=("Arial", 12)).pack(pady=5)
        tk.Label(test_window, text=f"Возраст: {age} лет", font=("Arial", 12)).pack(pady=5)


        # Для завершения теста
        close_button = tk.Button(test_window, text="Завершить тест", command=test_window.destroy)
        close_button.pack(pady=20)


if __name__ == "__main__":
    app = MainScreen()
    app.mainloop()
