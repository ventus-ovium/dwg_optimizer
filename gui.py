import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import sys  
import ctypes
from tkinterdnd2 import TkinterDnD, DND_FILES

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ToolTip(object):
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.tw = None

    def enter(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        
        # Создаем окно без рамок
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        
        # Дизайн самой подсказки
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffe0", relief='solid', borderwidth=1,
                       font=("Segoe UI", 9))
        label.pack(ipadx=4, ipady=4)

    def leave(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None

class AppWindow:
    def __init__(self, on_start_callback):
        try:
            myappid = 'mycompany.dwgoptimizer.ultimate.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass
        
        # Используем TkinterDnD вместо обычного Tk
        self.root = TkinterDnD.Tk()
        self.root.title("DWG Optimizer")
        self.root.geometry("750x600")
        self.root.minsize(700, 550)

        try:
            icon_path = resource_path("icon.ico")
            self.root.iconbitmap(default=icon_path)
        except Exception as e:
            print(f"Не удалось загрузить иконку: {e}")
        
        self.on_start_callback = on_start_callback
        self.selected_items = []
        self.cancel_flag = False
        
        # Переменные галочек
        self.var_replace_text = tk.BooleanVar(value=False)
        self.var_opt_dwg = tk.BooleanVar(value=True)
        self.var_print = tk.BooleanVar(value=True)
        self.var_merge = tk.BooleanVar(value=True)
        self.var_opt_pdf = tk.BooleanVar(value=True)

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        try: style.theme_use('vista')
        except: style.theme_use('clam')
        style.configure(".", font=("Segoe UI", 10))
        style.configure("Start.TButton", font=("Segoe UI", 11, "bold"), foreground="green")

    def _build_ui(self):
        main_container = ttk.Frame(self.root, padding="15")
        main_container.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # === ЛЕВАЯ КОЛОНКА ===
        left_panel = ttk.LabelFrame(top_frame, text=" Выбор операций ", padding="15")
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        #ttk.Label(left_panel, text="Выберите этапы:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Функция для быстрого создания ряда (Галочка + Иконка)
        def create_row(parent, text, var, tooltip_text, command=None, pady=5):
            row = ttk.Frame(parent)
            row.pack(fill=tk.X, pady=pady)
            ttk.Checkbutton(row, text=text, variable=var, command=command).pack(side=tk.LEFT)
            lbl = ttk.Label(row, text=" ℹ️ ", foreground="#999999", cursor="hand2")
            lbl.pack(side=tk.LEFT, padx=(5, 0))
            ToolTip(lbl, tooltip_text) # Привязываем нашу подсказку
            return row

        # --- 1. Блок замены текста ---
        # Здесь мы сохраняем row в переменную self.row_replace, чтобы поля ввода знали, куда "выезжать"
        self.row_replace = create_row(left_panel, "Замена текста", 
                                      self.var_replace_text, 
                                      "Ищет точное совпадение текста во всех пространствах чертежа\nи заменяет его на новый. Поддерживает TEXT и MTEXT.", 
                                      command=self._toggle_text_inputs, pady=2)
        
        self.frame_text = ttk.Frame(left_panel)
        ttk.Label(self.frame_text, text="Искать:", font=("Segoe UI", 8)).pack(anchor="w")
        self.entry_old = ttk.Entry(self.frame_text, width=22)
        self.entry_old.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(self.frame_text, text="Заменить на:", font=("Segoe UI", 8)).pack(anchor="w")
        self.entry_new = ttk.Entry(self.frame_text, width=22)
        self.entry_new.pack(fill=tk.X)
        self._toggle_text_inputs() 

        # Остальные галочки
        create_row(left_panel, "Сжатие DWG", self.var_opt_dwg, 
                   "Делает WBLOCK (ПБЛОК) чертежа, сбрасывает рамки\nизображений (FRAME=0) и удаляет неиспользуемый мусор")
        
        create_row(left_panel, "Печать в PDF", self.var_print, 
                   "Автоматически находит все листы чертежа и печатает\nих в PDF. .")
        
        create_row(left_panel, "Склейка PDF", self.var_merge, 
                   "Объединяет листы одного чертежа в многостраничный PDF,\nдля корректности работы используйте в листах DWG\nдля разных страниц одного чертежа окончания '_1', '_2', и т.д.\nПри наличии в одном DWG разных чертежей программа не объединяет их")
        
        create_row(left_panel, "Сжатие PDF", self.var_opt_pdf, 
                   "Сжимает потоки данных и оптимизирует структуру PDF,\nсущественно уменьшая вес итоговых файлов.")

        # === ПРАВАЯ КОЛОНКА ===
        right_panel = ttk.LabelFrame(top_frame, text=" Список файлов ", padding="10")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        toolbar = ttk.Frame(right_panel)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(toolbar, text="+ Папка", command=self._add_folder, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="+ Файлы", command=self._add_files, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Очистить всё", command=self._clear_list).pack(side=tk.RIGHT)
        ttk.Button(toolbar, text="Удалить", command=self._remove_selected).pack(side=tk.RIGHT, padx=(0, 5))

        list_frame = ttk.Frame(right_panel)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, font=("Consolas", 9), activestyle="none", bd=1, relief="solid", highlightthickness=0)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)
        
        # Подключаем Drag and Drop
        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind('<<Drop>>', self._on_drop)
        
        ttk.Label(right_panel, text="Перетащите файлы в это окно или воспользуйтесь кнопками выше", font=("Segoe UI", 8), foreground="gray").pack(anchor="w", pady=(5,0))

        # === НИЖНЯЯ ПАНЕЛЬ ===
        bottom_frame = ttk.Frame(main_container)
        bottom_frame.pack(fill=tk.X)

        status_frame = ttk.Frame(bottom_frame)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.lbl_status = ttk.Label(status_frame, text="Готов к работе", foreground="gray", font=("Segoe UI", 9))
        self.lbl_status.pack(side=tk.LEFT)
        self.lbl_time = ttk.Label(status_frame, text="", font=("Segoe UI", 9))
        self.lbl_time.pack(side=tk.RIGHT)

        self.progress = ttk.Progressbar(bottom_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X, pady=(0, 10))

        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(fill=tk.X)

        self.btn_start = ttk.Button(btn_frame, text="ЗАПУСТИТЬ ОБРАБОТКУ", style="Start.TButton", command=self._start_thread)
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 5))

        self.btn_stop = ttk.Button(btn_frame, text="ОСТАНОВИТЬ", command=self._stop_thread)
        self.btn_stop.pack(side=tk.RIGHT, fill=tk.X, ipady=5)
        self.btn_stop.state(['disabled'])

    # --- ЛОГИКА ---
    def _toggle_text_inputs(self):
        if self.var_replace_text.get():
            self.frame_text.pack(fill=tk.X, padx=20, pady=(0, 10), after=self.row_replace)
        else:
            self.frame_text.pack_forget()

    def _on_drop(self, event):
        dropped_files = self.root.tk.splitlist(event.data)
        for f in dropped_files:
            path = os.path.normpath(f)
            if path not in self.selected_items:
                if os.path.isdir(path):
                    self.selected_items.append(path)
                    self.listbox.insert(tk.END, f"📂 {path}")
                elif path.lower().endswith('.dwg'):
                    self.selected_items.append(path)
                    self.listbox.insert(tk.END, f"📄 {os.path.basename(path)}")

    def _add_folder(self):
        d = filedialog.askdirectory()
        if d:
            path = d.replace("/", "\\")
            if path not in self.selected_items:
                self.selected_items.append(path)
                self.listbox.insert(tk.END, f"📂 {path}")

    def _add_files(self):
        files = filedialog.askopenfilenames(filetypes=[("DWG Files", "*.dwg")])
        for f in files:
            path = f.replace("/", "\\")
            if path not in self.selected_items:
                self.selected_items.append(path)
                self.listbox.insert(tk.END, f"📄 {os.path.basename(path)}")

    def _remove_selected(self):
        selection = self.listbox.curselection()
        if not selection: return
        for index in reversed(selection):
            self.listbox.delete(index)
            del self.selected_items[index]

    def _clear_list(self):
        self.selected_items.clear()
        self.listbox.delete(0, tk.END)

    def _start_thread(self):
        if not self.selected_items:
            messagebox.showwarning("Внимание", "Список пуст!\nДобавьте файлы или папку для обработки.")
            return

        if self.var_replace_text.get() and not self.entry_old.get().strip():
            messagebox.showwarning("Внимание", "Укажите текст для поиска.")
            return

        self.cancel_flag = False

        settings = {
            "input_items": self.selected_items,
            "do_replace_text": self.var_replace_text.get(),
            "old_text": self.entry_old.get(),
            "new_text": self.entry_new.get(),
            "do_opt_dwg": self.var_opt_dwg.get(),
            "do_print": self.var_print.get(),
            "do_merge": self.var_merge.get(),
            "do_opt_pdf": self.var_opt_pdf.get(),
            "progress_callback": self.update_progress_ui,
            "status_callback": self.update_status_ui,
            "time_callback": self.update_time_ui,
            "is_cancelled": lambda: self.cancel_flag
        }
        
        self.btn_start.state(['disabled'])
        self.btn_stop.state(['!disabled'])
        self.progress["value"] = 0
        
        threading.Thread(target=self._run_process, args=(settings,), daemon=True).start()

    def _stop_thread(self):
        if messagebox.askyesno("Остановка", "Вы уверены, что хотите прервать обработку?\nТекущий файл будет безопасно доработан."):
            self.cancel_flag = True
            self.lbl_status.config(text="⏳ Остановка... Дожидаемся завершения...", foreground="red")
            self.btn_stop.state(['disabled'])

    def _run_process(self, settings):
        try:
            result_time = self.on_start_callback(settings)
            msg = "Все задачи выполнены успешно!"
            if result_time and isinstance(result_time, str):
                msg += f"\n\n⏱ Затраченное время: {result_time}"
            self.root.after(0, lambda: messagebox.showinfo("Готово", msg))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", f"Критический сбой: {e}"))
        finally:
            self.root.after(0, self._reset_ui)

    def _reset_ui(self):
        self.btn_start.state(['!disabled'])
        self.btn_stop.state(['disabled'])
        self.lbl_status.config(text="Готово", foreground="green")
        self.progress["value"] = 100
        self.lbl_time.config(text="")

    def update_progress_ui(self, percent):
        self.root.after(0, lambda: self.progress.configure(value=percent))

    def update_status_ui(self, text):
        self.root.after(0, lambda: self.lbl_status.configure(text=text, foreground="black"))

    def update_time_ui(self, text):
        self.root.after(0, lambda: self.lbl_time.configure(text=text))

    def run(self):
        self.root.mainloop()
