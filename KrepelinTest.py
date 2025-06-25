import tkinter as tk
import random
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import simpledialog, messagebox

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

def position_window(window, width, height, x, y):
    window.geometry(f"{width}x{height}+{x}+{y}")


class KrepelinTestInstruction(tk.Toplevel):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.user_id = user_id


        self.user_name, self.user_patronymic, self.user_surname, self.user_age = self.get_user_data(user_id)

        self.title("Инструкция к тесту")
        self.state("zoomed")
        self.configure(bg="#f0f0f0")

        instruction_text = (
            "Счёт по Крепелину\n\n"
            "Перед Вами будут представлены 8 строк по 20 столбцов с числами от 1 до 9\n"
            "Вам необходимо последовательно складывать числа и записывать их в ответ, отбрасывая десятки\n"
            "Например, если сумма получилась 12, то Вы записываете только 2\n\n"
            "На каждую строку Вам отводится по 30 секунд.\n"
            "Постарайтесь выполнить как можно больше сложений и не допустить ошибки. Удачи!\n"
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
        cursor.execute("SELECT name, patronymic, surname, age FROM users WHERE id=?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def start_test(self):
        self.destroy()
        KrepelinTest(self.master, self.user_id)
class KrepelinTest(tk.Toplevel):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.user_id = user_id
        self.user_name, self.user_patronymic, self.user_surname, self.user_age = self.get_user_data(user_id)
        self.title("Счёт по Крепелину")
        self.state("zoomed")

        self.rows = 8
        self.cols = 20
        self.time_per_row = 30

        self.top_numbers = []
        self.bottom_numbers = []
        self.top_labels = []
        self.bottom_labels = []
        self.entries = []
        self.timers = []
        self.done_buttons = []
        self.row_done = []

        self.correct_first_four = []
        self.correct_last_four = []
        self.errors_per_row = []
        self.error_count = 0
        self.current_row = 0

        self.error_label = tk.Label(self, text=f"Ошибки: {self.error_count}", font=("Arial", 16))
        self.error_label.pack(anchor="e", padx=10, pady=(10, 0))

        self.table_frame = tk.Frame(self)
        self.table_frame.pack(pady=5)

        self.create_grid()

        self.start_button = tk.Button(self, text="Начать", font=("Arial", 12), command=self.start_test)
        self.start_button.pack(pady=5)

    def create_grid(self):
        for row in range(self.rows):
            row_top = []
            row_bottom = []
            row_top_labels = []
            row_bottom_labels = []
            row_entries = []

            for col in range(self.cols):
                top_val = random.randint(1, 9)
                bottom_val = random.randint(1, 9)
                lbl_top = tk.Label(self.table_frame, text="", font=("Arial", 12))
                lbl_top.grid(row=row * 3, column=col, padx=1, pady=1)
                row_top.append(top_val)
                row_top_labels.append(lbl_top)

                lbl_bottom = tk.Label(self.table_frame, text="", font=("Arial", 12))
                lbl_bottom.grid(row=row * 3 + 1, column=col, padx=1, pady=1)
                row_bottom.append(bottom_val)
                row_bottom_labels.append(lbl_bottom)

                vcmd = (self.register(self.validate_digit), "%P")

                entry = tk.Entry(
                    self.table_frame,
                    width=2,
                    font=("Arial", 12),
                    justify='center',
                    state='disabled',
                    bg='white',
                    validate="key",
                    validatecommand=vcmd
                )
                entry.grid(row=row * 3 + 2, column=col, padx=1, pady=1)
                row_entries.append(entry)
                entry.bind("<KeyRelease>", lambda event, r=row, c=col: self.auto_advance(event, r, c))

            self.top_numbers.append(row_top)
            self.bottom_numbers.append(row_bottom)
            self.top_labels.append(row_top_labels)
            self.bottom_labels.append(row_bottom_labels)
            self.entries.append(row_entries)

            timer_label = tk.Label(self.table_frame, text="0:00", font=("Arial", 12))
            timer_label.grid(row=row * 3, column=self.cols + 1, padx=5)
            self.timers.append(timer_label)

            btn = tk.Button(self.table_frame, text="Готово", font=("Arial", 9), state="disabled",
                            command=lambda r=row: self.finish_row(r))
            btn.grid(row=row * 3 + 1, column=self.cols + 1)
            self.done_buttons.append(btn)

            self.row_done.append(False)
            self.errors_per_row.append(0)

    def start_test(self):
        self.start_button.config(state="disabled")
        for row in range(self.rows):
            for col in range(self.cols):
                self.top_labels[row][col].config(text=str(self.top_numbers[row][col]))
                self.bottom_labels[row][col].config(text=str(self.bottom_numbers[row][col]))

        self.start_row(self.current_row)

    def start_row(self, row):
        for entry in self.entries[row]:
            entry.config(state='normal', bg='white')

        self.entries[row][0].focus_set()

        self.done_buttons[row].config(state='normal')
        self.row_done[row] = False
        self.update_timer(row, self.time_per_row)

    def update_timer(self, row, remaining):
        if self.row_done[row]:
            return

        self.timers[row].config(text=f"0:{remaining:02}")
        if remaining > 0:
            self.after(1000, lambda: self.update_timer(row, remaining - 1))
        else:
            self.finish_row(row)

    def validate_digit(self, P):
        return P.isdigit() and len(P) <= 1

    def auto_advance(self, event, row, col):
        value = event.widget.get()
        if len(value) == 1 and value.isdigit():
            next_col = col + 1
            if next_col < self.cols:
                self.entries[row][next_col].focus_set()
            else:
                self.finish_row(row)

    def finish_row(self, row):
        self.done_buttons[row].config(state="disabled")
        for entry in self.entries[row]:
            entry.config(state='disabled')

        errors = self.check_row(row)
        self.error_count += errors
        self.errors_per_row[row] = errors
        self.error_label.config(text=f"Ошибки: {self.error_count}")

        self.row_done[row] = True

        if row < 4:
            self.correct_first_four.append(self.cols - errors)
        elif row >= 4:
            self.correct_last_four.append(self.cols - errors)

        self.current_row += 1
        if self.current_row < self.rows:
            self.start_row(self.current_row)
        else:
            self.show_results()

    def get_user_data(self, user_id):
        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, patronymic, surname, age FROM users WHERE id=?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def check_row(self, row):
        errors = 0
        for col in range(self.cols):
            try:
                expected_sum = self.top_numbers[row][col] + self.bottom_numbers[row][col]
                expected_digit = expected_sum % 10
                user_input = self.entries[row][col].get()
                if user_input != str(expected_digit):
                    errors += 1
                    self.entries[row][col].config(bg="red")
                else:
                    self.entries[row][col].config(bg="lightgreen")
            except:
                errors += 1
                self.entries[row][col].config(bg="red")
        return errors

    def show_results(self):
        password_window = tk.Toplevel(self)
        def check_password_and_continue():
            entered_password = password_entry.get()

            try:
                conn = sqlite3.connect('test_app.db')
                cursor = conn.cursor()
                cursor.execute('SELECT password FROM settings LIMIT 1')
                result = cursor.fetchone()
                conn.close()

                if not result:
                    messagebox.showerror("Ошибка", "Пароль не установлен в системе!")
                    return

                correct_password = result[0]

                if entered_password == correct_password:
                    password_window.destroy()
                    self.show_interpretation_window()
                else:
                    messagebox.showerror("Ошибка", "Неверный пароль!")

            except sqlite3.OperationalError as e:
                messagebox.showerror("Ошибка БД", f"Ошибка доступа к базе данных: {e}")

        password_window.title("Доступ к интерпретации")
        password_window.geometry("300x150")

        center_window(password_window, 300, 150)

        password_window.grab_set()
        password_window.transient(self)
        password_window.focus_set()

        tk.Label(password_window, text="Введите пароль для просмотра результатов:").pack(pady=10)
        password_entry = tk.Entry(password_window, show="*", width=30)
        password_entry.pack(pady=5)
        password_entry.focus_set()

        ok_button = tk.Button(password_window, text="ОК", command=check_password_and_continue, bg="green", fg="white")
        ok_button.pack(pady=10)

    def show_interpretation_window(self):
        full_name = f"{self.user_surname} {self.user_name}"
        if hasattr(self, 'user_patronymic') and self.user_patronymic:
            full_name += f" {self.user_patronymic}"

        S1 = sum(self.correct_first_four)
        S2 = sum(self.correct_last_four)
        K_work = S2 / S1 if S1 > 0 else 0

        result_window = tk.Toplevel(self)
        result_window.title("Результаты и интерпретация")
        result_window_width = 600
        result_window_height = 400
        position_window(result_window, result_window_width, result_window_height, 950, 100)

        result_text = (
            f"Имя: {full_name}\n"
            f"Возраст: {self.user_age} лет\n\n"
            f"Коэффициент работоспособности: {K_work:.2f}\n"
            f"Ошибки: {self.error_count}\n\n"
            "Введите интерпретацию:"
        )

        label = tk.Label(result_window, text=result_text, justify="left", anchor="w")
        label.pack(padx=10, pady=10, anchor="w")

        interpretation_entry = tk.Text(result_window, height=5, width=60)
        interpretation_entry.pack(padx=10, pady=(0, 10))

        def on_submit():
            user_interpretation = interpretation_entry.get("1.0", tk.END).strip()
            if not user_interpretation:
                user_interpretation = "Интерпретация не предоставлена."

            self.save_results_to_db(K_work, self.error_count, user_interpretation)
            result_window.destroy()
            messagebox.showinfo("Завершено", "Результаты и интерпретация успешно сохранены.")

        submit_button = tk.Button(result_window, text="Сохранить интерпретацию", command=on_submit,bg="#4CAF50",fg="white")
        submit_button.pack(pady=5)

        self.plot_graph()

    def plot_graph(self):
        total_problems = [self.cols for _ in range(self.rows)]
        solved_problems = [self.cols - errors for errors in self.errors_per_row]
        errors = self.errors_per_row

        fig, (ax, ax_text) = plt.subplots(2, 1, figsize=(10, 10), gridspec_kw={'height_ratios': [3, 2]})

        ax.plot(range(self.rows), total_problems, label="Всего примеров", color="blue", linestyle="--", linewidth=1)
        ax.plot(range(self.rows), solved_problems, label="Верно решённые", color="green", marker="o", linestyle="-",
                markersize=6, linewidth=2)
        ax.bar(range(self.rows), errors, label="Ошибки", color="red", alpha=0.5)

        ax.set_title("Кривая работоспособности (Крепелин)")
        ax.set_xlabel("Номер строки")
        ax.set_ylabel("Количество примеров")
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        ax.xaxis.set_major_locator(plt.IndexLocator(base=1, offset=0))
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="upper right")

        for i, val in enumerate(solved_problems):
            ax.text(i, val + 0.5, str(val), ha="center", va="bottom", fontsize=10, color="green")

        instruction_text = (
            "Анализ графика:\n"
            "• Сильная разница в количестве вычисленных примеров между строками — возможные трудности включения внимания.\n"
            "• Рост ошибок по мере выполнения — признаки утомления и снижения устойчивости внимания.\n"
            "• Значительные колебания количества ошибок на протяжении теста — нестабильность внимания.\n"
            "• Отсутствие ошибок или их незначительное количество (2-3) — хорошая концентрация.\n"
            "Анализ коэффициента работоспособности:\n"
            "• Коэффициент работоспособности близкий к 1 — утомления почти нет.\n"
            "• Если коэффициент больше 1, то это свидетельствует о медленной врабатываемости испытуемого.\n"
            "• Чем ближе значение коэффициента к 0, тем больше истощение внимание и снижение работоспособности."
        )

        ax_text.axis("off")
        ax_text.text(0, 1, instruction_text, fontsize=10, va='top', ha='left', wrap=True)

        plt.tight_layout()


        graph_window = tk.Toplevel(self)
        graph_window.title("Кривая работоспособности")
        graph_window_width = 800
        graph_window_height = 800
        position_window(graph_window, graph_window_width, graph_window_height, 100, 100)

        canvas = FigureCanvasTkAgg(fig, master=graph_window)
        canvas.draw()
        canvas.get_tk_widget().pack()
    def interpret_results(self):
        interpretations = ["Анализ коэффициента работоспособности:\n"
        "• Близкий к 1 — утомления почти нет.\n"
        "• Ниже 1 — выше степень утомляемости."]

        return "\n\n".join(interpretations)

    def save_results_to_db(self, K_work, error_count, interpretation):
        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()
        test_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO test_results_krepelin_test (
                test_date,
                user_id,
                K_work,
                error_count,
                interpret_results
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            test_date,
            self.user_id,
            round(K_work, 4),
            error_count,
            interpretation
        ))

        krepelin_result_text = (
            f"Индекс работоспособности: {round(K_work, 2)}\n"
            f"Ошибок: {error_count}\n"
            f"Интерпретация: {interpretation}"
        )

        cursor.execute("""
            SELECT id FROM full_test_results
            WHERE user_id = ? AND DATE(test_date) = DATE(?)
        """, (self.user_id, test_date.split(' ')[0]))
        existing_entry = cursor.fetchone()

        if existing_entry:
            cursor.execute("""
                UPDATE full_test_results
                SET krepelin_result = ?
                WHERE id = ?
            """, (krepelin_result_text, existing_entry[0]))
        else:
            cursor.execute("""
                INSERT INTO full_test_results (
                    test_date,
                    user_id,
                    krepelin_result
                )
                VALUES (?, ?, ?)
            """, (test_date, self.user_id, krepelin_result_text))

        conn.commit()
        conn.close()

