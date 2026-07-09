import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import sys  
import ctypes
from tkinterdnd2 import TkinterDnD, DND_FILES

def resource_path(relative_path):
    """ Получает абсолютный путь к ресурсу, работает и для dev, и для PyInstaller """
    try:
        # PyInstaller создает временную папку и хранит путь в _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class AppWindow:
    def __init__(self, on_start_callback):

        try:
            myappid = 'mycompany.dwgoptimizer.ultimate.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass
        
        self.root = TkinterDnD.Tk()
        self.root.title("DWG Optimizer")
        self.root.geometry("750x550")
        self.root.minsize(700, 500)

        myappid = 'mycompany.dwgoptimizer.ultimate.1.0' # Любая уникальная строка
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        try:
            icon_path = resource_path("icon.ico")
            self.root.iconbitmap(default=icon_path)
        except Exception as e:
            print(f"Не удалось загрузить иконку: {e}")
        
        self.on_start_callback = on_start_callback
        self.selected_items = []
        self.cancel_flag = False
        
        # Переменные галочек
        self.var_opt_dwg = tk.BooleanVar(value=True)
        self.var_print = tk.BooleanVar(value=True)
        self.var_merge = tk.BooleanVar(value=True)
        self.var_opt_pdf = tk.BooleanVar(value=True)

        # Настройка стилей
        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use('vista')  # На Windows дает нативный вид
        except:
            style.theme_use('clam')   # Если vista недоступна

        # Основные шрифты
        base_font = ("Segoe UI", 10)
        bold_font = ("Segoe UI", 10, "bold")
        header_font = ("Segoe UI", 12, "bold")
        
        # Настройка цветов и шрифтов для виджетов
        style.configure(".", font=base_font)
        style.configure("TButton", padding=5)
        style.configure("Header.TLabel", font=header_font)
        style.configure("Bold.TCheckbutton", font=bold_font)
        
        # Стиль для большой кнопки Старт
        style.configure("Start.TButton", font=("Segoe UI", 11, "bold"), foreground="green")

    def _build_ui(self):
        # Главный контейнер с отступами
        main_container = ttk.Frame(self.root, padding="15")
        main_container.pack(fill=tk.BOTH, expand=True)

        # --- ВЕРХНЯЯ ЧАСТЬ (Разделена на две колонки) ---
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # === ЛЕВАЯ КОЛОНКА (Действия) ===
        left_panel = ttk.LabelFrame(top_frame, text=" Выбор операций ", padding="15")
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        #ttk.Label(left_panel, text="Выберите этапы:", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 10))
        
        ttk.Checkbutton(left_panel, text="1. Сжатие DWG", variable=self.var_opt_dwg).pack(anchor="w", pady=5)
        ttk.Checkbutton(left_panel, text="2. Печать в PDF", variable=self.var_print).pack(anchor="w", pady=5)
        ttk.Checkbutton(left_panel, text="3. Склейка PDF", variable=self.var_merge).pack(anchor="w", pady=5)
        ttk.Checkbutton(left_panel, text="4. Сжатие PDF", variable=self.var_opt_pdf).pack(anchor="w", pady=5)

        #ttk.Separator(left_panel, orient="horizontal").pack(fill=tk.X, pady=15)
        
        #ttk.Label(left_panel, text="Инфо:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        #ttk.Label(left_panel, text="• Удаление .bak и .log\n  выполняется всегда.\n• Склейка работает\n  только для файлов\n  из одного DWG.", 
        #          font=("Segoe UI", 8), foreground="gray").pack(anchor="w", pady=5)

        # === ПРАВАЯ КОЛОНКА (Список файлов) ===
        right_panel = ttk.LabelFrame(top_frame, text=" Очередь файлов ", padding="10")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Панель инструментов списка
        toolbar = ttk.Frame(right_panel)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(toolbar, text="+ Папка", command=self._add_folder, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="+ Файлы", command=self._add_files, width=10).pack(side=tk.LEFT, padx=(0, 5))
        
        # Кнопки удаления справа
        ttk.Button(toolbar, text="Очистить всё", command=self._clear_list).pack(side=tk.RIGHT)
        ttk.Button(toolbar, text="Удалить", command=self._remove_selected).pack(side=tk.RIGHT, padx=(0, 5))

        # Список с скроллбаром
        list_frame = ttk.Frame(right_panel)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, 
                                  font=("Consolas", 9), activestyle="none",
                                  bd=1, relief="solid", highlightthickness=0)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)
        self.listbox.drop_target_register(DND_FILES)
        self.listbox.dnd_bind('<<Drop>>', self._on_drop)
        
        # Подсказка под списком
        ttk.Label(right_panel, text="Перетащите файлы сюда или используйте кнопки выше", 
                  font=("Segoe UI", 8), foreground="gray").pack(anchor="w", pady=(5,0))

        # --- НИЖНЯЯ ЧАСТЬ (Статус и Запуск) ---
        bottom_frame = ttk.Frame(main_container)
        bottom_frame.pack(fill=tk.X)

        # Статус бар
        status_frame = ttk.Frame(bottom_frame)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.lbl_status = ttk.Label(status_frame, text="Готов к работе", foreground="#0066cc", font=("Segoe UI", 9, "bold"))
        self.lbl_status.pack(side=tk.LEFT)
        
        self.lbl_time = ttk.Label(status_frame, text="", font=("Segoe UI", 9))
        self.lbl_time.pack(side=tk.RIGHT)

        # Прогресс бар
        self.progress = ttk.Progressbar(bottom_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # --- БЛОК КНОПОК ЗАПУСКА И ОСТАНОВКИ ---
        btn_frame = ttk.Frame(bottom_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        self.btn_start = ttk.Button(btn_frame, text="ЗАПУСТИТЬ ОБРАБОТКУ", style="Start.TButton", command=self._start_thread)
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 5))

        self.btn_stop = ttk.Button(btn_frame, text="ОСТАНОВИТЬ", command=self._stop_thread)
        self.btn_stop.pack(side=tk.RIGHT, fill=tk.X, ipady=5)
        self.btn_stop.state(['disabled']) # По умолчанию кнопка остановки отключена

    # --- ЛОГИКА ---
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

    def _on_drop(self, event):
        # Библиотека возвращает пути одной строкой, разбиваем их безопасно
        dropped_files = self.root.tk.splitlist(event.data)
        
        for f in dropped_files:
            path = os.path.normpath(f) # Приводим слеши к стандарту Windows
            if path not in self.selected_items:
                if os.path.isdir(path):
                    self.selected_items.append(path)
                    self.listbox.insert(tk.END, f"📂 {path}")
                elif path.lower().endswith('.dwg'):
                    self.selected_items.append(path)
                    self.listbox.insert(tk.END, f"📄 {os.path.basename(path)}")

    def _remove_selected(self):
        # Получаем индексы выделенных элементов
        selection = self.listbox.curselection()
        if not selection:
            return
            
        # Удаляем с конца, чтобы не сбивались индексы
        for index in reversed(selection):
            self.listbox.delete(index)
            # Удаляем из внутреннего списка данных
            del self.selected_items[index]

    def _clear_list(self):
        self.selected_items.clear()
        self.listbox.delete(0, tk.END)

    def _start_thread(self):
        if not self.selected_items:
            messagebox.showwarning("Внимание", "Список пуст!\nДобавьте файлы или папку для обработки.")
            return

        self.cancel_flag = False  # Сбрасываем флаг перед новым запуском

        settings = {
            "input_items": self.selected_items,
            "do_opt_dwg": self.var_opt_dwg.get(),
            "do_print": self.var_print.get(),
            "do_merge": self.var_merge.get(),
            "do_opt_pdf": self.var_opt_pdf.get(),
            "progress_callback": self.update_progress_ui,
            "status_callback": self.update_status_ui,
            "time_callback": self.update_time_ui,
            "is_cancelled": lambda: self.cancel_flag  # <-- ПЕРЕДАЕМ ФУНКЦИЮ ПРОВЕРКИ ФЛАГА
        }
        
        self.btn_start.state(['disabled'])
        self.btn_stop.state(['!disabled']) # Включаем кнопку "Остановить"
        self.progress["value"] = 0
        
        threading.Thread(target=self._run_process, args=(settings,), daemon=True).start()

    def _stop_thread(self):
        """ Срабатывает при нажатии кнопки ОСТАНОВИТЬ """
        if messagebox.askyesno("Остановка", "Вы уверены, что хотите прервать обработку?\nТекущий файл будет безопасно доработан."):
            self.cancel_flag = True
            self.lbl_status.config(text="⏳ Остановка... Дожидаемся завершения текущего процесса...", foreground="red")
            self.btn_stop.state(['disabled']) # Отключаем кнопку, чтобы не жали 100 раз

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
        self.btn_stop.state(['disabled'])  # Отключаем кнопку остановки
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
