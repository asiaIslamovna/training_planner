import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime
import calendar


class CalendarPopup(tk.Toplevel):
    """Всплывающее окно календаря для выбора даты"""

    MONTH_NAMES = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    def __init__(self, owner, target_entry):
        super().__init__(owner)
        self.target = target_entry
        self.title("Календарь")
        self.geometry("320x290")
        self.resizable(False, False)

        self.view_date = datetime.now()
        self.picked_date = None

        self._build_ui()
        self._draw_calendar()

        self.transient(owner)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        self._place_in_center(owner)

    def _place_in_center(self, parent):
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        w, h = self.winfo_width(), self.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        top_bar = tk.Frame(self)
        top_bar.pack(pady=8)

        self.btn_prev = tk.Button(top_bar, text="◄", width=3, command=self._go_prev_month)
        self.btn_prev.pack(side=tk.LEFT, padx=4)

        self.lbl_month = tk.Label(top_bar, text="", width=20, font=("Arial", 10, "bold"))
        self.lbl_month.pack(side=tk.LEFT)

        self.btn_next = tk.Button(top_bar, text="►", width=3, command=self._go_next_month)
        self.btn_next.pack(side=tk.LEFT, padx=4)

        header_frame = tk.Frame(self)
        header_frame.pack(pady=3)
        for i, wd in enumerate(self.WEEKDAYS):
            tk.Label(header_frame, text=wd, width=4, font=("Arial", 8, "bold")).grid(row=0, column=i)

        self.days_area = tk.Frame(self)
        self.days_area.pack(pady=3)

        bottom_bar = tk.Frame(self)
        bottom_bar.pack(pady=8)
        tk.Button(bottom_bar, text="OK", width=9, command=self._confirm).pack(side=tk.LEFT, padx=4)
        tk.Button(bottom_bar, text="Отмена", width=9, command=self._cancel).pack(side=tk.LEFT, padx=4)

    def _draw_calendar(self):
        for w in self.days_area.winfo_children():
            w.destroy()

        self.lbl_month.config(text=f"{self.MONTH_NAMES[self.view_date.month - 1]} {self.view_date.year}")

        cal = calendar.monthcalendar(self.view_date.year, self.view_date.month)
        today = datetime.now().date()

        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0:
                    continue
                date_obj = datetime(self.view_date.year, self.view_date.month, day).date()

                if date_obj == today:
                    bg, fg = "#0078D7", "white"
                elif self.picked_date and date_obj == self.picked_date:
                    bg, fg = "#E5F3FF", "black"
                else:
                    bg, fg = "white", "black"

                btn = tk.Button(
                    self.days_area, text=str(day), width=4,
                    bg=bg, fg=fg,
                    command=lambda d=day: self._pick_day(d)
                )
                btn.grid(row=r, column=c, padx=1, pady=1)

    def _pick_day(self, day):
        self.picked_date = datetime(self.view_date.year, self.view_date.month, day).date()
        self._draw_calendar()

    def _go_prev_month(self):
        if self.view_date.month == 1:
            self.view_date = self.view_date.replace(year=self.view_date.year - 1, month=12)
        else:
            self.view_date = self.view_date.replace(month=self.view_date.month - 1)
        self._draw_calendar()

    def _go_next_month(self):
        if self.view_date.month == 12:
            self.view_date = self.view_date.replace(year=self.view_date.year + 1, month=1)
        else:
            self.view_date = self.view_date.replace(month=self.view_date.month + 1)
        self._draw_calendar()

    def _confirm(self):
        if self.picked_date:
            self.target.delete(0, tk.END)
            self.target.insert(0, self.picked_date.strftime("%d.%m.%Y"))
        self.destroy()

    def _cancel(self):
        self.destroy()


class WorkoutTracker:
    """Основной класс приложения для учёта тренировок"""

    WORKOUT_LIST = ["Бег", "Плавание", "Велосипед", "Силовая", "Йога", "Растяжка", "Другое"]

    def __init__(self, window):
        self.window = window
        self.window.title("Мой План Тренировок")
        self.window.geometry("980x720")

        self.storage_path = "workouts.json"
        self.records = []

        self._setup_ui()
        self._load_from_disk()

        self.window.protocol("WM_DELETE_WINDOW", self._safe_exit)

    # ------------------------------------------------------------------
    # Построение интерфейса
    # ------------------------------------------------------------------

    def _setup_ui(self):
        self._build_menu()

        # Панель ввода
        entry_panel = ttk.LabelFrame(self.window, text="Новая запись", padding=10)
        entry_panel.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ttk.Label(entry_panel, text="Дата (ДД.ММ.ГГГГ):").grid(row=0, column=0, sticky="w", pady=4)
        date_box = tk.Frame(entry_panel)
        date_box.grid(row=0, column=1, sticky="w", pady=4, padx=5)
        self.entry_date = ttk.Entry(date_box, width=15)
        self.entry_date.pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(date_box, text="📅", width=3,
                   command=lambda: CalendarPopup(self.window, self.entry_date)).pack(side=tk.LEFT)
        self.entry_date.bind('<KeyRelease>', self._auto_dots)
        self.entry_date.bind('<FocusOut>', self._fix_date_on_leave)

        ttk.Label(entry_panel, text="Вид тренировки:").grid(row=1, column=0, sticky="w", pady=4)
        self.combo_type = ttk.Combobox(entry_panel, values=self.WORKOUT_LIST, width=18)
        self.combo_type.grid(row=1, column=1, sticky="w", pady=4, padx=5)
        self.combo_type.set(self.WORKOUT_LIST[0])

        ttk.Label(entry_panel, text="Минуты:").grid(row=2, column=0, sticky="w", pady=4)
        self.entry_duration = ttk.Entry(entry_panel, width=20)
        self.entry_duration.grid(row=2, column=1, sticky="w", pady=4, padx=5)

        ttk.Button(entry_panel, text="Добавить в список", command=self._add_record).grid(
            row=3, column=0, columnspan=2, pady=10)

        # Панель фильтров
        filter_panel = ttk.LabelFrame(self.window, text="Поиск и фильтры", padding=10)
        filter_panel.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        ttk.Label(filter_panel, text="Дата:").grid(row=0, column=0, sticky="w", pady=4)
        f_date_box = tk.Frame(filter_panel)
        f_date_box.grid(row=0, column=1, sticky="w", pady=4, padx=5)
        self.filter_date = ttk.Entry(f_date_box, width=15)
        self.filter_date.pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(f_date_box, text="📅", width=3,
                   command=lambda: CalendarPopup(self.window, self.filter_date)).pack(side=tk.LEFT)
        self.filter_date.bind('<KeyRelease>', self._auto_dots)

        ttk.Label(filter_panel, text="Тип:").grid(row=1, column=0, sticky="w", pady=4)
        self.filter_type = ttk.Combobox(filter_panel, values=["Все"] + self.WORKOUT_LIST, width=18)
        self.filter_type.grid(row=1, column=1, sticky="w", pady=4, padx=5)
        self.filter_type.set("Все")

        ttk.Button(filter_panel, text="Показать", command=self._apply_filters).grid(row=2, column=0, padx=4, pady=4)
        ttk.Button(filter_panel, text="Сбросить", command=self._remove_filters).grid(row=2, column=1, padx=4, pady=4)

        # Таблица
        table_panel = ttk.LabelFrame(self.window, text="Мои тренировки", padding=10)
        table_panel.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        cols = ("date", "type", "duration")
        self.table = ttk.Treeview(table_panel, columns=cols, show="headings", height=16)
        self.table.heading("date", text="Дата")
        self.table.heading("type", text="Вид тренировки")
        self.table.heading("duration", text="Длительность (мин)")
        self.table.column("date", width=140)
        self.table.column("type", width=190)
        self.table.column("duration", width=140)

        scroller = ttk.Scrollbar(table_panel, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscrollcommand=scroller.set)
        self.table.grid(row=0, column=0, sticky="nsew")
        scroller.grid(row=0, column=1, sticky="ns")

        self.ctx_menu = tk.Menu(self.window, tearoff=0)
        self.ctx_menu.add_command(label="Удалить запись", command=self._delete_selected)
        self.table.bind("<Button-3>", self._on_right_click)

        # Статус
        self.status = ttk.Label(self.window, text="Готово", relief=tk.SUNKEN)
        self.status.grid(row=3, column=0, sticky="ew", padx=10, pady=4)

        self.window.grid_rowconfigure(2, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        table_panel.grid_rowconfigure(0, weight=1)
        table_panel.grid_columnconfigure(0, weight=1)

    def _build_menu(self):
        bar = tk.Menu(self.window)
        self.window.config(menu=bar)

        file_menu = tk.Menu(bar, tearoff=0)
        bar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Сохранить (Ctrl+S)", command=self._save_to_disk, accelerator="Ctrl+S")
        file_menu.add_command(label="Сохранить как...", command=self._save_as)
        file_menu.add_command(label="Загрузить...", command=self._open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Экспорт...", command=self._export)
        file_menu.add_command(label="Импорт...", command=self._import)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self._safe_exit)

        self.window.bind('<Control-s>', lambda e: self._save_to_disk())
        self.window.bind('<Control-S>', lambda e: self._save_to_disk())

    # ------------------------------------------------------------------
    # Работа с датой
    # ------------------------------------------------------------------

    def _auto_dots(self, event):
        widget = event.widget
        if event.keysym in ('BackSpace', 'Delete'):
            return
        digits = ''.join(c for c in widget.get() if c.isdigit())
        result = ''
        if len(digits) > 0:
            result = digits[:2]
        if len(digits) > 2:
            result += '.' + digits[2:4]
        if len(digits) > 4:
            result += '.' + digits[4:8]
        if result != widget.get():
            widget.delete(0, tk.END)
            widget.insert(0, result)
            widget.icursor(len(result))

    def _fix_date_on_leave(self, event=None):
        widget = event.widget if event else self.entry_date
        text = widget.get().strip()
        if not text:
            return
        digits = ''.join(c for c in text if c.isdigit())
        if len(digits) == 8:
            widget.delete(0, tk.END)
            widget.insert(0, f"{digits[:2]}.{digits[2:4]}.{digits[4:8]}")

    # ------------------------------------------------------------------
    # Валидация и основные операции
    # ------------------------------------------------------------------

    def _check_fields(self, date_str, dur_str):
        try:
            datetime.strptime(date_str, "%d.%m.%Y")
            minutes = int(dur_str)
            if minutes <= 0:
                messagebox.showerror("Ошибка", "Минуты должны быть больше нуля")
                return False
            return True
        except ValueError:
            messagebox.showerror("Ошибка", "Дата должна быть ДД.ММ.ГГГГ")
            return False

    def _add_record(self):
        d = self.entry_date.get().strip()
        t = self.combo_type.get()
        dur = self.entry_duration.get().strip()

        if not self._check_fields(d, dur):
            return

        self.records.append({"date": d, "type": t, "duration": int(dur)})
        self._save_to_disk()
        self._redraw_table()
        self._clear_form()
        messagebox.showinfo("Готово", "Запись добавлена")

    def _delete_selected(self):
        sel = self.table.selection()
        if not sel:
            return
        vals = self.table.item(sel[0], "values")
        for rec in self.records:
            if (rec["date"] == vals[0] and
                rec["type"] == vals[1] and
                rec["duration"] == int(vals[2])):
                self.records.remove(rec)
                break
        self._save_to_disk()
        self._redraw_table()

    # ------------------------------------------------------------------
    # Фильтрация
    # ------------------------------------------------------------------

    def _apply_filters(self):
        fd = self.filter_date.get().strip()
        ft = self.filter_type.get()
        filtered = self.records[:]

        if ft != "Все":
            filtered = [r for r in filtered if r["type"] == ft]
        if fd:
            filtered = [r for r in filtered if r["date"] == fd]

        self._redraw_table(filtered)

    def _remove_filters(self):
        self.filter_date.delete(0, tk.END)
        self.filter_type.set("Все")
        self._redraw_table()

    # ------------------------------------------------------------------
    # Таблица и форма
    # ------------------------------------------------------------------

    def _redraw_table(self, data=None):
        self.table.delete(*self.table.get_children())
        for rec in (data if data is not None else self.records):
            self.table.insert("", "end", values=(rec["date"], rec["type"], rec["duration"]))

    def _clear_form(self):
        self.entry_date.delete(0, tk.END)
        self.combo_type.set(self.WORKOUT_LIST[0])
        self.entry_duration.delete(0, tk.END)

    # ------------------------------------------------------------------
    # JSON: сохранение / загрузка / экспорт / импорт
    # ------------------------------------------------------------------

    def _save_to_disk(self):
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=4)
            self._update_status()
        except Exception as err:
            messagebox.showerror("Ошибка", f"Не сохранить: {err}")

    def _save_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")],
            title="Куда сохранить?"
        )
        if path:
            old = self.storage_path
            self.storage_path = path
            if not self._save_to_disk():
                self.storage_path = old

    def _open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")],
            title="Выбрать файл"
        )
        if path:
            self.storage_path = path
            self._load_from_disk()

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")],
            title="Экспорт"
        )
        if not path:
            return
        try:
            package = {
                "export_time": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "total": len(self.records),
                "types_used": list({r["type"] for r in self.records}),
                "items": self.records
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(package, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Экспорт", f"Готово: {path}")
        except Exception as err:
            messagebox.showerror("Ошибка", str(err))

    def _import(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("Все файлы", "*.*")],
            title="Импорт"
        )
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            if isinstance(raw, dict) and "items" in raw:
                items = raw["items"]
            elif isinstance(raw, list):
                items = raw
            else:
                messagebox.showerror("Ошибка", "Неизвестный формат")
                return

            valid = [it for it in items if all(k in it for k in ("date", "type", "duration"))]
            if not valid:
                messagebox.showerror("Ошибка", "Нет подходящих записей")
                return

            if messagebox.askyesno("Импорт", f"Найдено {len(valid)} записей.\nДа — заменить, Нет — добавить"):
                self.records = valid
            else:
                self.records.extend(valid)

            self._save_to_disk()
            self._redraw_table()
            messagebox.showinfo("Импорт", f"Добавлено {len(valid)}")
        except json.JSONDecodeError:
            messagebox.showerror("Ошибка", "Битый JSON")
        except Exception as err:
            messagebox.showerror("Ошибка", str(err))

    def _load_from_disk(self):
        if not os.path.exists(self.storage_path):
            self.records = []
            self._update_status()
            return
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and "items" in data:
                self.records = data["items"]
            else:
                self.records = data
            self._redraw_table()
            self._update_status()
        except Exception as err:
            messagebox.showwarning("Внимание", f"Ошибка загрузки: {err}")
            self.records = []

    def _update_status(self):
        size = os.path.getsize(self.storage_path) if os.path.exists(self.storage_path) else 0
        self.status.config(
            text=f"Файл: {self.storage_path} | Записей: {len(self.records)} | {size} байт"
        )

    # ------------------------------------------------------------------
    # Системные обработчики
    # ------------------------------------------------------------------

    def _on_right_click(self, event):
        row = self.table.identify_row(event.y)
        if row:
            self.table.selection_set(row)
            self.ctx_menu.post(event.x_root, event.y_root)

    def _safe_exit(self):
        self._save_to_disk()
        self.window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = WorkoutTracker(root)
    root.mainloop()