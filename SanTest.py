import tkinter as tk
from tkinter import messagebox
import sqlite3
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

class SanTestInstruction(tk.Toplevel):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.user_id = user_id

        self.user_name, self.user_patronymic, self.user_surname, self.user_age = self.get_user_data(user_id)

        self.title("Инструкция к тесту САН")
        self.state("zoomed")
        self.configure(bg="#f0f0f0")

        instruction_text = (
            "Тест 'Самочувствие, активность, настроение'\n\n"
            "Вы увидите пары противоположных характеристик (например, 'Веселый — Грустный').\n"
            "Ваша задача — выбрать кнопку с числом от 1 до 3, которая отражает, насколько вы\n"
            "чувствуете себя ближе к одному из утверждений:\n\n"
            "   3 — полностью соответствует левому/правому утверждению\n"
            "   2 — скорее соответствует\n"
            "   1 — немного соответствует\n\n"
            "Оценивайте своё текущее состояние. Не раздумывайте долго.\n"
            "После ответа на 30 пар будет выведен результат.\n\n"
            "Нажмите кнопку ниже, чтобы начать тест."
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
        SanTest(self.user_id)
class SanTest(tk.Toplevel):
    def __init__(self, user_id):
        super().__init__()

        self.user_id = user_id

        self.user_name, self.user_patronymic, self.user_surname, self.user_age = self.get_user_data(user_id)
        self.title("Тест САН")
        self.state("zoomed")
        self.configure(bg="white")

        self.questions = [
            ("Самочувствие хорошее", "Самочувствие плохое", False),
            ("Чувствую себя сильным", "Чувствую себя слабым", False),
            ("Пассивный", "Активный", True),
            ("Малоподвижный", "Подвижный", True),
            ("Веселый", "Грустный", False),
            ("Хорошее настроение", "Плохое настроение", False),
            ("Работоспособный", "Разбитый", False),
            ("Полный сил", "Обессиленный", False),
            ("Медлительный", "Быстрый", True),
            ("Бездеятельный", "Деятельный", True),
            ("Счастливый", "Несчастный", False),
            ("Жизнерадостный", "Мрачный", False),
            ("Напряженный", "Расслабленный", True),
            ("Здоровый", "Больной", False),
            ("Безучастный", "Увлеченный", True),
            ("Равнодушный", "Заинтересованный", True),
            ("Восторженный", "Унылый", False),
            ("Радостный", "Печальный", False),
            ("Отдохнувший", "Усталый", False),
            ("Свежий", "Изнуренный", False),
            ("Сонливый", "Возбужденный", True),
            ("Желание отдохнуть", "Желание работать", True),
            ("Спокойный", "Взволнованный", False),
            ("Оптимистичный", "Пессимистичный", False),
            ("Выносливый", "Утомляемый", False),
            ("Бодрый", "Вялый", False),
            ("Соображать трудно", "Соображать легко", True),
            ("Рассеянный", "Внимательный", True),
            ("Полный надежд", "Разочарованный", False),
            ("Довольный", "Недовольный", False),
        ]

        self.answers = []
        self.question_index = 0

        self.content_frame = tk.Frame(self, bg="white")
        self.content_frame.pack(expand=True, fill="both", pady=50)

        self.left_label = tk.Label(self.content_frame, text="", font=("Arial", 20), width=20, anchor="e", bg="white")
        self.left_label.pack(side="left", padx=20, pady=20)

        self.scale_frame = tk.Frame(self.content_frame, bg="white")
        self.scale_frame.pack(side="left", expand=True)

        self.right_label = tk.Label(self.content_frame, text="", font=("Arial", 20), width=20, anchor="w", bg="white")
        self.right_label.pack(side="right", padx=20, pady=20)

        self.display_question()


    def display_question(self):
        for widget in self.scale_frame.winfo_children():
            widget.destroy()

        if self.question_index >= len(self.questions):
            self.show_results()
            return

        left, right, _ = self.questions[self.question_index]
        self.left_label.config(text=left)
        self.right_label.config(text=right)

        for i in range(-3, 4):
            btn = tk.Button(
                self.scale_frame,
                text=str(abs(i)),
                width=3,
                height=2,
                font=("Arial", 20),
                bg="lightgray",
                fg="black",
                command=lambda i=i: self.record_answer(i)
            )
            btn.grid(row=0, column=i + 3, padx=10, pady=20)
    def get_user_data(self, user_id):
        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, patronymic, surname, age FROM users WHERE id=?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result

    def record_answer(self, answer):
        self.answers.append(answer)
        self.question_index += 1
        self.display_question()

    def show_results(self):
        def compute_score(answer, positive_on_right):
            return 4 + answer if positive_on_right else 4 - answer

        raw_scores = [
            compute_score(ans, positive_on_right=pos_right)
            for ans, (_, _, pos_right) in zip(self.answers, self.questions)
        ]

        scales = {
            "Самочувствие": [0, 1, 6, 7, 12, 13, 18, 19, 24, 25],
            "Активность": [2, 3, 8, 9, 14, 15, 20, 21, 26, 27],
            "Настроение": [4, 5, 10, 11, 16, 17, 22, 23, 28, 29]
        }

        results = {}
        interpretation = {}

        for scale, indices in scales.items():
            values = [raw_scores[i] for i in indices]
            avg = sum(values) / len(values)
            results[scale] = round(avg, 2)

            if 5.0 <= avg <= 5.5:
                state = "норма"
            elif avg > 5.5:
                state = "благоприятное"
            elif 4.0 <= avg < 5.0:
                state = "благоприятное"
            else:
                state = "неблагоприятное"

            interpretation[scale] = state

        full_name = f"{self.user_surname} {self.user_name}"
        if hasattr(self, 'user_patronymic') and self.user_patronymic:
            full_name += f" {self.user_patronymic}"

        result_text = f"Имя: {full_name}:\nВозраст: {self.user_age} лет\n\n"
        for scale in results:
            result_text += f"{scale}: {results[scale]} — {interpretation[scale]}\n"

        messagebox.showinfo("Результаты", result_text)
        self.save_results_to_db(results, interpretation)
        self.destroy()
    def save_results_to_db(self, results, interpretation):
        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO test_results_san_test (
                test_date,
                user_id,
                samocuvstvie,
                aktivnost,
                nastroenie,
                samocuvstvie_state,
                aktivnost_state,
                nastroenie_state
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            self.user_id,
            results["Самочувствие"],
            results["Активность"],
            results["Настроение"],
            interpretation["Самочувствие"],
            interpretation["Активность"],
            interpretation["Настроение"]
        ))

        san_result_text = (
            f"Самочувствие: {interpretation['Самочувствие']}\n"
            f"Активность: {interpretation['Активность']}\n"
            f"Настроение: {interpretation['Настроение']}"
        )

        cursor.execute("""
               SELECT id FROM full_test_results
               WHERE user_id = ? AND DATE(test_date) = DATE(?)
           """, (self.user_id, datetime.now().strftime("%Y-%m-%d")))
        existing_entry = cursor.fetchone()

        if existing_entry:
            cursor.execute("""
                   UPDATE full_test_results
                   SET san_result = ?
                   WHERE id = ?
               """, (san_result_text, existing_entry[0]))
        else:
            cursor.execute("""
                   INSERT INTO full_test_results (
                       test_date,
                       user_id,
                       san_result
                   )
                   VALUES (?, ?, ?)
               """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.user_id, san_result_text))

        conn.commit()
        conn.close()
