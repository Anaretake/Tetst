import tkinter as tk
from tkinter import messagebox
import sqlite3
import statistics
from ThresholdsSettings import ThresholdsSettings


class SettingsMenu(tk.Toplevel):
    def __init__(self, master, user_id):
        super().__init__(master)
        self.title("Настройки")
        self.geometry("400x300")

        tk.Label(self, text="Выберите тест для настройки", font=("Arial", 14)).pack(pady=20)

        tk.Button(self, text="Адаптивная модель операторской деятельности", width=40, height=2,
                  command=self.open_adaptive_model_window).pack(pady=10)

        tk.Button(self, text="Тест на сложную зрительно-моторную реакцию", width=40, height=2,
                  command=self.configure_reaction_thresholds).pack(pady=10)

    def open_adaptive_model_window(self):

        adaptive_window = tk.Toplevel(self)
        adaptive_window.title("Адаптивная модель операторской деятельности")
        adaptive_window.geometry("600x400")


        tk.Button(adaptive_window, text="Рассчитать нормализованный Qfol", width=40, height=2,
                  command=self.calculate_normalized_qfol).pack(pady=10)


        tk.Button(adaptive_window, text="Применить", width=40, height=2,
                  command=self.apply_changes).pack(pady=10)

        self.display_qfol_table(adaptive_window)

    def display_qfol_table(self, window):
        import tkinter.ttk as ttk

        tree = ttk.Treeview(window, columns=("user_id", "qfol_value", "timestamp"), show="headings")
        tree.pack(pady=10)

        tree.heading("user_id", text="User ID")
        tree.heading("qfol_value", text="Qfol Value")
        tree.heading("timestamp", text="Timestamp")

        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, qfol_value, timestamp FROM qfol_raw_data")
        rows = cursor.fetchall()

        for row in rows:
            tree.insert("", "end", values=row)

        conn.close()

    def calculate_normalized_qfol(self):
        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()

        cursor.execute("SELECT qfol_value FROM qfol_raw_data WHERE user_id = ?", (self.user_id,))
        rows = cursor.fetchall()

        if not rows:
            messagebox.showinfo("Информация", "Нет данных для нормализации.")
            conn.close()
            return

        values = [row[0] for row in rows]

        mean_val = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(
            values) > 1 else 1

        normalized_values = [(x - mean_val) / std_dev for x in values]

        for i, normalized_value in enumerate(normalized_values):
            cursor.execute("""
                UPDATE qfol_raw_data
                SET qfol_value = ?
                WHERE user_id = ? AND timestamp = ?
            """, (normalized_value, self.user_id, rows[i][2]))

        conn.commit()
        conn.close()
    def apply_changes(self):
        conn = sqlite3.connect("test_app.db")
        cursor = conn.cursor()

        cursor.execute("SELECT value FROM normalization_stats WHERE key = ?", ("qfol_empirical_coefficient",))
        result = cursor.fetchone()

        if result and result[0] == 0:
            cursor.execute("""
                   INSERT INTO normalization_stats (key, value)
                   VALUES (?, ?)
               """, ("qfol_empirical_coefficient", 20000))

        conn.commit()
        conn.close()

    def configure_reaction_thresholds(self):
        ThresholdsSettings(self)