import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

class ResultsViewer:
    def __init__(self, parent, save_mode="simple"):
        self.parent = parent
        self.edit_window = None
        self.edit_entry = None
        self.current_item = None
        self.current_col = None
        self.tree = None
        self.columns = []
        self.save_mode = save_mode
    def setup_editing(self, tree, columns):
        self.tree = tree
        self.columns = columns
        tree.bind("<Double-1>", self.on_double_click)

    def save_changes(self):
        if self.current_item is None or self.current_col is None:
            return

        new_value = self.edit_entry.get("1.0", tk.END).strip()

        values = list(self.tree.item(self.current_item, 'values'))
        values[self.current_col] = new_value
        self.tree.item(self.current_item, values=values)

        try:
            record_id = int(self.current_item)
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный ID записи.")
            return
        try:
            conn = sqlite3.connect("test_app.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE test_results_simple_reaction
                SET interpretation = ?
                WHERE id = ?
            """, (new_value, record_id))
            conn.commit()
            messagebox.showinfo("Успешно", "Интерпретация сохранена для выбранной строки.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить изменения:\n{str(e)}")
            return
        finally:
            conn.close()

        if self.edit_window:
            self.edit_window.destroy()

    def save_changes_reaction_test(self):
        if self.current_item is None or self.current_col is None:
            return

        new_value = self.edit_entry.get("1.0", tk.END).strip()

        values = list(self.tree.item(self.current_item, 'values'))
        values[self.current_col] = new_value
        self.tree.item(self.current_item, values=values)

        try:
            record_id = int(self.current_item)
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный ID записи.")
            return

        try:
            conn = sqlite3.connect("test_app.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE test_results_reaction_test
                SET full_interpretation = ?
                WHERE id = ?
            """, (new_value, record_id))
            conn.commit()
            messagebox.showinfo("Успешно", "Интерпретация сохранена для выбранной строки.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить изменения:\n{str(e)}")
            return
        finally:
            conn.close()

        if self.edit_window:
            self.edit_window.destroy()

    def save_changes_test_results(self):
        if self.current_item is None or self.current_col is None:
            return

        new_value = self.edit_entry.get("1.0", tk.END).strip()

        values = list(self.tree.item(self.current_item, 'values'))
        values[self.current_col] = new_value
        self.tree.item(self.current_item, values=values)

        try:
            record_id = int(self.current_item)
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный ID записи.")
            return

        try:
            conn = sqlite3.connect("test_app.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE test_results
                SET ball_comment = ?
                WHERE id = ?
            """, (new_value, record_id))
            conn.commit()
            messagebox.showinfo("Успешно", "Интерпретация сохранена для выбранной строки.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить изменения:\n{str(e)}")
            return
        finally:
            conn.close()

        if self.edit_window:
            self.edit_window.destroy()

    def save_changes_krepelin_test(self):
        if self.current_item is None or self.current_col is None:
            return

        new_value = self.edit_entry.get("1.0", tk.END).strip()

        values = list(self.tree.item(self.current_item, 'values'))
        values[self.current_col] = new_value
        self.tree.item(self.current_item, values=values)

        try:
            record_id = int(self.current_item)
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный ID записи.")
            return

        try:
            conn = sqlite3.connect("test_app.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE test_results_krepelin_test
                SET interpret_results = ?
                WHERE id = ?
            """, (new_value, record_id))
            conn.commit()
            messagebox.showinfo("Успешно", "Интерпретация сохранена для выбранной строки.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить изменения:\n{str(e)}")
            return
        finally:
            conn.close()

        if self.edit_window:
            self.edit_window.destroy()

    def on_double_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region not in ("cell", "tree"):
            return

        col = self.tree.identify_column(event.x)
        row = self.tree.identify_row(event.y)

        if not row:
            return

        col_index = int(col[1:]) - 1

        if self.columns[col_index] != "Интерпретация":
            return

        current_values = self.tree.item(row, 'values')
        current_value = current_values[col_index]

        self.edit_window = tk.Toplevel(self.parent)
        self.edit_window.title("Редактирование интерпретации")
        window_width = 800
        window_height = 400

        screen_width = self.edit_window.winfo_screenwidth()
        screen_height = self.edit_window.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.edit_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.edit_window.resizable(False, False)

        self.edit_entry = tk.Text(self.edit_window, wrap=tk.WORD, font=('Helvetica', 12), height=15)
        self.edit_entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
        self.edit_entry.insert("1.0", current_value)

        button_frame = tk.Frame(self.edit_window)
        button_frame.pack(pady=10)

        save_button = tk.Button(button_frame,
                                text="Сохранить изменения",
                                command=self._get_save_function(),
                                bg="#4CAF50",
                                fg="white",
                                font=('Helvetica', 10, 'bold'))
        save_button.pack(side=tk.LEFT, padx=10)

        cancel_button = tk.Button(button_frame,
                                  text="Отмена",
                                  command=self.edit_window.destroy,
                                  bg="#f44336",
                                  fg="white",
                                  font=('Helvetica', 10))
        cancel_button.pack(side=tk.LEFT, padx=10)

        self.current_item = row
        self.current_col = col_index

    def _get_save_function(self):
        if self.save_mode == "reaction_test":
            return self.save_changes_reaction_test
        elif self.save_mode == "test_results":
            return self.save_changes_test_results
        elif self.save_mode == "krepelin_test":
            return self.save_changes_krepelin_test
        else:
            return self.save_changes