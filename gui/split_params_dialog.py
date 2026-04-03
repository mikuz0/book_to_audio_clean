import tkinter as tk
from tkinter import ttk

class SplitParamsDialog:
    """Диалоговое окно для настройки параметров разбиения текста"""
    
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Параметры разбиения текста")
        self.dialog.geometry("650x650")
        self.dialog.minsize(550, 550)
        self.dialog.resizable(True, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.value_vars = {}
        
        self.setup_ui()
        self.load_values()
        
        # Центрируем окно
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Создание интерфейса окна"""
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Пояснение
        info_label = ttk.Label(main_frame, 
            text="Настройка разбиения текста на фрагменты.\n"
                 "Фрагменты оптимальной длины помогают избежать артефактов (хвостов).\n\n"
                 "Алгоритм работы:\n"
                 "1. Базовое разбиение по главным разделителям\n"
                 "2. Объединение коротких фрагментов до минимальной длины\n"
                 "3. Разбиение длинных фрагментов по второстепенным разделителям\n"
                 "4. Объединение коротких фрагментов (второй проход)\n"
                 "5. Восстановление знаков препинания по исходному тексту\n"
                 "6. Добавление символа завершения в конец фрагмента\n"
                 "7. Нормализация пробелов",
            wraplength=580, justify=tk.LEFT)
        info_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Минимальная длина
        self._create_slider(main_frame, "Минимальная длина фрагмента:", 
                            "split_min_length", 50, 200, 10, 2, is_int=True,
                            tooltip="Фрагменты короче этого значения будут объединены с соседними")
        
        # Максимальная длина
        self._create_slider(main_frame, "Максимальная длина фрагмента:", 
                            "split_max_length", 150, 500, 10, 3, is_int=True,
                            tooltip="Фрагменты длиннее этого значения будут разбиты по второстепенным разделителям")
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Главные разделители
        ttk.Label(main_frame, text="Главные разделители (базовое разбиение):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.primary_delimiters_var = tk.StringVar()
        primary_entry = ttk.Entry(main_frame, textvariable=self.primary_delimiters_var, width=30)
        primary_entry.grid(row=5, column=1, sticky=tk.W, padx=5)
        ttk.Label(main_frame, text="Пример: .!?", font=('TkDefaultFont', 8, 'italic')).grid(row=6, column=1, sticky=tk.W, padx=5)
        
        # Второстепенные разделители
        ttk.Label(main_frame, text="Второстепенные разделители (для разбиения длинных):").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.secondary_delimiters_var = tk.StringVar()
        secondary_entry = ttk.Entry(main_frame, textvariable=self.secondary_delimiters_var, width=30)
        secondary_entry.grid(row=7, column=1, sticky=tk.W, padx=5)
        ttk.Label(main_frame, text="Пример: :;", font=('TkDefaultFont', 8, 'italic')).grid(row=8, column=1, sticky=tk.W, padx=5)
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Символ завершения фрагмента
        ttk.Label(main_frame, text="Символ завершения фрагмента:").grid(row=10, column=0, sticky=tk.W, pady=5)
        self.terminator_var = tk.StringVar()
        terminator_entry = ttk.Entry(main_frame, textvariable=self.terminator_var, width=10)
        terminator_entry.grid(row=10, column=1, sticky=tk.W, padx=5)
        ttk.Label(main_frame, text="Точка (.), восклицательный знак (!), вопросительный знак (?),\n"
                                   "многоточие (...), пробел ( ) или оставить пустым.\n"
                                   "Пустое поле = ничего не добавлять.",
                  font=('TkDefaultFont', 8, 'italic'), wraplength=400).grid(row=11, column=0, columnspan=2, sticky=tk.W, padx=5)
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').grid(row=12, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Дополнительная информация
        info2_label = ttk.Label(main_frame, 
            text="Примечание:\n"
                 "• В конце фрагмента запятая (,) заменяется на точку (.)\n"
                 "• В начале фрагмента удаляются недопустимые знаки (.,;:...)\n"
                 "• Первая буква фрагмента делается заглавной\n"
                 "• Кавычки и скобки сохраняются из исходного текста",
            wraplength=580, justify=tk.LEFT, font=('TkDefaultFont', 8, 'italic'))
        info2_label.grid(row=13, column=0, columnspan=2, sticky=tk.W, pady=(5, 10))
        
        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=14, column=0, columnspan=2, pady=15)
        
        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.on_cancel).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Сбросить", command=self.on_reset).pack(side=tk.LEFT, padx=5)
    
    def _create_slider(self, parent, label, key, from_, to, step, row, is_int=False, tooltip=""):
        """Создание ползунка с подписью"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=5)
        
        # Контейнер для слайдера и значения
        slider_frame = ttk.Frame(parent)
        slider_frame.grid(row=row, column=1, sticky=tk.W, padx=5)
        slider_frame.columnconfigure(0, weight=1)
        
        self.value_vars[key] = tk.DoubleVar()
        
        slider = ttk.Scale(slider_frame, from_=from_, to=to, variable=self.value_vars[key],
                           orient=tk.HORIZONTAL, length=200)
        slider.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        value_label = ttk.Label(slider_frame, text="", width=6)
        value_label.grid(row=0, column=1, padx=10)
        
        def update_label(*args):
            val = self.value_vars[key].get()
            if is_int:
                value_label.config(text=f"{int(val)}")
            else:
                value_label.config(text=f"{val:.0f}")
        
        self.value_vars[key].trace_add("write", update_label)
        update_label()
        
        # Тултип
        if tooltip:
            self._add_tooltip(slider, tooltip)
    
    def _add_tooltip(self, widget, text):
        """Добавить всплывающую подсказку"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttk.Label(tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1)
            label.pack()
            widget.tooltip = tooltip
        
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
    
    def load_values(self):
        """Загрузить текущие значения из конфига"""
        self.value_vars["split_min_length"].set(self.config.get("split_min_length", 150))
        self.value_vars["split_max_length"].set(self.config.get("split_max_length", 250))
        self.primary_delimiters_var.set(self.config.get("split_primary_delimiters", ".!?"))
        self.secondary_delimiters_var.set(self.config.get("split_secondary_delimiters", ":;"))
        self.terminator_var.set(self.config.get("split_terminator", "."))
    
    def on_ok(self):
        """Сохранение параметров и закрытие"""
        self.config.set("split_min_length", int(self.value_vars["split_min_length"].get()))
        self.config.set("split_max_length", int(self.value_vars["split_max_length"].get()))
        self.config.set("split_primary_delimiters", self.primary_delimiters_var.get())
        self.config.set("split_secondary_delimiters", self.secondary_delimiters_var.get())
        self.config.set("split_terminator", self.terminator_var.get())
        
        self.dialog.destroy()
    
    def on_cancel(self):
        """Закрытие без сохранения"""
        self.dialog.destroy()
    
    def on_reset(self):
        """Сброс значений по умолчанию"""
        self.value_vars["split_min_length"].set(150)
        self.value_vars["split_max_length"].set(250)
        self.primary_delimiters_var.set(".!?")
        self.secondary_delimiters_var.set(":;")
        self.terminator_var.set(".")