import tkinter as tk
from tkinter import messagebox
import random
import time
import numpy as np
from datetime import datetime
import sqlite3



def db_interpret(value: float, category: str, db_path="test_app.db") -> str:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT interpretation FROM interpretation_ranges
        WHERE category = ?
        AND ? BETWEEN range_start AND range_end
        ORDER BY range_start ASC
        LIMIT 1
    """, (category, value))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else "—"

class ReactionTestInstructionWindow(tk.Toplevel):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.user_id = user_id

        self.user_name, self.user_patronymic, self.user_surname, self.user_age = self.get_user_data(user_id)

        self.title("Инструкция к тесту на сложную зрительно-моторную реакцию")
        self.state("zoomed")
        self.configure(bg="#f0f0f0")

        instruction_text = (
            "Добро пожаловать в тест на сложную зрительно-моторную реакцию.\n\n"
            "В ходе теста Вам будет предложено реагировать на появление стимулов (кругов).\n"
            "Если круг будет зелёным, нажмите кнопку 'Ф' на клавиатуре или 'ДА' на панели.\n"
            "Если круг будет красным, нажмите кнопку 'В' на клавиатуре или 'НЕТ' на панели.\n\n"
            "Попробуйте реагировать как можно быстрее и точнее.\n"
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
        ReactionTest(self.user_id)


class ReactionTest(tk.Toplevel):
    def __init__(self, user_id):
        super().__init__()

        self.user_id = user_id

        self.user_name, self.user_patronymic, self.user_surname, self.user_age = self.get_user_data(user_id)
        self.title("Тест на сложную зрительно-моторную реакцию")
        self.state("zoomed")
        self.bind("<Key>", self.on_key_press)
        self.focus_set()

        self.canvas = tk.Canvas(self, bg="white", width=1920, height=600)
        self.canvas.pack()

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(pady=10)

        self.yes_button = tk.Button(
            self.button_frame,
            text="ДА",
            width=20,
            height=3,
            command=lambda: self.handle_reaction("yes"),
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            activeforeground="white",
            font=("Arial", 16, "bold"),
            relief=tk.RAISED,
            borderwidth=3
        )
        self.yes_button.pack(side="left", padx=10)

        self.no_button = tk.Button(
            self.button_frame,
            text="НЕТ",
            width=20,
            height=3,
            command=lambda: self.handle_reaction("no"),
            bg="#F44336",
            fg="white",
            activebackground="#d32f2f",
            activeforeground="white",
            font=("Arial", 16, "bold"),
            relief=tk.RAISED,
            borderwidth=3
        )
        self.no_button.pack(side="left", padx=10)

        self.test_running = False
        self.stimulus_count = 75
        self.current_circle = None
        self.current_color = None
        self.start_time = None
        self.reaction_times = []
        self.missed_stimuli = 0
        self.premature_reactions = 0
        self.incorrect_reactions = 0
        self.circle_count = 0

        self.countdown_seconds = 5
        self.countdown_text = None
        self.show_countdown()

    def on_key_press(self, event):
        if event.keycode == 65:
            self.handle_reaction("yes")
        elif event.keycode == 68:
            self.handle_reaction("no")

    def get_user_data(self, user_id):
        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, patronymic, surname, age FROM users WHERE id=?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def show_countdown(self):
        self.canvas.delete("all")

        self.countdown_text = self.canvas.create_text(
            760, 300, text=f"Тест начнётся через {self.countdown_seconds}",
            font=("Arial", 32), fill="black"
        )

        if self.countdown_seconds > 0:
            self.countdown_seconds -= 1
            self.after(1000, self.show_countdown)
        else:
            self.canvas.delete(self.countdown_text)
            self.test_running = True
            self.start_new_stimulus()

    def start_new_stimulus(self):
        if self.circle_count >= self.stimulus_count:
            self.end_test()
            return
        self.circle_count += 1
        delay = random.uniform(2, 5)
        self.after(int(delay * 1000), self.show_stimulus)

    def show_stimulus(self):
        self.canvas.delete("all")
        self.current_color = random.choice(["red", "green"])
        x, y = 760, 300
        radius = 150
        self.current_circle = self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=self.current_color)
        self.start_time = time.time()

    def handle_reaction(self, clicked_button):
        if not self.test_running:
            return

        if self.start_time is None or self.current_circle is None:
            self.premature_reactions += 1
            self.circle_count += 1
            self.start_new_stimulus()
            return

        reaction_time = time.time() - self.start_time
        correct_button = "yes" if self.current_color == "green" else "no"

        self.process_reaction(reaction_time, correct_button, clicked_button)

        try:
            self.canvas.delete(self.current_circle)
        except tk.TclError:
            pass

        self.current_circle = None
        self.start_time = None
        self.start_new_stimulus()

    def process_reaction(self, reaction_time, correct_button, clicked_button):
        if reaction_time < 0.2:
            self.premature_reactions += 1
        elif clicked_button == correct_button:
            self.reaction_times.append(reaction_time)
        else:
            self.incorrect_reactions += 1

        if reaction_time > 2:
            self.missed_stimuli += 1

    def end_test(self):
        if not self.test_running:
            return
        self.test_running = False

        reaction_times_ms = [rt * 1000 for rt in self.reaction_times]
        avg_reaction_time = np.mean(reaction_times_ms) if reaction_times_ms else 0
        std_deviation = np.std(reaction_times_ms) if reaction_times_ms else 0

        total_errors = self.missed_stimuli + self.premature_reactions + self.incorrect_reactions
        correct_reactions = len(self.reaction_times)
        total_stimuli = self.stimulus_count
        accuracy_percent = (correct_reactions / total_stimuli) * 100 if total_stimuli else 0

        reaction_speed_interpretation = db_interpret(avg_reaction_time, "reaction_speed")
        std_deviation_interpretation = db_interpret(std_deviation, "std_deviation")
        accuracy_interpretation = db_interpret(accuracy_percent, "accuracy")
        full_interpretation = (
            f"{reaction_speed_interpretation}\n"
            f"{std_deviation_interpretation}\n"
            f"{accuracy_interpretation}"
        )

        full_name = f"{self.user_surname} {self.user_name}"
        if hasattr(self, 'user_patronymic') and self.user_patronymic:
            full_name += f" {self.user_patronymic}"

        results_message = (
            f"Имя: {full_name}\n"
            f"Возраст: {self.user_age} лет\n\n"
            f"Среднее время реакции: {avg_reaction_time:.1f} мс — {reaction_speed_interpretation}\n\n"
            f"СКО времени реакции:     {std_deviation:.1f} мс — {std_deviation_interpretation}\n\n"
            f"Доля точных ответов:     {accuracy_percent:.2f}% — {accuracy_interpretation}\n\n"
            f"Пропущено стимулов:      {self.missed_stimuli}\n"
            f"Упреждающих реакций:    {self.premature_reactions}\n"
            f"Неправильных реакций:    {self.incorrect_reactions}\n"
            f"Общее количество ошибок: {total_errors}\n\n"
            f"Количество стимулов:      {self.circle_count}/{self.stimulus_count}\n"
        )

        messagebox.showinfo("Результаты теста", results_message)

        self.yes_button.config(state="disabled")
        self.no_button.config(state="disabled")

        try:
            self.canvas.delete("all")
        except tk.TclError:
            pass

        self.save_results_to_db(
            avg_reaction_time,
            std_deviation,
            accuracy_percent,
            full_interpretation
        )
        self.destroy()

    def save_results_to_db(self, avg_reaction_time, std_deviation, accuracy_percent, full_interpretation):
        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()
        test_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        avg_reaction_time = round(avg_reaction_time, 2)
        std_deviation = round(std_deviation, 2)
        accuracy_percent = round(accuracy_percent, 2)

        cursor.execute("""
            INSERT INTO test_results_reaction_test (
                test_date, user_id,
                avg_reaction_time, std_deviation, accuracy_percent,
                full_interpretation
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            test_date, self.user_id,
            avg_reaction_time, std_deviation, accuracy_percent,
            full_interpretation
        ))

        complex_reaction_result_text = full_interpretation

        cursor.execute("""
                SELECT id FROM full_test_results
                WHERE user_id = ? AND DATE(test_date) = DATE(?)
            """, (self.user_id, test_date.split(' ')[0]))
        existing_entry = cursor.fetchone()

        if existing_entry:
            cursor.execute("""
                    UPDATE full_test_results
                    SET complex_reaction_result = ?
                    WHERE id = ?
                """, (complex_reaction_result_text, existing_entry[0]))
        else:
            cursor.execute("""
                    INSERT INTO full_test_results (
                        test_date,
                        user_id,
                        complex_reaction_result
                    )
                    VALUES (?, ?, ?)
                """, (test_date, self.user_id, complex_reaction_result_text))

        conn.commit()
        conn.close()