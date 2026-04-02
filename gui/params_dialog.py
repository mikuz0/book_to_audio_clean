import tkinter as tk
from tkinter import ttk

class ParamsDialog:
    """Диалоговое окно для настройки параметров синтеза XTTS"""
    
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Параметры синтеза XTTS")
        self.dialog.geometry("700x650")
        self.dialog.minsize(600, 550)
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
            text="Настройка параметров синтеза речи.\n"
                 "Увеличение repetition_penalty помогает бороться с хвостами и повторами.\n"
                 "num_beams - количество лучей поиска (1 = быстро, больше = качественнее, но медленнее).",
            wraplength=650, justify=tk.LEFT)
        info_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Температура
        self._create_slider(main_frame, "Температура (temperature):", 
                            "temperature", 0.1, 1.5, 0.05, 2, is_int=False,
                            tooltip="Чем выше, тем креативнее, но больше артефактов")
        
        # Штраф за повторы
        self._create_slider(main_frame, "Штраф за повторы (repetition_penalty):", 
                            "repetition_penalty", 1.0, 5.0, 0.1, 3, is_int=False,
                            tooltip="Увеличивайте для борьбы с повторами и хвостами")
        
        # Штраф за длину
        self._create_slider(main_frame, "Штраф за длину (length_penalty):", 
                            "length_penalty", 0.5, 2.0, 0.05, 4, is_int=False,
                            tooltip="Положительные значения укорачивают фразы")
        
        # Top K (новый диапазон от 1)
        self._create_slider(main_frame, "Top K:", 
                            "top_k", 1, 100, 1, 5, is_int=True,
                            tooltip="Меньше = предсказуемее. Минимум 1.")
        
        # Top P (новый диапазон от 0.01)
        self._create_slider(main_frame, "Top P:", 
                            "top_p", 0.01, 1.0, 0.01, 6, is_int=False,
                            tooltip="Меньше = предсказуемее. Минимум 0.01.")
        
        # Num Beams (новый параметр)
        self._create_slider(main_frame, "Num Beams (количество лучей):", 
                            "num_beams", 1, 20, 1, 7, is_int=True,
                            tooltip="Количество путей поиска. 1 = быстро, больше = качественнее, но медленнее.")
        
        # GPT cond len
        self._create_slider(main_frame, "GPT cond len (сек):", 
                            "gpt_cond_len", 3, 30, 1, 8, is_int=True,
                            tooltip="Длина образца для клонирования голоса")
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Чекбокс для sound_norm_refs
        ttk.Label(main_frame, text="Sound norm refs:").grid(row=10, column=0, sticky=tk.W, pady=10)
        self.sound_norm_var = tk.BooleanVar()
        self.sound_norm_check = ttk.Checkbutton(main_frame, text="Авто-нормализация образца", 
                                                 variable=self.sound_norm_var)
        self.sound_norm_check.grid(row=10, column=1, sticky=tk.W, pady=10)
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').grid(row=11, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=12, column=0, columnspan=2, pady=15)
        
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
                           orient=tk.HORIZONTAL, length=250)
        slider.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        value_label = ttk.Label(slider_frame, text="", width=8)
        value_label.grid(row=0, column=1, padx=10)
        
        def update_label(*args):
            val = self.value_vars[key].get()
            if is_int:
                value_label.config(text=f"{int(val)}")
            else:
                value_label.config(text=f"{val:.2f}")
        
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
        self.value_vars["temperature"].set(self.config.get("temperature", 0.85))
        self.value_vars["repetition_penalty"].set(self.config.get("repetition_penalty", 2.0))
        self.value_vars["length_penalty"].set(self.config.get("length_penalty", 1.0))
        self.value_vars["top_k"].set(self.config.get("top_k", 50))
        self.value_vars["top_p"].set(self.config.get("top_p", 0.85))
        self.value_vars["num_beams"].set(self.config.get("num_beams", 1))
        self.value_vars["gpt_cond_len"].set(self.config.get("gpt_cond_len", 12))
        self.sound_norm_var.set(self.config.get("sound_norm_refs", True))
    
    def on_ok(self):
        """Сохранение параметров и закрытие"""
        self.config.set("temperature", self.value_vars["temperature"].get())
        self.config.set("repetition_penalty", self.value_vars["repetition_penalty"].get())
        self.config.set("length_penalty", self.value_vars["length_penalty"].get())
        self.config.set("top_k", int(self.value_vars["top_k"].get()))
        self.config.set("top_p", self.value_vars["top_p"].get())
        self.config.set("num_beams", int(self.value_vars["num_beams"].get()))
        self.config.set("gpt_cond_len", int(self.value_vars["gpt_cond_len"].get()))
        self.config.set("sound_norm_refs", self.sound_norm_var.get())
        
        self.dialog.destroy()
    
    def on_cancel(self):
        """Закрытие без сохранения"""
        self.dialog.destroy()
    
    def on_reset(self):
        """Сброс значений по умолчанию"""
        defaults = {
            "temperature": 0.85,
            "repetition_penalty": 2.0,
            "length_penalty": 1.0,
            "top_k": 50,
            "top_p": 0.85,
            "num_beams": 1,
            "gpt_cond_len": 12,
            "sound_norm_refs": True
        }
        
        self.value_vars["temperature"].set(defaults["temperature"])
        self.value_vars["repetition_penalty"].set(defaults["repetition_penalty"])
        self.value_vars["length_penalty"].set(defaults["length_penalty"])
        self.value_vars["top_k"].set(defaults["top_k"])
        self.value_vars["top_p"].set(defaults["top_p"])
        self.value_vars["num_beams"].set(defaults["num_beams"])
        self.value_vars["gpt_cond_len"].set(defaults["gpt_cond_len"])
        self.sound_norm_var.set(defaults["sound_norm_refs"])