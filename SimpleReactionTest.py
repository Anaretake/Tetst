import tkinter as tk
from tkinter import messagebox
import random
import time
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from datetime import datetime
import sqlite3


class SimpleReactionTestInstructionWindow(tk.Toplevel):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.user_id = user_id

        self.user_name, self.user_patronymic, self.user_surname, self.user_age = self.get_user_data(user_id)

        self.title("Инструкция к тесту на простую зрительно-моторную реакцию")
        self.state("zoomed")
        self.configure(bg="#f0f0f0")

        instruction_text = (
            "Тест на простую зрительно-моторную реакцию\n\n"
            "Вам предстоит отреагировать на серию из 75 световых стимулов зелёного цвета.\n"
            "Первые 5 стимулов — тренировочные и не учитываются при подсчёте результатов.\n\n"
            "Каждый раз, как только увидите зелёный круг, нажмите на стимул ЛКМ как можно быстрее.\n"
            "Если нажмёте до появления стимула — это будет считаться упреждающей ошибкой.\n"
            "Если не нажмёте вовремя — стимул будет считаться пропущенным.\n\n"
            "Удачи!\n"
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
        SimpleReactionTest(self.user_id)
class SimpleReactionTest(tk.Toplevel):
    def __init__(self, user_id):
        super().__init__()

        self.user_id = user_id

        self.user_name, self.user_patronymic, self.user_surname, self.user_age = self.get_user_data(user_id)

        self.title("Тест на простую зрительно-моторную реакцию")
        self.state("zoomed")

        self.canvas = tk.Canvas(self, bg="white", width=1920, height=1080)
        self.canvas.pack()



        self.total_stimuli = 30
        self.training_stimuli = 5
        self.valid_stimuli = 5

        self.stimulus_index = 0
        self.reaction_times = []
        self.premature_reactions = 0
        self.missed_stimuli = 0

        self.stimulus_ready = False
        self.stimulus_id = None
        self.start_time = None
        self.test_ended = False

        self.draw_red_circle()
        self.after(1000, self.next_trial)

    def draw_red_circle(self):
        self.after(100, self._draw_red_circle_actual)

    def _draw_red_circle_actual(self):
        self.canvas.delete("all")

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            self.after(100, self._draw_red_circle_actual)
            return

        x = canvas_width // 2
        y = canvas_height // 2
        radius = 150

        self.stimulus_id = self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill="red", tags="circle"
        )
        self.canvas.tag_bind("circle", "<Button-1>", self.handle_click)

    def turn_circle_green(self):
        self.canvas.itemconfig(self.stimulus_id, fill="green")
        self.start_time = time.time()
        self.stimulus_ready = True
        self.after(2000, self.check_missed_stimulus)

    def next_trial(self):
        if self.stimulus_index >= self.total_stimuli:
            self.end_test()
            return

        self.stimulus_ready = False
        self.canvas.itemconfig(self.stimulus_id, fill="red")


        delay = random.uniform(2, 5)
        self.after(int(delay * 1000), self.turn_circle_green)

    def get_user_data(self, user_id):
        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, patronymic, surname, age FROM users WHERE id=?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def handle_click(self, event):
        current_time = time.time()

        if not self.stimulus_ready:
            self.premature_reactions += 1
            self.stimulus_ready = False
            self.stimulus_index += 1
            self.canvas.itemconfig(self.stimulus_id, fill="red")

            if self.stimulus_index >= self.total_stimuli:
                self.end_test()
            else:
                delay = random.uniform(2, 5)
                self.after(int(delay * 1000), self.turn_circle_green)
            return

        reaction_time = (current_time - self.start_time) * 1000

        if reaction_time < 150:
            self.premature_reactions += 1
        elif reaction_time > 2000:
            self.missed_stimuli += 1
        elif self.stimulus_index >= self.training_stimuli:
            self.reaction_times.append(reaction_time)

        self.stimulus_index += 1
        self.stimulus_ready = False
        self.canvas.itemconfig(self.stimulus_id, fill="red")

        if self.stimulus_index >= self.total_stimuli:
            self.end_test()
        else:
            delay = random.uniform(2, 5)
            self.after(int(delay * 1000), self.turn_circle_green)
    def check_missed_stimulus(self):
        if self.stimulus_ready:
            self.stimulus_ready = False
            self.stimulus_index += 1
            if self.stimulus_index > self.training_stimuli:
                self.missed_stimuli += 1
            self.canvas.itemconfig(self.stimulus_id, fill="red")


            delay = random.uniform(2, 5)
            self.after(int(delay * 1000), self.next_trial)

    def interpret_reaction_time(self, avg_time):
        if avg_time < 220:
            return "Высокая скорость реагирования обработки информации "
        elif 220 <= avg_time <= 250:
            return "Хорошая скорость реакции"
        elif 251 <= avg_time <= 280:
            return "Средняя скорость реакции"
        else:
            return "Замедление реакции,возможно утомление"

    def interpret_std_deviation(self, std_dev):
        if std_dev < 40:
            return "Высокая стабильность реакции"
        elif 40 <= std_dev <= 90:
            return "Допустимые колебания внимания"
        else:
            return "Возможно нарушение внимания или наличие отвлекающих факторов"

    def interpret_wippl_coefficient(self, wippl_coefficient):
        if 0.90 <= wippl_coefficient <= 1.00:
            return "Отличная точность выполнения"
        elif 0.80 <= wippl_coefficient < 0.90:
            return "Незначительное число ошибок"
        elif 0.70 <= wippl_coefficient < 0.80:
            return "Среднее количество ошибок"
        else:
            return "Снижение точности выполнения, большое количество ошибок"

    def end_test(self):
        if self.test_ended:
            return

        self.test_ended = True
        avg_time = np.mean(self.reaction_times) if self.reaction_times else 0
        std_dev = np.std(self.reaction_times) if self.reaction_times else 0

        N = self.total_stimuli
        P = self.premature_reactions
        M = self.missed_stimuli

        if N > 0:
            wippl_coefficient = (N - (P + M)) / N
            wippl_coefficient = max(0, min(1, wippl_coefficient))
        else:
            wippl_coefficient = 0

        reaction_time_interpretation = self.interpret_reaction_time(avg_time)
        std_deviation_interpretation = self.interpret_std_deviation(std_dev)
        wippl_interpretation = self.interpret_wippl_coefficient(wippl_coefficient)
        full_interpretation = (
            f"Скорость: {reaction_time_interpretation}\n"
            f"СКО: {std_deviation_interpretation}\n"
            f"Точность: {wippl_interpretation}"
        )

        full_name = f"{self.user_surname} {self.user_name}"
        if hasattr(self, 'user_patronymic') and self.user_patronymic:
            full_name += f" {self.user_patronymic}"
        results_text = (
            f"Имя: {full_name}\n"
            f"Возраст: {self.user_age} лет\n\n"
            f"Среднее время реакции: {avg_time:.2f} мс\n"
            f"Интерпретация: {reaction_time_interpretation}\n\n"
            f"СКО (стандартное отклонение): {std_dev:.2f} мс\n"
            f"Количество упреждающих реакций: {self.premature_reactions}\n"
            f"Количество пропущенных стимулов: {self.missed_stimuli}\n"
            f"Общее количество ошибок: {self.premature_reactions + self.missed_stimuli}\n"
            f"Всего учтённых стимулов: {len(self.reaction_times)} из {self.valid_stimuli}\n\n"
            f"Коэффициент Уиппла: {wippl_coefficient:.2f}\n"
            f"Интерпретация: {wippl_interpretation}\n"
        )

        messagebox.showinfo("Результаты теста", results_text)
        self.save_reaction_test_result(
            avg_time=avg_time,
            std_dev=std_dev,
            wippl_coefficient=wippl_coefficient,
            interpretation=full_interpretation
        )


    def show_results_window(self, results_text):
        result_window = tk.Toplevel(self)
        result_window.title("Результаты")
        result_window.geometry("500x400")

        text_widget = tk.Text(result_window, wrap="word", font=("Arial", 12))
        text_widget.insert("1.0", results_text)
        text_widget.config(state="disabled")
        text_widget.pack(expand=True, fill="both", padx=10, pady=10)

        button_frame = tk.Frame(result_window)
        button_frame.pack(pady=10)

        graph_button = tk.Button(button_frame, text="Показать график", command=self.plot_reaction_times)
        graph_button.pack(side="left", padx=10)

        close_button = tk.Button(button_frame, text="Закрыть", command=lambda: [result_window.destroy(), self.destroy()])
        close_button.pack(side="right", padx=10)

    def plot_reaction_times(self):
        if not self.reaction_times:
            return
        plt.figure(figsize=(8, 4))
        plt.plot(self.reaction_times, marker='o', linestyle='-', color='green')
        plt.title("Время реакции на каждый стимул")
        plt.xlabel("Номер стимула")
        plt.ylabel("Время реакции (мс)")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def save_reaction_test_result(self, avg_time, std_dev, wippl_coefficient, interpretation):
        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()

        test_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO test_results_simple_reaction (
                test_date, user_id, avg_reaction_time, std_deviation, wippl_coefficient, interpretation
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (test_date, self.user_id, avg_time, std_dev, wippl_coefficient, interpretation))


        simple_reaction_result_text = interpretation


        cursor.execute("""
                SELECT id FROM full_test_results
                WHERE user_id = ? AND DATE(test_date) = DATE(?)
            """, (self.user_id, test_date.split(' ')[0]))
        existing_entry = cursor.fetchone()

        if existing_entry:

            cursor.execute("""
                    UPDATE full_test_results
                    SET simple_reaction_result = ?
                    WHERE id = ?
                """, (simple_reaction_result_text, existing_entry[0]))
        else:

            cursor.execute("""
                    INSERT INTO full_test_results (
                        test_date,
                        user_id,
                        simple_reaction_result
                    )
                    VALUES (?, ?, ?)
                """, (test_date, self.user_id, simple_reaction_result_text))

        conn.commit()
        conn.close()