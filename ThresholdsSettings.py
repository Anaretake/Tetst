import sqlite3
import tkinter as tk
from tkinter import messagebox
from thresholds import REACTION_SPEED_RANGES, STD_RANGES, ACCURACY_RANGES



class ThresholdsSettings(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Настройки порогов")
        self.resizable(False, False)


        self.entries = {
            "reaction": [],
            "std": [],
            "accuracy": []
        }

        self._build_section("Скорость реакции (мс)", REACTION_SPEED_RANGES, "reaction")
        self._build_section("СКО реакции (мс)", STD_RANGES, "std")
        self._build_section("Доля точных ответов (%)", ACCURACY_RANGES, "accuracy")

        tk.Button(self, text="Сохранить", font=("Arial", 14), command=self._on_save).pack(pady=10)

    def _build_section(self, title, ranges_list, key):
        frame = tk.LabelFrame(self, text=title, padx=10, pady=10, font=("Arial", 12))
        frame.pack(fill="x", padx=10, pady=5)

        for idx, (label, lo, hi) in enumerate(ranges_list):
            tk.Label(frame, text=label, width=30, anchor="w", font=("Arial", 11)) \
                .grid(row=idx, column=0, sticky="w", pady=2)

            lo_e = tk.Entry(frame, width=6, font=("Arial", 11))
            lo_e.insert(0, str(lo))
            lo_e.grid(row=idx, column=1, padx=5)

            hi_e = tk.Entry(frame, width=6, font=("Arial", 11))
            hi_e.insert(0, str(hi))
            hi_e.grid(row=idx, column=2, padx=5)

            self.entries[key].append((lo_e, hi_e))

    def _on_save(self):
        global REACTION_SPEED_RANGES, STD_RANGES, ACCURACY_RANGES

        new_ranges = {
            "reaction": [],
            "std": [],
            "accuracy": []
        }

        for key, lst in self.entries.items():
            for (lo_e, hi_e), (label, _, _) in zip(lst, {
                "reaction": REACTION_SPEED_RANGES,
                "std": STD_RANGES,
                "accuracy": ACCURACY_RANGES
            }[key]):
                try:
                    lo = float(lo_e.get().strip())
                    hi_raw = hi_e.get().strip()
                    hi = float(hi_raw) if hi_raw.lower() != "inf" else float("inf")
                    new_ranges[key].append((label, lo, hi))
                except ValueError:
                    messagebox.showerror("Ошибка", f"Неверный ввод диапазона: {lo_e.get()} — {hi_e.get()}")
                    return


        REACTION_SPEED_RANGES = new_ranges["reaction"]
        STD_RANGES = new_ranges["std"]
        ACCURACY_RANGES = new_ranges["accuracy"]


        self._update_ranges_in_db(new_ranges)

        print("Пороговые значения обновлены!")
        self.destroy()

    def _update_ranges_in_db(self, new_ranges):
        conn = sqlite3.connect("test_app.db")
        cur = conn.cursor()

        CATEGORY_MAP = {
            "reaction": "reaction_speed",
            "std": "std_deviation",
            "accuracy": "accuracy"
        }


        for short_key, ranges in new_ranges.items():
            db_category = CATEGORY_MAP[short_key]
            for interpretation, lo, hi in ranges:
                print(f"Обновление: {db_category} - {interpretation}: {lo} - {hi}")

                try:
                    cur.execute("""
                        UPDATE interpretation_ranges
                        SET range_start = ?, range_end = ?
                        WHERE category = ? AND interpretation = ?
                    """, (lo, hi, db_category, interpretation))
                except sqlite3.Error as e:
                    print(f"Ошибка при обновлении: {e}")
                    conn.rollback()
                    return

        conn.commit()
        conn.close()

        print("Обновленные диапазоны в базе данных:")
        for short_key, ranges in new_ranges.items():
            db_category = CATEGORY_MAP[short_key]
            for interpretation, lo, hi in ranges:
                print(f"{db_category} - {interpretation}: {lo} - {hi}")