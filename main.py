import tkinter as tk
import random
import time
from reaction_test import ReactionTestInstructionWindow
from SimpleReactionTest import SimpleReactionTestInstructionWindow
from SanTest import SanTestInstruction
from KrepelinTest import KrepelinTestInstruction
from db_setup import init_db
import sqlite3
from tkinter import ttk
from datetime import datetime
from utils import ResultsViewer
from datetime import date
from tkinter import messagebox
from func import (
    export_to_excel,
    show_help_window,
)


def get_qfol_coefficient(db_path="test_app.db"):
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM normalization_stats WHERE key='qfol_coefficient'")
    row = cursor.fetchone()
    conn.close()
    return float(row[0]) if row else 20000

def update_qfol_coefficient(new_value, db_path="test_app.db"):
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO normalization_stats (key, value)
        VALUES (?, ?)
    """, ('qfol_coefficient', new_value))
    conn.commit()
    conn.close()

def center_window(window, width, height, y_offset=0):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2) - y_offset
    if x < 0:
        x = 0
    if y < 0:
        y = 0
    window.geometry(f"{width}x{height}+{x}+{y}")


class InstructionWindow(tk.Toplevel):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.user_id = user_id

        self.user_name, self.user_surname, self.user_patronymic, self.user_age = self.get_user_data(user_id)

        self.title("Инструкция к тесту")
        self.state("zoomed")
        self.configure(bg="#f0f0f0")


        instruction_text = (
            "Это тест на адаптивную модель операторской деятельности.\n\n"
            "Вам необходимо следовать курсором за движущемся квадратом.\n"
            "Также сверху, снизу, слева и справа от квадрата расположены числа.\n"
            "Вам необходимо складывать горизонтально и вертикально расположенные числа.\n"
            "Далее Вы должны сравнить полученные результаты.\n"
            "Результаты сравнения фиксируете следующим образом:\n"
            "если сумма горизонтально расположенных чисел больше, чем вертикально, нажмите левую кнопку мыши,\n"
            "иначе - нажмите правую. При правильном решении скорость движения квадрата будет увеличиваться, при неправильном - уменьшаться.\n"
            "Учитывайте следующее: все арифметические действия должны производится в уме, а результат засчитывается "
            "только при попадании в квадрат.\n"
            "Тест длится выбранное вами время. Удачи!"
        )

        main_container = tk.Frame(self, bg="#f0f0f0", padx=40, pady=30)
        main_container.pack(fill="both", expand=True)

        self.instruction_frame = tk.LabelFrame(
            main_container,
            text=" Инструкция ",
            font=("Arial", 16, "bold"),
            bg="white",
            fg="black",
            bd=2,
            relief=tk.GROOVE,
            padx=20,
            pady=20
        )
        self.instruction_frame.pack(fill="both", expand=True)

        self.instruction_label = tk.Label(
            self.instruction_frame,
            text=instruction_text,
            justify="left",
            anchor="nw",
            font=("Arial", 20),
            wraplength=self.winfo_width() - 100,
            bg="white",
            fg="black"
        )
        self.instruction_label.pack(fill="both", expand=True)

        controls_frame = tk.Frame(main_container, bg="#f0f0f0")
        controls_frame.pack(pady=(20, 0))

        self.time_choice = tk.StringVar()
        time_options = ["1 минута", "5 минут", "10 минут"]
        self.time_choice.set(time_options[2])

        time_menu = tk.OptionMenu(controls_frame, self.time_choice, *time_options)
        time_menu.config(
            font=("Arial", 16),
            width=15,
            height=2,
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            relief=tk.RAISED,
            borderwidth=2
        )
        time_menu["menu"].config(
            bg="white",
            fg="black",
            activebackground="#f0f0f0",
            activeforeground="black"
        )
        time_menu.pack(pady=(0, 10))

        start_button = tk.Button(
            controls_frame,
            text="Начать тест",
            command=self.start_test,
            font=("Arial", 16),
            width=20,
            height=2,
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            activeforeground="white",
            relief=tk.RAISED,
            borderwidth=2
        )
        start_button.pack()

        self.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        self.instruction_label.config(wraplength=event.width - 100)
    def get_user_data(self, user_id):
        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, surname, patronymic, age FROM users WHERE id=?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            name, surname, patronymic, age = result
            return name, surname, patronymic, age
        return None, None, None, None

    def start_test(self):
        time_option = self.time_choice.get()
        time_in_minutes = 1 if time_option == "1 минута" else 5 if time_option == "5 минут" else 10

        self.destroy()
        AdaptiveModelTest(self.user_id, time_in_minutes)

    def on_resize(self, event):
        new_width = event.width
        self.instruction_label.config(wraplength=new_width - 40)


class AdaptiveModelTest(tk.Toplevel):
    def __init__(self, user_id, test_duration):
        super().__init__()
        self.test_ended = False
        self.user_id = user_id
        self.test_duration = test_duration

        self.user_name, self.user_surname, self.user_patronymic, self.user_age = self.get_user_data(user_id)
        self.Qcal_list = []
        self.Qfol_list = []

        self.title("Адаптивная модель операторской деятельности")
        self.geometry("800x600")
        center_window(self, 800, 600)
        self.canvas = tk.Canvas(self, bg="white", width=800, height=600)
        self.canvas.pack()

        self.square_size = 50
        self.start_x = random.randint(0, 750)
        self.start_y = random.randint(0, 550)

        self.square = self.canvas.create_rectangle(self.start_x, self.start_y,
                                                   self.start_x + self.square_size, self.start_y + self.square_size,
                                                   fill="lime")
        self.cross = self.canvas.create_text(self.start_x + self.square_size / 2,
                                             self.start_y + self.square_size / 2,
                                             text="✚", font=("Arial", 24))

        self.numbers_text = self.canvas.create_text(self.start_x + self.square_size / 2,
                                                    self.start_y - 10, text="", font=("Arial", 20))

        self.dx, self.dy = 2, 2
        self.speed = 60

        self.correct_answers = 0
        self.incorrect_answers = 0
        self.time_in_square = 0
        self.last_time = time.time()

        self.track_x, self.track_y = [], []
        self.last_dx_track = None
        self.last_dy_track = None
        self.direction_changes_x = 0
        self.direction_changes_y = 0

        self.min_x = float('inf')
        self.max_x = float('-inf')
        self.min_y = float('inf')
        self.max_y = float('-inf')

        self.Qs_total = 0
        self.Qs_count = 0

        self.bind("<Button-1>", self.left_click)
        self.bind("<Button-3>", self.right_click)
        self.bind("<Escape>", lambda e: self.end_test())

        self.cursor_cross_size = 10
        self.cursor_cross_h = self.canvas.create_line(0, 0, 0, 0, fill="red", width=2)
        self.cursor_cross_v = self.canvas.create_line(0, 0, 0, 0, fill="red", width=2)
        self.canvas.config(cursor="none")

        self.countdown_text_id = None
        self.show_countdown(5)

    def show_countdown(self, count):
        if self.countdown_text_id:
            self.canvas.delete(self.countdown_text_id)

        if count == 0:
            self.canvas.delete(self.countdown_text_id)
            self.countdown_text_id = None
            self.start_test()
        else:
            self.countdown_text_id = self.canvas.create_text(
                400, 300, text=str(count), font=("Arial", 72), fill="gray"
            )
            self.after(1000, lambda: self.show_countdown(count - 1))

    def start_test(self):
        self.start_time = time.time()
        self.after(self.test_duration * 60000, self.end_test)
        self.update_minute_data()

        self.display_numbers()
        self.animate()
        self.check_cursor_position()

    def animate(self):
        if self.test_ended or not self.winfo_exists() or not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return

        try:
            x1, y1, x2, y2 = self.canvas.coords(self.square)
        except tk.TclError:
            return

        if x1 <= 0 or x2 >= 800:
            self.dx = -self.dx
        if y1 <= 0 or y2 >= 600:
            self.dy = -self.dy

        self.canvas.move(self.square, self.dx, self.dy)
        self.canvas.move(self.cross, self.dx, self.dy)
        for num_id in self.number_ids:
            self.canvas.move(num_id, self.dx, self.dy)

        self.after(self.speed, self.animate)

    def generate_numbers(self):
        while True:
            top = random.randint(1, 9)
            bottom = random.randint(1, 9)
            left = random.randint(1, 9)
            right = random.randint(1, 9)
            vertical_sum = top + bottom
            horizontal_sum = left + right

            if vertical_sum != horizontal_sum:
                return {"top": top, "bottom": bottom, "left": left, "right": right}

    def display_numbers(self):
        self.numbers = self.generate_numbers()
        x1, y1, x2, y2 = self.canvas.coords(self.square)
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        if hasattr(self, "number_ids"):
            for num_id in self.number_ids:
                self.canvas.delete(num_id)

        self.number_ids = []

        self.number_ids.append(
            self.canvas.create_text(center_x, y1 - 20, text=str(self.numbers["top"]), font=("Arial", 20)))
        self.number_ids.append(
            self.canvas.create_text(center_x, y2 + 20, text=str(self.numbers["bottom"]), font=("Arial", 20)))
        self.number_ids.append(
            self.canvas.create_text(x1 - 20, center_y, text=str(self.numbers["left"]), font=("Arial", 20)))
        self.number_ids.append(
            self.canvas.create_text(x2 + 20, center_y, text=str(self.numbers["right"]), font=("Arial", 20)))

    def left_click(self, event):
        x1, y1, x2, y2 = self.canvas.coords(self.square)
        cursor_x = self.winfo_pointerx() - self.winfo_rootx()
        cursor_y = self.winfo_pointery() - self.winfo_rooty()

        if x1 < cursor_x < x2 and y1 < cursor_y < y2:
            vertical_sum = self.numbers["top"] + self.numbers["bottom"]
            horizontal_sum = self.numbers["left"] + self.numbers["right"]


            if horizontal_sum > vertical_sum:
                self.correct_answers += 1
                self.adjust_speed(+10)
            else:
                self.incorrect_answers += 1
                self.adjust_speed(-10)

            self.display_numbers()
    def right_click(self, event):
        x1, y1, x2, y2 = self.canvas.coords(self.square)
        cursor_x = self.winfo_pointerx() - self.winfo_rootx()
        cursor_y = self.winfo_pointery() - self.winfo_rooty()

        if x1 < cursor_x < x2 and y1 < cursor_y < y2:
            vertical_sum = self.numbers["top"] + self.numbers["bottom"]
            horizontal_sum = self.numbers["left"] + self.numbers["right"]
            if vertical_sum > horizontal_sum:
                self.correct_answers += 1
                self.adjust_speed(+10)
            else:
                self.incorrect_answers += 1
                self.adjust_speed(-10)

            self.display_numbers()

    def adjust_speed(self, delta):
        self.speed = max(10, min(200, self.speed - delta))
    def check_cursor_position(self):
        def update():
            if self.test_ended or not self.winfo_exists() or not hasattr(self,
                                                                         "canvas") or not self.canvas.winfo_exists():
                return

            try:
                x1, y1, x2, y2 = self.canvas.coords(self.square)
            except tk.TclError:
                return

            cursor_x = self.winfo_pointerx() - self.winfo_rootx()
            cursor_y = self.winfo_pointery() - self.winfo_rooty()
            now = time.time()

            if x1 < cursor_x < x2 and y1 < cursor_y < y2:
                self.time_in_square += now - self.last_time

            self.last_time = now

            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            self.min_x = min(self.min_x, center_x)
            self.max_x = max(self.max_x, center_x)
            self.min_y = min(self.min_y, center_y)
            self.max_y = max(self.max_y, center_y)

            if self.track_x:
                dx = center_x - self.track_x[-1]
                dy = center_y - self.track_y[-1]
                if self.last_dx_track and dx * self.last_dx_track < 0:
                    self.direction_changes_x += 1
                if self.last_dy_track and dy * self.last_dy_track < 0:
                    self.direction_changes_y += 1
                self.last_dx_track = dx
                self.last_dy_track = dy

            self.track_x.append(center_x)
            self.track_y.append(center_y)

            try:
                self.canvas.coords(self.cursor_cross_h, cursor_x - self.cursor_cross_size, cursor_y,
                                   cursor_x + self.cursor_cross_size, cursor_y)
                self.canvas.coords(self.cursor_cross_v, cursor_x, cursor_y - self.cursor_cross_size,
                                   cursor_x, cursor_y + self.cursor_cross_size)
            except tk.TclError:
                return

            if not self.test_ended:
                self.after(20, update)

        update()

    def update_minute_data(self):
        if self.test_ended:
            return

        attempts = self.correct_answers + self.incorrect_answers
        Qcal = self.correct_answers / attempts if attempts > 0 else 0
        Qcal_score = min(max(Qcal, 0.01), 1.00)
        self.Qcal_list.append(Qcal_score)

        if self.track_x and self.track_y:
            Ax = max(self.track_x) - min(self.track_x)
            Ay = max(self.track_y) - min(self.track_y)
            duration = len(self.track_x) * 0.02
            Fx = self.direction_changes_x / duration if duration > 0 else 0
            Fy = self.direction_changes_y / duration if duration > 0 else 0
            raw_qfol = Ax * Ay * Fx * Fy
            empirical_max = get_qfol_coefficient()
            Qfol = raw_qfol / empirical_max
            Qfol_score = min(max(Qfol, 0.01), 1.00)
        else:
            Qfol_score = 0.01

        self.Qfol_list.append(Qfol_score)

        self.after(60000, self.update_minute_data)

    def calculate_results(self):
        duration = time.time() - self.start_time
        attempts = self.correct_answers + self.incorrect_answers

        if attempts > 0:
            self.Qcal = self.correct_answers / attempts
        else:
            self.Qcal = 0


        self.Qcal_score = min(max(self.Qcal, 0.01), 1.00)

        if not self.track_x or not self.track_y:
            self.Qfol = 0.01
            self.Qfol_score = 0.01
            self.Qtotal = 0.01
            self.Qtotal_score = 0.01
            return

        Ax = max(self.track_x) - min(self.track_x)
        Ay = max(self.track_y) - min(self.track_y)
        duration = len(self.track_x) * 0.02
        Fx = self.direction_changes_x / duration if duration > 0 else 0
        Fy = self.direction_changes_y / duration if duration > 0 else 0

        raw_qfol = Ax * Ay * Fx * Fy
        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()

        cursor.execute("""
                INSERT INTO qfol_raw_data (user_id, qfol_value) 
                VALUES (?, ?)
            """, (self.user_id, raw_qfol))

        conn.commit()
        conn.close()
        empirical_max = get_qfol_coefficient()
        self.Qfol = raw_qfol / empirical_max
        self.Qfol_score = min(max(self.Qfol, 0.01), 1.00)
        print(f"Qcal_score: {self.Qcal_score}")
        print(f"Qfol_score: {self.Qfol_score}")
        print(f"Qtotal (product): {self.Qcal_score * self.Qfol_score}")

        self.Qtotal = self.Qfol_score * self.Qcal_score
        self.Qtotal_score = min(max(self.Qtotal, 0.01), 1.00)
        self.ball_score = round(self.Qtotal_score * 9 + 1)
        self.ball_score = max(1, min(self.ball_score, 10))

        if self.ball_score <= 2:
            self.ball_comment = "Неуспешный результат"
        elif 3 <= self.ball_score <= 6:
            self.ball_comment = "Результат средней успешности"
        else:
            self.ball_comment = "Успешный результат"
    def show_graph(self):
        import matplotlib.pyplot as plt

        minutes = list(range(1, len(self.Qcal_list) + 1))
        plt.figure(figsize=(8, 5))
        plt.plot(minutes, self.Qcal_list, label='Счёт (Qcal)', marker='o')
        plt.plot(minutes, self.Qfol_list, label='Слежение (Qfol)', marker='s')
        plt.xlabel("Время (минуты)")
        plt.ylabel("Показатели качества")
        plt.ylim(0, 1.05)
        plt.title("Кривая работоспособности / утомления")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

    def show_results(self):
        full_name = f"{self.user_surname} {self.user_name}"
        if hasattr(self, 'user_patronymic') and self.user_patronymic:
            full_name += f" {self.user_patronymic}"
        results_message = (
            f"Имя: {full_name}\n"
            f"Возраст: {self.user_age} лет\n\n"
            f"Правильных ответов: {self.correct_answers}\n"
            f"Неправильных ответов: {self.incorrect_answers}\n\n"
            f"Показатель счёта (Qcal): {self.Qcal_score:.2f} (из 1.00)\n"
            f"Показатель слежения (Qfol): {self.Qfol_score:.2f} (из 1.00)\n"
            f"Интегральный показатель (Qtotal): {self.Qtotal_score:.2f} (из 1.00)\n"
            f"Оценка: {self.ball_score}/10 — {self.ball_comment}\n"
        )
        messagebox.showinfo("Результаты теста", results_message)
    def get_user_data(self, user_id):
        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, surname, patronymic, age FROM users WHERE id=?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            name, surname, patronymic, age = result
            return name, surname, patronymic, age
        return None, None, None, None

    def end_test(self):
        if self.test_ended:
            return
        self.test_ended = True

        self.calculate_results()
        self.save_results_to_db()
        self.show_results()
        self.show_graph()
        self.destroy()

    def save_results_to_db(self):
        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()

        test_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
                INSERT INTO test_results (
                    test_date,
                    user_id,
                    correct_answers,
                    incorrect_answers,
                    score_indicator,
                    tracking_indicator,
                    integral_indicator,
                    ball_score,
                    ball_comment
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
            test_date,
            self.user_id,
            self.correct_answers,
            self.incorrect_answers,
            round(self.Qcal_score, 4),
            round(self.Qfol_score, 4),
            round(self.Qtotal_score, 4),
            self.ball_score,
            self.ball_comment
        ))
        adaptive_model_result_text = f"{self.ball_score} баллов — {self.ball_comment}"

        cursor.execute("""
                SELECT id FROM full_test_results
                WHERE user_id = ? AND DATE(test_date) = DATE(?)
          """, (self.user_id, test_date.split(' ')[0]))
        existing_entry = cursor.fetchone()

        if existing_entry:
            cursor.execute("""
                    UPDATE full_test_results
                    SET adaptive_model_result = ?
                    WHERE id = ?
                """, (adaptive_model_result_text, existing_entry[0]))
        else:
            cursor.execute("""
                    INSERT INTO full_test_results (
                        test_date,
                        user_id,
                        adaptive_model_result
                    )
                    VALUES (?, ?, ?)
                """, (test_date, self.user_id, adaptive_model_result_text))

        conn.commit()
        conn.close()
class MainScreen(tk.Tk):
    def __init__(self):
        super().__init__()
        init_db()
        self.title("Главный экран")
        self.state("zoomed")
        self.configure(bg="#f0f0f0")

        self.user_name = ""
        self.user_surname = ""
        self.user_patronymic = ""
        self.user_age = 0

        button_style = {
            "bg": "#ffffff",
            "fg": "#333333",
            "font": ("Arial", 12, "bold"),
            "width": 60,
            "height": 2,
            "activebackground": "#e0e0e0",
            "relief": tk.RAISED,
            "borderwidth": 2
        }

        tk.Label(self, text="Главный экран", font=("Arial", 24, "bold"), bg="#f0f0f0").pack(pady=20)

        password_label = tk.Label(self, text="Пароль = 1234", font=("Arial", 12), bg="#f0f0f0", fg="red")
        password_label.place(relx=1.0, rely=0.0, anchor='ne', x=-10, y=10)

        tk.Label(self, text="Выберите пользователя:", font=("Arial", 12), bg="#f0f0f0").pack(pady=10)

        self.user_combobox = ttk.Combobox(self, state="readonly", width=50, font=("Arial", 12))
        self.user_combobox.pack()
        self.user_combobox.bind("<<ComboboxSelected>>", self.select_user)

        tk.Button(self, text="Добавить нового пользователя",
                  command=self.open_add_user_window,
                  bg="#4CAF50",
                  fg="white",
                  font=("Arial", 12, "bold"),
                  padx=10,
                  pady=5).pack(pady=15)

        buttons = [
            ("Адаптивная модель операторской деятельности", self.start_adaptive_test),
            ("Тест на сложную зрительно-моторную реакцию", self.start_reaction_test),
            ("Тест на простую зрительно-моторную реакцию", self.start_simplereaction_test),
            ("Самочувствие, активность, настроение", self.start_san_test),
            ("Счёт по Крепелину", self.start_krepelin_test),
            ("Результаты", self.open_results_menu),
            ("Настройки", self.open_settings_window),
            ("Закрыть приложение",self.close_application)
        ]

        for text, command in buttons:
            btn = tk.Button(self, text=text, command=command, **button_style)
            btn.pack(pady=10)

        self.load_users()

    def close_application(self):
        self.destroy()

    def load_users(self):
        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, surname, patronymic, age FROM users")
        users = cursor.fetchall()
        conn.close()

        self.user_map = {}
        display_list = []

        for user in users:
            user_id, name, surname, patronymic, age = user
            display = f"{name} {surname} {patronymic}, {age} лет"
            display_list.append(display)
            self.user_map[display] = (user_id, name, surname, patronymic, age)

        self.user_combobox['values'] = display_list
        if display_list:
            self.user_combobox.current(0)
            self.select_user()

    def select_user(self, event=None):
        selection = self.user_combobox.get()
        if selection in self.user_map:
            self.user_id, self.user_name, self.user_surname, self.user_patronymic, self.user_age = self.user_map[selection]

    def open_add_user_window(self):
        add_window = tk.Toplevel(self)
        add_window.title("Добавить пользователя")
        add_window.geometry("300x350")
        center_window(add_window, 300, 350)

        tk.Label(add_window, text="Имя:").pack(pady=5)
        name_entry = tk.Entry(add_window)
        name_entry.pack(pady=5)

        tk.Label(add_window, text="Фамилия:").pack(pady=5)
        surname_entry = tk.Entry(add_window)
        surname_entry.pack(pady=5)

        tk.Label(add_window, text="Отчество:").pack(pady=5)
        patronymic_entry = tk.Entry(add_window)
        patronymic_entry.pack(pady=5)

        tk.Label(add_window, text="Дата рождения (ДД.ММ.ГГГГ):").pack(pady=5)
        birthdate_entry = tk.Entry(add_window)
        birthdate_entry.pack(pady=5)

        def save_new_user():
            name = name_entry.get().strip()
            surname = surname_entry.get().strip()
            patronymic = patronymic_entry.get().strip()
            birthdate_text = birthdate_entry.get().strip()

            if not name or not surname or not birthdate_text:
                messagebox.showerror("Ошибка", "Введите все обязательные данные.")
                return

            if not (name.isalpha() and surname.isalpha() and (patronymic.isalpha() or patronymic == "")):
                messagebox.showerror("Ошибка", "Имя, фамилия и отчество должны содержать только буквы.")
                return

            try:
                day, month, year = map(int, birthdate_text.split('.'))
                birthdate = date(year, month, day)
                today = date.today()
                age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

                if age < 12 or age > 100:
                    messagebox.showerror("Ошибка", "Возраст должен быть от 12 до 100 лет.")
                    return

            except (ValueError, AttributeError):
                messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ДД.ММ.ГГГГ")
                return

            conn = sqlite3.connect("test_app.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (name, surname, patronymic, age) 
                VALUES (?, ?, ?, ?)
            """, (name, surname, patronymic, age))
            conn.commit()
            conn.close()

            add_window.destroy()
            self.load_users()

        tk.Button(add_window, text="Сохранить", command=save_new_user, bg="#4CAF50", fg="white").pack(pady=15)

    def validate_user_data(self):
        if not self.user_name or not self.user_surname or not (12 <= self.user_age <= 100):
            messagebox.showerror("Ошибка", "Выберите пользователя.")
            return False
        return True

    def start_adaptive_test(self):
        if self.validate_user_data():
            InstructionWindow(self, self.user_id)

    def start_reaction_test(self):
        if self.validate_user_data():
            ReactionTestInstructionWindow(self, self.user_id)

    def start_simplereaction_test(self):
        if self.validate_user_data():
            SimpleReactionTestInstructionWindow(self, self.user_id)

    def start_san_test(self):
        if self.validate_user_data():
            SanTestInstruction(self, self.user_id)

    def start_krepelin_test(self):
        if self.validate_user_data():
            KrepelinTestInstruction(self, self.user_id)

    def open_settings_window(self):
        settings_window = tk.Toplevel(self)
        settings_window.title("Настройки")
        center_window(settings_window, 300, 250)

        tk.Label(settings_window, text="Текущий пароль:").pack(pady=5)
        current_password_entry = tk.Entry(settings_window, show="*")
        current_password_entry.pack(pady=5)

        tk.Label(settings_window, text="Новый пароль:").pack(pady=5)
        new_password_entry = tk.Entry(settings_window, show="*")
        new_password_entry.pack(pady=5)

        def save_new_password():
            current_password = current_password_entry.get()
            new_password = new_password_entry.get()

            if not current_password or not new_password:
                messagebox.showerror("Ошибка", "Все поля должны быть заполнены!")
                return

            try:
                conn = sqlite3.connect('test_app.db')
                cursor = conn.cursor()

                cursor.execute('SELECT password FROM settings LIMIT 1')
                result = cursor.fetchone()

                if not result:
                    messagebox.showerror("Ошибка", "Пароль не найден в базе данных!")
                    conn.close()
                    return

                db_password = result[0]

                if current_password != db_password:
                    messagebox.showerror("Ошибка", "Неверный текущий пароль!")
                    conn.close()
                    return

                cursor.execute('UPDATE settings SET password = ?', (new_password,))
                conn.commit()
                conn.close()

                messagebox.showinfo("Успех", "Пароль успешно изменён!")
                settings_window.destroy()

            except sqlite3.Error as e:
                messagebox.showerror("Ошибка БД", f"Ошибка при работе с базой данных: {e}")
                if 'conn' in locals():
                    conn.close()

        save_btn = tk.Button(
            settings_window,
            text="Сохранить изменения",
            command=save_new_password,
            bg="#4CAF50",
            fg="white"
        )
        save_btn.pack(pady=15)
    def open_results_menu(self):
        def check_password():
            entered_password = password_entry.get()

            try:
                conn = sqlite3.connect('test_app.db')
                cursor = conn.cursor()
                cursor.execute('SELECT password FROM settings LIMIT 1')
                result = cursor.fetchone()
                conn.close()

                if not result:
                    messagebox.showerror("Ошибка", "Пароль не найден в базе данных!")
                    return

                correct_password = result[0]
                if entered_password == correct_password:
                    password_window.destroy()
                    show_results_window()
                else:
                    messagebox.showerror("Ошибка", "Неверный пароль!")

            except sqlite3.OperationalError as e:
                messagebox.showerror("Ошибка БД", f"Таблица settings не найдена: {e}")

        def show_results_window():
            results_window = tk.Toplevel(self)
            results_window.title("Результаты тестов")
            center_window(results_window, 500, 550)

            instructions_btn = tk.Button(
                results_window,
                text="Инструкции",
                width=50,
                height=2,
                command=self.show_instructions,
                bg="#4CAF50",
                fg="white",
                activebackground="#45a049"
            )
            instructions_btn.pack(pady=10)

            buttons = [
                ("Адаптивная модель операторской деятельности", self.show_adaptive_results),
                ("Тест на сложную зрительно-моторную реакцию", self.show_complex_reaction_results),
                ("Тест на простую зрительно-моторную реакцию", self.show_simple_reaction_results),
                ("Самочувствие, активность, настроение", self.show_san_results),
                ("Счёт по Крепелину", self.show_krepelin_results)
                # ("Общие результаты всех тестов", self.show_full_test_results)
            ]

            for text, command in buttons:
                tk.Button(
                    results_window,
                    text=text,
                    width=50,
                    height=2,
                    command=command,
                    bg="white",
                    fg="black",
                    activebackground="#ddd"
                ).pack(pady=5)
        password_window = tk.Toplevel(self)
        password_window.title("Введите пароль")
        center_window(password_window, 300, 150)
        password_window.grab_set()

        tk.Label(password_window, text="Введите пароль:").pack(pady=10)
        password_entry = tk.Entry(password_window, show="*", width=30)
        password_entry.pack(pady=5)

        tk.Button(
            password_window,
            text="ОК",
            command=check_password,
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049"
        ).pack(pady=10)

    def show_instructions(self):
        instructions_window = tk.Toplevel(self)
        instructions_window.title("Инструкции и интерпретация результатов")
        instructions_window.state("zoomed")

        instructions_window.after(10, lambda: center_window(instructions_window, 900, 700))

        notebook = ttk.Notebook(instructions_window)
        notebook.pack(fill='both', expand=True)
        test_instructions = {
            "Адаптивная модель операторской деятельности": [
                "Инструкция:",
                "Это тест на адаптивную модель операторской деятельности.\n\n"
                "Вам необходимо следовать курсором за движущемся квадратом.\n"
                "Также сверху, снизу, слева и справа от квадрата расположены числа.\n"
                "Вам необходимо складывать горизонтально и вертикально расположенные числа.\n"
                "Далее Вы должны сравнить полученные результаты.\n"
                "Результаты сравнения фиксируете следующим образом:\n"
                "если сумма горизонтально расположенных чисел больше, чем вертикально, нажмите левую кнопку мыши,\n"
                "иначе - нажмите правую. При правильном решении скорость движения квадрата будет увеличиваться, при неправильном - уменьшаться.\n"
                "Учитывайте следующее: все арифметические действия должны производится в уме, а результат засчитывается "
                "только при попадании в квадрат.\n"
                "Тест длится выбранное вами время. Удачи!",
                "Интерпретация результатов:",
                "0-2 балла - неуспешный результат",
                "3-6 балла(-ов)- результат средней успешности",
                "6-10 баллов - успешный результат"
            ],
            "Тест на сложную зрительно-моторную реакцию": [
                "Инструкция:",
                "В ходе теста Вам будет предложено реагировать на появление стимулов (кругов).\n"
                "Если круг будет зелёным, нажмите кнопку 'Ф' на клавиатуре или 'ДА' на панели.\n"
                "Если круг будет красным, нажмите кнопку 'В' на клавиатуре или 'НЕТ' на панели.\n\n"
                "Попробуйте реагировать как можно быстрее и точнее.\n"
                "",
                "Интерпретация результатов:",
                "- Время реакции: < 525 - отличная скорость реакции, 526-580 - хорошая скорость, 581-600 - допустимые показатели,>600 - признаки утомления",
                " Диапазоны могут меняться в зависимости от конкретных групп!",
                "Стандартное отклонение (описывает стабильность внимания): < 90 - очень высокая стабильность внимания,"
                " 91-130 - незначительные колебания, 131-165 - выраженная нестабильность внимания",
                "- Точность (количество правильных ответов): > 98 - отличная концентрация, 94-98 - незначительное количество ошибок,",
                " 90-93 - умеренное количество ошибок, возможно утомление, >90 - большое количество ошибок."
            ],
            "Тест на простую зрительно-моторную реакцию": [
                "Инструкция:",
                "Вам предстоит отреагировать на серию из 75 световых стимулов зелёного цвета.\n"
                "Первые 5 стимулов — тренировочные и не учитываются при подсчёте результатов.\n\n"
                "Каждый раз, как только увидите зелёный круг, нажмите на стимул ЛКМ как можно быстрее.\n"
                "Если нажмёте до появления стимула — это будет считаться упреждающей ошибкой.\n"
                "Если не нажмёте вовремя — стимул будет считаться пропущенным.\n\n"
                "",
                "Интерпретация результатов:",
                "- Среднее время реакции: <220  - высокая скорость реагирования , 220-250 - хорошая скорость реакции",
                "251-280 - средняя скорость реакции, >280 - замедленная скорость реакции",
                "- Стандартное отклонение (стабильность реакции): <40 - высокая стабильность, 40-90 - допустимые колебания внимания,",
                ">90 - возможно нарушение внимания",
                "- Коэффициент Уиппла: >0.9 - высокая точность, 0.8-0.89 - незначительное число ошибок, 0.7-0.79 - средняя точность,",
                "<0.7 - снижение точности, возможно утомление"
            ],
            "Самочувствие, активность, настроение (САН)": [
                "Инструкция:",
                "Тест 'Самочувствие, активность, настроение'\n\n"
                "Вы увидите пары противоположных характеристик (например, 'Веселый — Грустный').\n"
                "Ваша задача — выбрать кнопку с числом от 1 до 3, которая отражает, насколько вы\n"
                "чувствуете себя ближе к одному из утверждений:\n\n"
                "   3 — полностью соответствует левому/правому утверждению\n"
                "   2 — скорее соответствует\n"
                "   1 — немного соответствует\n\n"
                "Оценивайте своё текущее состояние. Не раздумывайте долго.\n"
                "После ответа на 30 пар будет выведен результат.\n\n"
                "",
                "Интерпретация результатов:",
                "Средний балл шкалы равен 4.",
                "Оценки, превышающие 4 балла, говорят о благоприятном состоянии испытуемого.",
                "Оценки ниже 4 баллов свидетельствуют о не благоприятном состоянии испытуемого.",
                "Оценки состояния лежащие в диапазоне 5,0—5,5 баллов свидетельствуют о нормальном состоянии испытуемого.",
                "Следует учитывать, что при анализе функционального состояния испытуемого важны не только значения отдельных показателей САН, но и их соотношение."
            ],
            "Счёт по Крепелину": [
                "Инструкция:",
                "Счёт по Крепелину\n\n"
                "Перед Вами будут представлены 8 строк по 20 столбцов с числами от 1 до 9\n"
                "Вам необходимо последовательно складывать числа и записывать их в ответ, отбрасывая десятки\n"
                "Например, если сумма получилась 12, то Вы записываете только 2\n\n"
                "На каждую строку Вам отводится по 30 секунд.\n"
                "Постарайтесь выполнить как можно больше сложений и не допустить ошибки. \n"
                "",
                "Интерпретация результатов:",
                "- Количество обработанных строк: чем больше, тем лучше",
                "- Количество ошибок: должно быть минимальным",
                "- Темп работы: должен быть стабильным"
            ]
        }


        for test_name, instructions in test_instructions.items():
            frame = tk.Frame(notebook)
            notebook.add(frame, text=test_name)

            text_widget = tk.Text(
                frame,
                wrap='word',
                font=('Arial', 15),
                padx=10,
                pady=10
            )
            scrollbar = tk.Scrollbar(frame, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)

            scrollbar.pack(side='right', fill='y')
            text_widget.pack(fill='both', expand=True)


            for line in instructions:
                if line.startswith("Инструкция:") or line.startswith("Интерпретация результатов:"):
                    text_widget.insert('end', line + '\n', 'heading')
                else:
                    text_widget.insert('end', line + '\n')

            text_widget.tag_configure('heading', font=('Arial', 16, 'bold'))
            text_widget.config(state='disabled')

        close_btn = tk.Button(
            instructions_window,
            text="Закрыть",
            command=instructions_window.destroy,
            width=20
        )
        close_btn.pack(pady=10)

    def show_adaptive_results(self):
        results_window = tk.Toplevel(self)
        results_window.title("Результаты: Адаптивная модель")
        results_window.state("zoomed")

        label_font = ('Helvetica', 13)
        entry_font = ('Helvetica', 13)
        button_font = ('Helvetica', 13, 'bold')
        stats_font = ('Helvetica', 13, 'bold')

        control_frame = tk.Frame(results_window)
        control_frame.pack(pady=10, fill=tk.X)

        export_button = tk.Button(control_frame, text="Экспорт в Excel",
                                  command=lambda: export_to_excel(tree, columns),
                                  bg="#4CAF50", fg="white", font=button_font)
        export_button.pack(side=tk.LEFT, padx=10)

        help_button = tk.Button(control_frame, text="Справка",
                                command=lambda: show_help_window(results_window),
                                bg="#2196F3", fg="white", font=button_font)
        help_button.pack(side=tk.LEFT, padx=10)

        search_outer_frame = tk.Frame(results_window)
        search_outer_frame.pack(fill=tk.X)

        search_frame = tk.Frame(search_outer_frame)
        search_frame.pack(pady=10)

        full_name_label = tk.Label(search_frame, text="Поиск по ФИО:", font=label_font)
        full_name_label.grid(row=0, column=0, padx=5, pady=5)
        full_name_entry = tk.Entry(search_frame, width=30, font=entry_font)
        full_name_entry.grid(row=0, column=1, padx=5, pady=5)

        date_label = tk.Label(search_frame, text="Поиск по дате :", font=label_font)
        date_label.grid(row=0, column=2, padx=5, pady=5)
        date_entry = tk.Entry(search_frame, width=20, font=entry_font)
        date_entry.grid(row=0, column=3, padx=5, pady=5)

        search_button = tk.Button(search_frame, text="Поиск", command=lambda: filter_data(), font=button_font,bg="#4CAF50",fg="white")
        search_button.grid(row=0, column=4, padx=5, pady=5)

        stats_outer_frame = tk.Frame(results_window)
        stats_outer_frame.pack(fill=tk.X)

        stats_frame = tk.Frame(stats_outer_frame)
        stats_frame.pack(pady=10)

        avg_itog_label = tk.Label(stats_frame, text="Средний Итог: -", font=stats_font)
        avg_itog_label.pack(side=tk.LEFT, padx=20)

        avg_ball_label = tk.Label(stats_frame, text="Средний Балл: -", font=stats_font)
        avg_ball_label.pack(side=tk.LEFT, padx=20)

        above_avg_var = tk.BooleanVar()
        above_avg_check = tk.Checkbutton(
            stats_frame,
            text="Показать результаты выше среднего",
            variable=above_avg_var,
            command=lambda: filter_data(),
            font=label_font
        )
        above_avg_check.pack(side=tk.LEFT, padx=20)

        columns = (
            "Дата", "Имя", "Фамилия", "Отчество", "Возраст",
            "Правильные ответы", "Ошибки", "Счёт", "Слежение", "Итог", "Балл", "Интерпретация"
        )

        style = ttk.Style()
        style.configure("Treeview", rowheight=45, font=('Helvetica', 12))
        style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'))

        tree_frame = tk.Frame(results_window)
        tree_frame.pack(fill="both", expand=True)

        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical")
        scrollbar_y.pack(side="right", fill="y")

        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        scrollbar_x.pack(side="bottom", fill="x")

        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Treeview",
                            yscrollcommand=scrollbar_y.set,
                            xscrollcommand=scrollbar_x.set)
        tree.pack(side="left", fill="both", expand=True)

        scrollbar_y.config(command=tree.yview)
        scrollbar_x.config(command=tree.xview)

        headings = [
            ("Дата", 150), ("Имя", 160), ("Фамилия", 160), ("Отчество", 160),
            ("Возраст", 90), ("Правильные ответы", 200), ("Ошибки", 100),
            ("Счёт", 100), ("Слежение", 100), ("Итог", 100), ("Балл", 70), ("Интерпретация", 400)
        ]

        for col, width in headings:
            tree.heading(col, text=col, command=lambda _col=col: sort_column(tree, _col, False))
            tree.column(col, width=width, anchor="center" if col != "Интерпретация" else "w")

        def load_data(full_name_filter="", date_filter=""):
            query = """
                SELECT tr.test_date, tr.id, u.name, u.surname, u.patronymic, u.age, 
                       tr.correct_answers, tr.incorrect_answers, 
                       tr.score_indicator, tr.tracking_indicator, tr.integral_indicator,
                       tr.ball_score, tr.ball_comment
                FROM test_results tr
                JOIN users u ON tr.user_id = u.id
                WHERE 1=1
            """
            params = []

            if full_name_filter:
                parts = full_name_filter.strip().split()
                for part in parts:
                    query += """
                        AND (
                            UPPER(u.name) LIKE UPPER(?)
                            OR UPPER(u.surname) LIKE UPPER(?)
                            OR UPPER(u.patronymic) LIKE UPPER(?)
                        )
                    """
                    params.extend([f"%{part}%"] * 3)

            if date_filter:
                date_list = [d.strip() for d in date_filter.split(",") if d.strip()]
                date_conditions = []
                for d in date_list:
                    try:
                        dt = datetime.strptime(d, "%d.%m.%Y")
                        date_conditions.append("tr.test_date LIKE ?")
                        params.append(f"{dt.strftime('%Y-%m-%d')}%")
                    except ValueError:
                        print("Некорректный формат даты. Используйте ДД.ММ.ГГГГ")

                if date_conditions:
                    query += " AND (" + " OR ".join(date_conditions) + ")"

            query += " ORDER BY tr.test_date DESC"

            conn = sqlite3.connect("test_app.db")
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            return rows

        def compute_averages(rows):
            itog_values = [float(r[10]) for r in rows if r[10] is not None]
            ball_values = [float(r[11]) for r in rows if r[11] is not None]
            avg_itog = sum(itog_values) / len(itog_values) if itog_values else 0
            avg_ball = sum(ball_values) / len(ball_values) if ball_values else 0
            return avg_itog, avg_ball

        def update_stats_labels(avg_itog, avg_ball):
            avg_itog_label.config(text=f"Средний Итог: {avg_itog:.2f}")
            avg_ball_label.config(text=f"Средний Балл: {avg_ball:.2f}")

        def filter_data():
            full_name_filter = full_name_entry.get().strip()
            date_filter = date_entry.get().strip()

            rows = load_data(full_name_filter, date_filter)

            avg_itog, avg_ball = compute_averages(rows)

            if above_avg_var.get():
                rows = [r for r in rows if r[10] and float(r[10]) > avg_itog]

            tree.delete(*tree.get_children())
            for row in rows:
                iid = str(row[1])

                values = (
                    row[0],
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                    row[7],
                    row[8],
                    row[9],
                    row[10],
                    row[11],
                    row[12]
                )

                try:
                    values = list(values)
                    values[0] = datetime.strptime(values[0], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
                except:
                    pass

                tree.insert("", "end", iid=iid, values=values)

            update_stats_labels(avg_itog, avg_ball)

        def sort_column(tv, col, reverse):
            l = [(tv.set(k, col), k) for k in tv.get_children("")]
            if col == "Дата":
                l.sort(key=lambda x: datetime.strptime(x[0], "%d-%m-%Y") if x[0] else datetime.min, reverse=reverse)
            elif col in ("ID", "Возраст", "Правильные", "Неправильные", "Балл", "Итог"):
                l.sort(key=lambda x: float(x[0]) if x[0] else 0, reverse=reverse)
            else:
                l.sort(key=lambda x: (x[0] or "").lower(), reverse=reverse)

            for index, (val, k) in enumerate(l):
                tv.move(k, '', index)

            tv.heading(col, command=lambda: sort_column(tv, col, not reverse))

        filter_data()

        self.results_viewer = ResultsViewer(results_window, save_mode="test_results")
        self.results_viewer.setup_editing(tree, columns)

    def show_complex_reaction_results(self):
        results_window = tk.Toplevel(self)
        results_window.title("Результаты: Сложная зрительно-моторная реакция")
        results_window.state("zoomed")

        label_font = ('Helvetica', 13)
        entry_font = ('Helvetica', 13)
        button_font = ('Helvetica', 13, 'bold')
        stats_font = ('Helvetica', 13, 'bold')

        control_frame = tk.Frame(results_window)
        control_frame.pack(pady=10, fill=tk.X)

        export_button = tk.Button(control_frame, text="Экспорт в Excel",
                                  command=lambda: export_to_excel(tree, columns),
                                  bg="#4CAF50", fg="white", font=button_font)
        export_button.pack(side=tk.LEFT, padx=10)

        help_button = tk.Button(control_frame, text="Справка",
                                command=lambda: show_help_window(results_window),
                                bg="#2196F3", fg="white", font=button_font)
        help_button.pack(side=tk.LEFT, padx=10)

        search_frame = tk.Frame(results_window)
        search_frame.pack(pady=15)
        search_inner_frame = tk.Frame(search_frame)
        search_inner_frame.pack()

        full_name_label = tk.Label(search_inner_frame, text="Поиск по ФИО:", font=label_font)
        full_name_label.grid(row=0, column=0, padx=5, pady=5)
        full_name_entry = tk.Entry(search_inner_frame, width=40, font=entry_font)
        full_name_entry.grid(row=0, column=1, padx=5, pady=5)

        date_label = tk.Label(search_inner_frame, text="Поиск по дате:", font=label_font)
        date_label.grid(row=0, column=2, padx=5, pady=5)
        date_entry = tk.Entry(search_inner_frame, width=30, font=entry_font)
        date_entry.grid(row=0, column=3, padx=5, pady=5)

        search_button = tk.Button(
            search_inner_frame,
            text="Поиск",
            command=lambda: filter_data(),
            font=button_font,
            bg="#4CAF50",
            fg="white"
        )
        search_button.grid(row=0, column=4, padx=5, pady=5)

        stats_frame = tk.Frame(results_window)
        stats_frame.pack(pady=15)

        stats_inner_frame = tk.Frame(stats_frame)
        stats_inner_frame.pack()

        avg_reaction_label = tk.Label(stats_inner_frame, text="Среднее время реакции: -", font=stats_font)
        avg_reaction_label.grid(row=0, column=0, padx=15, pady=5)

        avg_accuracy_label = tk.Label(stats_inner_frame, text="Средняя точность: -", font=stats_font)
        avg_accuracy_label.grid(row=0, column=1, padx=15, pady=5)

        std_dev_label = tk.Label(stats_inner_frame, text="Среднее СКО: -", font=stats_font)
        std_dev_label.grid(row=0, column=2, padx=15, pady=5)

        above_avg_var = tk.BooleanVar()
        above_avg_check = tk.Checkbutton(
            stats_inner_frame,
            text="Показать лучшие результаты",
            variable=above_avg_var,
            command=lambda: filter_data(),
            font=label_font
        )
        above_avg_check.grid(row=0, column=3, padx=15, pady=5)
        columns = (
            "Дата", "Имя", "Фамилия", "Отчество", "Возраст",
            "Среднее время реакции (мс)",
            "СКО (мс)",
            "Точность (%)",
            "Интерпретация"
        )

        style = ttk.Style()
        style.configure("Treeview", rowheight=45, font=('Helvetica', 12))
        style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'))
        tree_frame = tk.Frame(results_window)
        tree_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(tree_frame)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=canvas.yview)
        scrollbar_y.pack(side="right", fill="y")

        scrollbar_x = ttk.Scrollbar(results_window, orient="horizontal", command=canvas.xview)
        scrollbar_x.pack(side="bottom", fill="x")

        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        inner_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        style = ttk.Style()
        style.configure("Treeview", rowheight=70, font=('Helvetica', 12))
        style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'))

        tree = ttk.Treeview(inner_frame, columns=columns, show="headings", style="Treeview")

        for col in columns:
            tree.heading(col, text=col, command=lambda _col=col: sort_column(tree, _col, False))
            if col == "Интерпретация":
                tree.column(col, width=650, anchor="w")
            elif col == "Возраст":
                tree.column(col, width=80, anchor="center")
            elif col == "Среднее время реакции (мс)":
                tree.column(col, width=250, anchor="center")
            else:
                tree.column(col, width=120, anchor="center")

        tree.pack(fill="both", expand=True)

        def get_filtered_rows(full_name_filter="", date_filter=""):
            query = """
                 SELECT tr.id, tr.test_date, u.name, u.surname, u.patronymic, u.age, 
                         tr.avg_reaction_time, tr.std_deviation, 
                         tr.accuracy_percent, tr.full_interpretation
                  FROM test_results_reaction_test tr
                  JOIN users u ON tr.user_id = u.id
                  WHERE 1=1
              """
            params = []

            if full_name_filter:
                name_parts = [n.strip() for n in full_name_filter.split(",") if n.strip()]
                if name_parts:
                    name_conditions = []
                    for part in name_parts:
                        sub_parts = part.split()
                        sub_conditions = []
                        for sub_part in sub_parts:
                            sub_conditions.append("UPPER(u.name) LIKE UPPER(?)")
                            sub_conditions.append("UPPER(u.surname) LIKE UPPER(?)")
                            sub_conditions.append("UPPER(u.patronymic) LIKE UPPER(?)")
                            params.extend([f"%{sub_part}%"] * 3)
                        name_conditions.append(f"({' OR '.join(sub_conditions)})")
                    query += f" AND ({' OR '.join(name_conditions)})"

            if date_filter:
                date_list = [d.strip() for d in date_filter.split(",") if d.strip()]
                converted_dates = []
                for d in date_list:
                    try:
                        dt = datetime.strptime(d, "%d.%m.%Y")
                        converted_dates.append(dt.strftime("%Y-%m-%d") + "%")
                    except ValueError:
                        pass
                if converted_dates:
                    date_conditions = " OR ".join(["tr.test_date LIKE ?"] * len(converted_dates))
                    query += f" AND ({date_conditions})"
                    params.extend(converted_dates)

            query += " ORDER BY tr.test_date DESC"

            conn = sqlite3.connect("test_app.db")
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            return rows

        def compute_averages(rows):
            reaction_times = [float(r[6]) for r in rows if r[6] is not None]
            accuracy_values = [float(r[8]) for r in rows if r[8] is not None]
            std_devs = [float(r[7]) for r in rows if r[7] is not None]

            avg_reaction = sum(reaction_times) / len(reaction_times) if reaction_times else 0
            avg_accuracy = sum(accuracy_values) / len(accuracy_values) if accuracy_values else 0
            avg_std_dev = sum(std_devs) / len(std_devs) if std_devs else 0

            return avg_reaction, avg_accuracy, avg_std_dev

        def update_stats_labels(avg_reaction, avg_accuracy, std_dev):
            avg_reaction_label.config(text=f"Среднее время реакции: {avg_reaction:.2f} мс")
            avg_accuracy_label.config(text=f"Средняя точность: {avg_accuracy:.2f} %")
            std_dev_label.config(text=f"Среднее СКО: {std_dev:.2f} мс")

        self.results_viewer = ResultsViewer(results_window, save_mode="reaction_test")
        self.results_viewer.setup_editing(tree, columns)

        def filter_data():
            full_name_filter = full_name_entry.get().strip()
            date_filter = date_entry.get().strip()

            rows = get_filtered_rows(full_name_filter, date_filter)
            if above_avg_var.get():
                avg_reaction, avg_accuracy, std_dev = compute_averages(rows)
                rows = [
                    r for r in rows
                    if r[6] is not None and r[7] is not None and r[8] is not None
                       and float(r[6]) < avg_reaction
                       and float(r[7]) < std_dev
                       and float(r[8]) > avg_accuracy
                ]

            tree.delete(*tree.get_children())
            for row in rows:
                values = list(row[1:])

                if values[0]:
                    try:
                        values[0] = datetime.strptime(values[0], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
                    except ValueError:
                        try:
                            values[0] = datetime.strptime(values[0], "%Y-%m-%d").strftime("%d.%m.%Y")
                        except ValueError:
                            print("Некорректный формат даты. Используйте ДД.ММ.ГГГГ")

                if len(values) >= 9 and values[8]:
                    words = values[8].split()
                    lines, line, char_count = [], '', 0
                    for word in words:
                        if char_count + len(word) > 60:
                            lines.append(line.strip())
                            line = ''
                            char_count = 0
                        line += word + ' '
                        char_count += len(word) + 1
                    lines.append(line.strip())
                    values[8] = '\n'.join(lines[:3])

                tree.insert("", "end", iid=str(row[0]), values=values)

            avg_reaction, avg_accuracy, std_dev = compute_averages(rows)
            update_stats_labels(avg_reaction, avg_accuracy, std_dev)
        def sort_column(treeview, col, reverse):

            col_index = columns.index(col)
            try:
                data = [(treeview.set(k, col), k) for k in treeview.get_children('')]

                data = [(float(v[0].replace(',', '.')), v[1]) if v[0] != '' else (float('-inf'), v[1]) for v in data]
            except Exception:
                data = [(treeview.set(k, col), k) for k in treeview.get_children('')]

            data.sort(reverse=reverse)
            for index, (val, k) in enumerate(data):
                treeview.move(k, '', index)
            treeview.heading(col, command=lambda: sort_column(treeview, col, not reverse))

        filter_data()

    def show_simple_reaction_results(self):
        results_window = tk.Toplevel(self)
        results_window.title("Результаты: Простая зрительно-моторная реакция")
        results_window.state("zoomed")
        label_font = ('Helvetica', 13)
        entry_font = ('Helvetica', 13)
        button_font = ('Helvetica', 13, 'bold')
        stats_font = ('Helvetica', 13, 'bold')

        show_above_average = tk.BooleanVar()

        control_frame = tk.Frame(results_window)
        control_frame.pack(pady=10, fill=tk.X)

        export_button = tk.Button(control_frame, text="Экспорт в Excel",
                                  command=lambda: export_to_excel(tree, columns),
                                  bg="#4CAF50", fg="white", font=button_font)
        export_button.pack(side=tk.LEFT, padx=10)

        help_button = tk.Button(control_frame, text="Справка",
                                command=lambda: show_help_window(results_window),
                                bg="#2196F3", fg="white", font=button_font)
        help_button.pack(side=tk.LEFT, padx=10)

        filter_checkbox = tk.Checkbutton(control_frame, text="Показать лучшие результаты",
                                         variable=show_above_average, font=label_font,
                                         command=lambda: load_data(full_name_entry.get().strip(),
                                                                   date_entry.get().strip()))
        filter_checkbox.pack(side=tk.LEFT, padx=10)

        search_frame = tk.Frame(results_window)
        search_frame.pack(pady=15)

        full_name_label = tk.Label(search_frame, text="Поиск по ФИО:", font=label_font)
        full_name_label.grid(row=0, column=0, padx=5, pady=5)
        full_name_entry = tk.Entry(search_frame, width=40, font=entry_font)
        full_name_entry.grid(row=0, column=1, padx=5, pady=5)

        date_label = tk.Label(search_frame, text="Поиск по дате:", font=label_font)
        date_label.grid(row=0, column=2, padx=5, pady=5)
        date_entry = tk.Entry(search_frame, width=30, font=entry_font)
        date_entry.grid(row=0, column=3, padx=5, pady=5)

        search_button = tk.Button(search_frame, text="Поиск", command=lambda: load_data(
            full_name_entry.get().strip(),
            date_entry.get().strip()
        ), font=button_font,  bg="#4CAF50",fg="white")
        search_button.grid(row=0, column=4, padx=5, pady=5)

        stats_frame = tk.Frame(results_window)
        stats_frame.pack(pady=15)

        avg_reaction_label = tk.Label(stats_frame, text="Ср. время реакции: -", font=stats_font)
        avg_reaction_label.grid(row=0, column=0, padx=15, pady=5)
        avg_std_dev_label = tk.Label(stats_frame, text="Ср. СКО: -", font=stats_font)
        avg_std_dev_label.grid(row=0, column=1, padx=15, pady=5)
        avg_whipple_label = tk.Label(stats_frame, text="Ср. коэф. Уиппла: -", font=stats_font)
        avg_whipple_label.grid(row=0, column=2, padx=15, pady=5)

        columns = (
            "Дата", "Имя", "Фамилия", "Отчество", "Возраст",
            "Сред. время реакции", "СКО", "Коэфф. Уиппла", "Интерпретация"
        )

        style = ttk.Style()
        style.configure("Treeview", rowheight=80, font=('Helvetica', 12))
        style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'))

        tree_frame = tk.Frame(results_window)
        tree_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Treeview")

        col_widths = {
            "Дата": 120,
            "Имя": 120,
            "Фамилия": 140,
            "Отчество": 140,
            "Возраст": 100,
            "Сред. время реакции": 200,
            "СКО": 120,
            "Коэфф. Уиппла": 140,
            "Интерпретация": 600
        }

        for col in columns:
            tree.heading(col, text=col, command=lambda _col=col: sort_column(tree, _col, False))
            anchor = "w" if col == "Интерпретация" else "center"
            tree.column(col, width=col_widths.get(col, 120), anchor=anchor)

        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        editor = ResultsViewer(results_window, save_mode="simple")
        editor.setup_editing(tree, columns)

        def get_filtered_rows(full_name_filter="", date_filter=""):
            query = """
                SELECT tr.id, tr.test_date, u.id, u.name, u.surname, u.patronymic, u.age,
                       tr.avg_reaction_time, tr.std_deviation, tr.wippl_coefficient, tr.interpretation
                FROM test_results_simple_reaction tr
                JOIN users u ON tr.user_id = u.id
                WHERE 1=1
            """
            params = []

            if full_name_filter:
                name_parts = [n.strip() for n in full_name_filter.split(",") if n.strip()]
                if name_parts:
                    name_conditions = []
                    for part in name_parts:
                        sub_parts = part.split()
                        sub_conditions = []
                        for sub_part in sub_parts:
                            sub_conditions.append("UPPER(u.name) LIKE UPPER(?)")
                            sub_conditions.append("UPPER(u.surname) LIKE UPPER(?)")
                            sub_conditions.append("UPPER(u.patronymic) LIKE UPPER(?)")
                            params.extend([f"%{sub_part}%"] * 3)
                        name_conditions.append(f"({' OR '.join(sub_conditions)})")
                    query += f" AND ({' OR '.join(name_conditions)})"

            if date_filter:
                date_list = [d.strip() for d in date_filter.split(",") if d.strip()]
                sql_dates = []
                for date_str in date_list:
                    try:
                        parsed_date = datetime.strptime(date_str, "%d.%m.%Y")
                        sql_dates.append(parsed_date.strftime("%Y-%m-%d"))
                    except ValueError:
                        print("Некорректный формат даты. Используйте ДД.ММ.ГГГГ")
                if sql_dates:
                    date_conditions = " OR ".join(["DATE(tr.test_date) = ?"] * len(sql_dates))
                    query += f" AND ({date_conditions})"
                    params.extend(sql_dates)

            query += " ORDER BY tr.test_date DESC"

            conn = sqlite3.connect("test_app.db")
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            return rows

        def compute_averages(rows):
            reaction_times = [float(r[7]) for r in rows if r[7] is not None]
            std_deviations = [float(r[8]) for r in rows if r[8] is not None]
            whipple_coeffs = [float(r[9]) for r in rows if r[9] is not None]

            avg_reaction = sum(reaction_times) / len(reaction_times) if reaction_times else 0
            avg_std_dev = sum(std_deviations) / len(std_deviations) if std_deviations else 0

            valid_whipple = [w for w in whipple_coeffs if 0 <= w <= 1]
            avg_whipple = sum(valid_whipple) / len(valid_whipple) if valid_whipple else 0

            return avg_reaction, avg_std_dev, avg_whipple

        def load_data(full_name_filter="", date_filter=""):
            rows = get_filtered_rows(full_name_filter, date_filter)

            for row in tree.get_children():
                tree.delete(row)

            avg_reaction, avg_std_dev, avg_whipple = compute_averages(rows)

            avg_reaction_label.config(text=f"Среднее время реакции: {avg_reaction:.2f} мс")
            avg_std_dev_label.config(text=f"Среднее СКО: {avg_std_dev:.2f}")
            avg_whipple_label.config(text=f"Средний коэфф. Уиппла: {avg_whipple:.2f}")

            for row in rows:
                if show_above_average.get():
                    if not (
                            row[7] < avg_reaction and
                            row[8] < avg_std_dev and
                            row[9] > avg_whipple
                    ):
                        continue

                formatted_row = [
                    row[1],
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                    round(row[7], 2) if isinstance(row[7], float) else row[7],
                    round(row[8], 2) if isinstance(row[8], float) else row[8],
                    round(row[9], 2) if isinstance(row[9], float) else row[9],
                    row[10]
                ]
                try:
                    formatted_row[0] = datetime.strptime(formatted_row[0], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
                except:
                    pass

                tree.insert("", "end", iid=str(row[0]), values=formatted_row)

        def sort_column(tv, col, reverse):
            l = [(tv.set(k, col), k) for k in tv.get_children("")]
            if col == "Дата":
                l.sort(key=lambda x: datetime.strptime(x[0], "%d-%m-%Y") if x[0] else datetime.min, reverse=reverse)
            elif col in ("Сред. время реакции", "СКО", "Коэф. Уиппла"):
                try:
                    l.sort(key=lambda x: float(x[0]) if x[0] and x[0] != '-' else float('inf'), reverse=reverse)
                except:
                    l.sort(key=lambda x: (x[0] or "").lower(), reverse=reverse)
            else:
                l.sort(key=lambda x: (x[0] or "").lower(), reverse=reverse)

            for index, (val, k) in enumerate(l):
                tv.move(k, '', index)

            tv.heading(col, command=lambda: sort_column(tv, col, not reverse))

        load_data()

    def show_san_results(self):
        results_window = tk.Toplevel(self)
        results_window.title("Результаты: САН (Самочувствие, Активность, Настроение)")
        results_window.state("zoomed")

        label_font = ('Helvetica', 13)
        entry_font = ('Helvetica', 13)
        button_font = ('Helvetica', 13, 'bold')
        stats_font = ('Helvetica', 13, 'bold')

        control_frame = tk.Frame(results_window)
        control_frame.pack(pady=10, fill=tk.X)

        export_button = tk.Button(control_frame, text="Экспорт в Excel",
                                  command=lambda: export_to_excel(tree, columns),
                                  bg="#4CAF50", fg="white", font=button_font)
        export_button.pack(side=tk.LEFT, padx=10)

        help_button = tk.Button(control_frame, text="Справка",
                                command=lambda: show_help_window(results_window),
                                bg="#2196F3", fg="white", font=button_font)
        help_button.pack(side=tk.LEFT, padx=10)


        search_frame = tk.Frame(results_window)
        search_frame.pack(pady=15, fill=tk.X)


        search_frame.grid_columnconfigure(1, weight=1)
        search_frame.grid_columnconfigure(3, weight=1)

        full_name_label = tk.Label(search_frame, text="Поиск по ФИО:", font=label_font)
        full_name_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        full_name_entry = tk.Entry(search_frame, font=entry_font)
        full_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        date_label = tk.Label(search_frame, text="Поиск по дате:", font=label_font)
        date_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")

        date_entry = tk.Entry(search_frame, font=entry_font)
        date_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        search_button = tk.Button(search_frame, text="Поиск", font=button_font,
                                  command=lambda: filter_data(),bg="#4CAF50",fg="white")
        search_button.grid(row=0, column=4, padx=5, pady=5)


        stats_frame = tk.Frame(results_window)
        stats_frame.pack(pady=15, fill=tk.X)

        columns = (
            "Дата", "Имя", "Фамилия", "Отчество", "Возраст",
            "Самочувствие", "Состояние С",
            "Активность", "Состояние А",
            "Настроение", "Состояние Н"
        )

        style = ttk.Style()
        style.configure("Treeview", rowheight=35, font=('Helvetica', 12))
        style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'))


        table_frame = tk.Frame(results_window)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        tree = ttk.Treeview(table_frame, columns=columns, show="headings", style="Treeview")

        col_widths = {
            "Дата": 120,
            "Имя": 120,
            "Фамилия": 140,
            "Отчество": 140,
            "Возраст": 70,
            "Самочувствие": 130,
            "Состояние С": 130,
            "Активность": 110,
            "Состояние А": 130,
            "Настроение": 110,
            "Состояние Н": 130,
        }

        for col in columns:
            tree.heading(col, text=col, command=lambda _col=col: sort_column(tree, _col, False))
            tree.column(col, width=col_widths.get(col, 100), anchor="center")


        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)


        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")


        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)


        def adjust_column_widths(event):
            total_width = event.width
            fixed_cols = ["ID", "Возраст"]
            fixed_width = sum(col_widths.get(col, 100) for col in fixed_cols)
            flexible_cols = [col for col in columns if col not in fixed_cols]

            flexible_width = max(total_width - fixed_width - 20, 100)
            width_per_col = flexible_width // max(len(flexible_cols), 1)

            for col in columns:
                if col in fixed_cols:
                    tree.column(col, width=col_widths.get(col, 100))
                else:
                    tree.column(col, width=width_per_col)

        tree.bind("<Configure>", adjust_column_widths)

        def load_data(full_name_filter="", date_filter=""):
            for row in tree.get_children():
                tree.delete(row)

            query = """
                SELECT tr.test_date, u.id, u.name, u.surname, u.patronymic, u.age,
                       tr.samocuvstvie, tr.samocuvstvie_state,
                       tr.aktivnost, tr.aktivnost_state,
                       tr.nastroenie, tr.nastroenie_state
                FROM test_results_san_test tr
                JOIN users u ON tr.user_id = u.id
                WHERE 1=1
            """
            params = []

            if full_name_filter:
                name_chunks = [chunk.strip() for chunk in full_name_filter.split(",") if chunk.strip()]
                name_conditions = []

                for chunk in name_chunks:
                    parts = chunk.split()
                    if not parts:
                        continue
                    sub_conditions = []
                    for part in parts:
                        sub_conditions.append(
                            "(UPPER(u.name) LIKE UPPER(?) OR UPPER(u.surname) LIKE UPPER(?) OR UPPER(u.patronymic) LIKE UPPER(?))")
                        params.extend([f"%{part}%"] * 3)
                    name_conditions.append("(" + " AND ".join(sub_conditions) + ")")

                if name_conditions:
                    query += " AND (" + " OR ".join(name_conditions) + ")"
            if date_filter:
                try:
                    date_parts = [d.strip() for d in date_filter.split(",") if d.strip()]
                    sql_dates = []
                    for part in date_parts:
                        parsed = datetime.strptime(part, "%d.%m.%Y")
                        sql_dates.append(parsed.strftime("%Y-%m-%d"))
                    query += " AND (" + " OR ".join(["DATE(tr.test_date) = ?"] * len(sql_dates)) + ")"
                    params.extend(sql_dates)
                except ValueError:
                    print("Некорректный формат даты. Используйте ДД.ММ.ГГГГ")

            query += " ORDER BY tr.test_date DESC"

            conn = sqlite3.connect("test_app.db")
            cursor = conn.cursor()
            cursor.execute(query, params)

            for row in cursor.fetchall():
                try:
                    formatted_date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
                except:
                    formatted_date = row[0]
                tree.insert("", "end", values=(formatted_date, *row[2:]))

            conn.close()

        def filter_data():
            load_data(
                full_name_filter=full_name_entry.get().strip(),
                date_filter=date_entry.get().strip()
            )

        def sort_column(tv, col, reverse):
            l = [(tv.set(k, col), k) for k in tv.get_children("")]
            if col == "Дата":
                l.sort(key=lambda x: datetime.strptime(x[0], "%d-%m-%Y") if x[0] else datetime.min, reverse=reverse)
            else:
                l.sort(key=lambda x: (x[0] or "").lower(), reverse=reverse)

            for index, (val, k) in enumerate(l):
                tv.move(k, '', index)

            tv.heading(col, command=lambda: sort_column(tv, col, not reverse))

        load_data()

    def show_krepelin_results(self):
        results_window = tk.Toplevel(self)
        results_window.title("Результаты: Тест по Крепелину")
        results_window.state("zoomed")

        label_font = ('Helvetica', 13)
        entry_font = ('Helvetica', 13)
        button_font = ('Helvetica', 13, 'bold')

        style = ttk.Style()
        style.configure("Treeview",
                        rowheight=30,
                        font=('Helvetica', 12),
                        borderwidth=1,
                        relief="solid")
        style.configure("Treeview.Heading",
                        font=('Helvetica', 12, 'bold'),
                        background="#f0f0f0")
        style.map("Treeview", background=[('selected', '#347083')])

        control_frame = tk.Frame(results_window)
        control_frame.pack(pady=10, fill=tk.X)

        export_button = tk.Button(control_frame, text="Экспорт в Excel",
                                  command=lambda: export_to_excel(tree, columns),
                                  bg="#4CAF50", fg="white", font=button_font)
        export_button.pack(side=tk.LEFT, padx=10)

        help_button = tk.Button(control_frame, text="Справка",
                                command=lambda: show_help_window(results_window),
                                bg="#2196F3", fg="white", font=button_font)
        help_button.pack(side=tk.LEFT, padx=10)

        search_frame = tk.Frame(results_window)
        search_frame.pack(pady=10)

        inner_search_frame = tk.Frame(search_frame)
        inner_search_frame.pack()

        tk.Label(inner_search_frame, text="Поиск по ФИО:", font=label_font).grid(row=0, column=0, padx=5, pady=2)
        full_name_entry = tk.Entry(inner_search_frame, width=40, font=entry_font)
        full_name_entry.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(inner_search_frame, text="Поиск по дате:", font=label_font).grid(row=0, column=2, padx=5,
                                                                                               pady=2)
        date_entry = tk.Entry(inner_search_frame, width=20, font=entry_font)
        date_entry.grid(row=0, column=3, padx=5, pady=2)

        search_button = tk.Button(
            inner_search_frame,
            text="Поиск",
            command=lambda: load_data(full_name_entry.get(), date_entry.get()),
            font=button_font,
            bg="#4CAF50",
            fg="white"
        )
        search_button.grid(row=0, column=4, padx=10, pady=2)

        average_label = tk.Label(results_window, text="", font=('Helvetica', 13, 'bold'))
        average_label.pack(pady=5)

        above_avg_var = tk.BooleanVar()
        above_avg_check = tk.Checkbutton(results_window,
                                         text="Показать только результаты выше среднего",
                                         variable=above_avg_var,
                                         command=lambda: filter_data(),
                                         font=label_font)
        above_avg_check.pack(pady=5)

        columns = ("Дата", "Имя", "Фамилия", "Отчество", "Возраст",
                   "Коэфф. работоспособности", "Ошибки", "Интерпретация")

        table_frame = tk.Frame(results_window, width=800, height=500)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            tree.heading(col, text=col, anchor="center", command=lambda _col=col: sort_column(tree, _col, False))
            if col == "Дата":
                tree.column(col, width=120, anchor="center", stretch=False)
            elif col == "Имя":
                tree.column(col, width=120, anchor="center", stretch=False)
            elif col == "Фамилия":
                tree.column(col, width=140, anchor="center", stretch=False)
            elif col == "Отчество":
                tree.column(col, width=140, anchor="center", stretch=False)
            elif col == "Возраст":
                tree.column(col, width=90, anchor="center", stretch=False)
            elif col == "Коэфф. работоспособности":
                tree.column(col, width=240, anchor="center", stretch=False)
            elif col == "Ошибки":
                tree.column(col, width=80, anchor="center", stretch=False)
            elif col == "Интерпретация":
                tree.column(col, width=620, anchor="w", stretch=False)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)

        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.krepelin_data = []
        self.krepelin_average = 0.0

        def load_data(full_name_filter="", date_filter=""):
            tree.delete(*tree.get_children())
            self.krepelin_data = []

            conn = sqlite3.connect("test_app.db")
            cursor = conn.cursor()

            query = """
                SELECT tr.test_date, tr.id, u.name, u.surname, u.patronymic, u.age,
                       tr.K_work, tr.error_count, tr.interpret_results
                FROM test_results_krepelin_test tr
                JOIN users u ON tr.user_id = u.id
                WHERE 1=1
            """
            params = []

            if full_name_filter:
                parts = [p.strip() for p in full_name_filter.split() if p.strip()]
                for part in parts:
                    query += """
                        AND (u.name LIKE ? OR u.surname LIKE ? OR u.patronymic LIKE ?)
                    """
                    params.extend([f"%{part}%"] * 3)

            if date_filter:
                try:
                    date_parts = [d.strip() for d in date_filter.split(",") if d.strip()]
                    sql_dates = []
                    for part in date_parts:
                        parsed = datetime.strptime(part, "%d.%m.%Y")
                        sql_dates.append(parsed.strftime("%Y-%m-%d"))
                    query += " AND (" + " OR ".join(["DATE(tr.test_date) = ?"] * len(sql_dates)) + ")"
                    params.extend(sql_dates)
                except ValueError:
                    print("Некорректный формат даты. Используйте ДД.ММ.ГГГГ или несколько через запятую.")

            query += " ORDER BY tr.test_date DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            k_sum = 0
            count = 0

            for row in rows:
                try:
                    date_str = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y")
                except:
                    date_str = row[0]

                record_id = row[1]
                k_work = float(row[6])
                data_row = (
                    date_str,
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                    f"{k_work:.2f}",
                    row[7],
                    row[8]
                )

                self.krepelin_data.append((record_id, *data_row, k_work))
                k_sum += k_work
                count += 1

            self.krepelin_average = round(k_sum / count, 2) if count else 0.0
            average_label.config(text=f"Средний коэффициент работоспособности: {self.krepelin_average:.2f}")

            filter_data()

        def filter_data():
            tree.delete(*tree.get_children())
            for row in self.krepelin_data:
                record_id = row[0]
                values = row[1:-1]
                k_work = row[-1]

                if not above_avg_var.get() or k_work > self.krepelin_average:
                    tree.insert("", "end", iid=str(record_id), values=values)

        def sort_column(tv, col, reverse):
            l = [(tv.set(k, col), k) for k in tv.get_children("")]

            if col == "Дата":
                l.sort(key=lambda x: datetime.strptime(x[0], "%d.%m.%Y"), reverse=reverse)
            elif col in ("Коэффициент работоспособности", "Ошибки", "Возраст"):
                l.sort(key=lambda x: float(x[0].replace(',', '.')) if x[0] else 0, reverse=reverse)
            else:
                l.sort(key=lambda x: x[0].lower() if x[0] else "", reverse=reverse)

            for index, (val, k) in enumerate(l):
                tv.move(k, "", index)

            tv.heading(col, command=lambda: sort_column(tv, col, not reverse))

        load_data()
    def show_full_test_results(self):
        results_window = tk.Toplevel(self)
        results_window.title("Общие результаты всех тестов")
        results_window.state("zoomed")

        style = ttk.Style()
        style.configure("Treeview", rowheight=70)

        search_frame = tk.Frame(results_window)
        search_frame.pack(pady=10)

        full_name_label = tk.Label(search_frame, text="Поиск по ФИО:")
        full_name_label.grid(row=0, column=0, padx=5)
        full_name_entry = tk.Entry(search_frame, width=40)
        full_name_entry.grid(row=0, column=1, padx=5)

        date_label = tk.Label(search_frame, text="Поиск по дате :")
        date_label.grid(row=0, column=2, padx=5)
        date_entry = tk.Entry(search_frame)
        date_entry.grid(row=0, column=3, padx=5)

        search_button = tk.Button(search_frame, text="Поиск", command=lambda: filter_data())
        search_button.grid(row=0, column=4, padx=5)

        columns = (
            "Дата", "ID", "Имя", "Фамилия", "Отчество", "Возраст",
            "АМОД (баллы и интерпретация)",
            "Сложная ЗМР (интерпретация)",
            "Простая ЗМР (интерпретация)",
            "Крепелин (интерпретация)",
            "САН (самочувствие, активность, настроение)"
        )

        tree = ttk.Treeview(results_window, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col, command=lambda _col=col: sort_column(tree, _col, False))
            if col in ("ID", "Возраст"):
                tree.column(col, width=40, anchor="center")
            elif col in ("Дата", "Имя", "Фамилия", "Отчество"):
                tree.column(col, width=100, anchor="center")
            else:
                tree.column(col, width=200, anchor="center")

        tree.pack(fill="both", expand=True)

        def load_data(full_name_filter="", date_filter=""):
            for row in tree.get_children():
                tree.delete(row)

            query = """
                SELECT 
                    ftr.test_date, u.id, u.name, u.surname, u.patronymic, u.age,
                    ftr.adaptive_model_result,
                    ftr.complex_reaction_result,
                    ftr.simple_reaction_result,
                    ftr.krepelin_result,
                    ftr.san_result
                FROM full_test_results ftr
                JOIN users u ON ftr.user_id = u.id
                WHERE 1=1
            """
            params = []

            if full_name_filter:
                parts = full_name_filter.strip().split()
                for part in parts:
                    query += """
                        AND (
                            UPPER(u.name) LIKE UPPER(?)
                            OR UPPER(u.surname) LIKE UPPER(?)
                            OR UPPER(u.patronymic) LIKE UPPER(?)
                        )
                    """
                    params.extend([f"%{part}%"] * 3)

            if date_filter:
                query += " AND ftr.test_date LIKE ?"
                params.append(f"%{date_filter}%")

            query += " ORDER BY ftr.test_date DESC"

            conn = sqlite3.connect("test_app.db")
            cursor = conn.cursor()
            cursor.execute(query, params)

            for row in cursor.fetchall():
                try:
                    formatted_date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y")
                except:
                    formatted_date = row[0]
                tree.insert("", "end", values=(formatted_date, *row[1:]))

            conn.close()

        def filter_data():
            load_data(
                full_name_filter=full_name_entry.get().strip(),
                date_filter=date_entry.get().strip()
            )

        def sort_column(tv, col, reverse):
            l = [(tv.set(k, col), k) for k in tv.get_children("")]
            if col == "Дата":
                l.sort(key=lambda x: datetime.strptime(x[0], "%d-%m-%Y"), reverse=reverse)
            else:
                l.sort(key=lambda x: (x[0] or "").lower(), reverse=reverse)

            for index, (val, k) in enumerate(l):
                tv.move(k, '', index)

            tv.heading(col, command=lambda: sort_column(tv, col, not reverse))

        load_data()


if __name__ == "__main__":
    init_db()
    app = MainScreen()
    app.mainloop()


