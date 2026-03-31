import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import json
import time
from pathlib import Path
import threading
import sys

# Добавляем путь для импорта модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_manager import ConfigManager
from core.text_extractor import TextExtractor
from core.text_processor import TextProcessor
from core.audio_generator import AudioGenerator
from gui.accent_editor import AccentEditor
from gui.params_dialog import ParamsDialog


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Книги в аудио - Конвертер")
        
        self.config = ConfigManager()
        
        geometry = self.config.get("window_geometry", "1000x750")
        self.root.geometry(geometry)
        
        # Переменные состояния
        self.work_dir = tk.StringVar(value=self.config.get("work_dir", ""))
        self.language = tk.StringVar(value=self.config.get("language", "ru"))
        self.auto_save = tk.BooleanVar(value=self.config.get("auto_save", True))
        
        # Настройки TTS
        self.speaker = tk.StringVar(value=self.config.get("speaker", "Claribel Dervla"))
        self.speed = tk.DoubleVar(value=self.config.get("speed", 1.0))
        self.output_format = tk.StringVar(value=self.config.get("output_format", "mp3"))
        self.speaker_wav = tk.StringVar(value=self.config.get("speaker_wav", ""))
        self.fragment_pause = tk.DoubleVar(value=self.config.get("fragment_pause", 0.2))
        self.initial_pause = tk.DoubleVar(value=self.config.get("initial_pause", 0.0))
        
        # Время запуска программы
        self.program_start_time = time.time()
        
        # Доступные спикеры XTTS
        self.available_speakers = [
            'Claribel Dervla', 'Daisy Studious', 'Gracie Wise', 'Tammie Ema',
            'Alison Dietlinde', 'Ana Florence', 'Annmarie Nele', 'Asya Anara',
            'Brenda Stern', 'Gitta Nikolina', 'Henriette Usha', 'Sofia Hellen',
            'Tammy Grit', 'Tanja Adelina', 'Vjollca Johnnie', 'Andrew Chipper',
            'Badr Odhiambo', 'Dionisio Schuyler', 'Royston Min', 'Viktor Eka',
            'Abrahan Mack', 'Adde Michal', 'Baldur Sanjin', 'Craig Gutsy',
            'Damien Black', 'Gilberto Mathias', 'Ilkin Urbano', 'Kazuhiko Atallah',
            'Ludvig Milivoj', 'Suad Qasim', 'Torcull Diarmuid', 'Viktor Menelaos',
            'Zacharie Aimilios', 'Nova Hogarth', 'Maja Ruoho', 'Uta Obando',
            'Lidiya Szekeres', 'Chandra MacFarland', 'Szofi Granger', 'Camilla Holmström',
            'Lilya Stainthorpe', 'Zofija Kendrick', 'Narelle Moon', 'Barbora MacLean',
            'Alexandra Hisakawa', 'Alma María', 'Rosemary Okafor', 'Ige Behringer',
            'Filip Traverse', 'Damjan Chapman', 'Wulf Carlevaro', 'Aaron Dreschner',
            'Kumar Dahl', 'Eugenio Mataracı', 'Ferran Simen', 'Xavier Hayasaka',
            'Luis Moray', 'Marcos Rudaski'
        ]
        
        self.current_step = self.config.get("last_step", 0)
        
        self.setup_ui()
        self.check_source_folder()
        self.update_step_status()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _format_time(self, seconds):
        """Форматирование времени в читаемый вид"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        if minutes > 0:
            return f"{minutes} минут {secs} секунд"
        return f"{secs} секунд"
    
    def check_source_folder(self):
        """Проверка наличия папки source, создание при необходимости"""
        work_dir = self.work_dir.get()
        if work_dir and os.path.exists(work_dir):
            source_dir = Path(work_dir) / "source"
            if not source_dir.exists():
                source_dir.mkdir(parents=True, exist_ok=True)
                self.log(f"Создана папка для исходных файлов: {source_dir}")
                self.log("Поместите книги (PDF, EPUB, FB2, TXT) в эту папку")
    
    def setup_ui(self):
        """Создание интерфейса"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # === Панель настроек ===
        settings_frame = ttk.LabelFrame(main_frame, text="Настройки", padding="10")
        settings_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        settings_frame.columnconfigure(1, weight=1)
        
        # Рабочая папка
        ttk.Label(settings_frame, text="Рабочая папка:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(settings_frame, textvariable=self.work_dir).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(settings_frame, text="Обзор...", command=self.browse_work_dir).grid(row=0, column=2, padx=5)
        
        ttk.Separator(settings_frame, orient='horizontal').grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # === Настройки озвучки ===
        ttk.Label(settings_frame, text="Настройки озвучки:", font=('TkDefaultFont', 10, 'bold')).grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(5,10))
        
        ttk.Label(settings_frame, text="Голос:").grid(row=3, column=0, sticky=tk.W, padx=5)
        voice_combo = ttk.Combobox(settings_frame, textvariable=self.speaker,
                                   values=self.available_speakers,
                                   state='readonly', width=25)
        voice_combo.grid(row=3, column=1, sticky=tk.W, padx=5)
        ttk.Label(settings_frame, text="Выберите голос из списка").grid(row=3, column=2, sticky=tk.W, padx=5)
        
        ttk.Label(settings_frame, text="Клонирование голоса (WAV):").grid(row=4, column=0, sticky=tk.W, padx=5)
        ttk.Entry(settings_frame, textvariable=self.speaker_wav).grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(settings_frame, text="Обзор...", command=self.browse_speaker_wav).grid(row=4, column=2, padx=5)
        
        ttk.Label(settings_frame, text="Скорость речи:").grid(row=5, column=0, sticky=tk.W, padx=5)
        speed_scale = ttk.Scale(settings_frame, from_=0.5, to=2.0, variable=self.speed, orient='horizontal', length=200)
        speed_scale.grid(row=5, column=1, sticky=tk.W, padx=5)
        self.speed_label = ttk.Label(settings_frame, text=f"{self.speed.get():.1f}x")
        self.speed_label.grid(row=5, column=2, sticky=tk.W, padx=5)
        speed_scale.configure(command=lambda x: self.speed_label.configure(text=f"{self.speed.get():.1f}x"))
        
        ttk.Label(settings_frame, text="Формат:").grid(row=6, column=0, sticky=tk.W, padx=5)
        format_frame = ttk.Frame(settings_frame)
        format_frame.grid(row=6, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(format_frame, text="MP3", variable=self.output_format, value="mp3").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_frame, text="WAV", variable=self.output_format, value="wav").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(settings_frame, text="Пауза между фрагментами:").grid(row=7, column=0, sticky=tk.W, padx=5)
        pause_scale = ttk.Scale(settings_frame, from_=0.0, to=2.0, variable=self.fragment_pause, orient='horizontal', length=200)
        pause_scale.grid(row=7, column=1, sticky=tk.W, padx=5)
        self.pause_label = ttk.Label(settings_frame, text=f"{self.fragment_pause.get():.1f} сек")
        self.pause_label.grid(row=7, column=2, sticky=tk.W, padx=5)
        pause_scale.configure(command=lambda x: self.pause_label.configure(text=f"{self.fragment_pause.get():.1f} сек"))
        
        ttk.Label(settings_frame, text="Пауза в начале:").grid(row=8, column=0, sticky=tk.W, padx=5)
        init_pause_scale = ttk.Scale(settings_frame, from_=0.0, to=2.0, variable=self.initial_pause, orient='horizontal', length=200)
        init_pause_scale.grid(row=8, column=1, sticky=tk.W, padx=5)
        self.init_pause_label = ttk.Label(settings_frame, text=f"{self.initial_pause.get():.1f} сек")
        self.init_pause_label.grid(row=8, column=2, sticky=tk.W, padx=5)
        init_pause_scale.configure(command=lambda x: self.init_pause_label.configure(text=f"{self.initial_pause.get():.1f} сек"))
        
        # Кнопка параметров синтеза
        ttk.Label(settings_frame, text="Параметры синтеза:").grid(row=9, column=0, sticky=tk.W, padx=5)
        ttk.Button(settings_frame, text="⚙ Настройки", command=self.open_synth_params).grid(row=9, column=1, sticky=tk.W, padx=5)
        
        ttk.Separator(settings_frame, orient='horizontal').grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # === Настройки словаря ===
        ttk.Label(settings_frame, text="Словарь исправлений:", font=('TkDefaultFont', 10, 'bold')).grid(row=11, column=0, columnspan=3, sticky=tk.W, pady=(5,10))
        
        dict_frame = ttk.Frame(settings_frame)
        dict_frame.grid(row=12, column=0, columnspan=3, sticky=tk.W, padx=5)
        ttk.Button(dict_frame, text="📝 Открыть словарь", command=self.open_stress_dict).pack(side=tk.LEFT, padx=5)
        ttk.Button(dict_frame, text="📄 Создать пример", command=self.create_example_dict).pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(settings_frame, text="Автосохранение настроек",
                       variable=self.auto_save).grid(row=13, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # === Панель шагов обработки ===
        steps_frame = ttk.LabelFrame(main_frame, text="Этапы обработки", padding="10")
        steps_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        btn_frame = ttk.Frame(steps_frame)
        btn_frame.grid(row=0, column=0, columnspan=2, pady=5)
        
        self.step1_btn = ttk.Button(btn_frame, text="1. Извлечь текст",
                                    command=self.run_step1, width=18)
        self.step1_btn.grid(row=0, column=0, padx=2)
        
        self.step2_btn = ttk.Button(btn_frame, text="2. Обработать текст",
                                    command=self.run_step2, width=18, state='disabled')
        self.step2_btn.grid(row=0, column=1, padx=2)
        
        self.step3_btn = ttk.Button(btn_frame, text="3. Разбить на фрагменты",
                                    command=self.run_step3, width=18, state='disabled')
        self.step3_btn.grid(row=0, column=2, padx=2)
        
        self.step4_btn = ttk.Button(btn_frame, text="4. Создать аудио",
                                    command=self.run_step4, width=18, state='disabled')
        self.step4_btn.grid(row=0, column=3, padx=2)
        
        self.step_all_btn = ttk.Button(btn_frame, text="▶ Выполнить все этапы",
                                       command=self.run_all_steps, width=18)
        self.step_all_btn.grid(row=0, column=4, padx=2)
        
        self.progress = ttk.Progressbar(steps_frame, mode='indeterminate')
        self.progress.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.status_var = tk.StringVar(value="Готов к работе")
        status_label = ttk.Label(steps_frame, textvariable=self.status_var)
        status_label.grid(row=2, column=0, columnspan=2)
        
        # === Лог выполнения ===
        log_frame = ttk.LabelFrame(main_frame, text="Лог выполнения", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Button(log_frame, text="Очистить лог", command=self.clear_log).grid(row=1, column=0, pady=5)
    
    def browse_work_dir(self):
        dirname = filedialog.askdirectory(
            title="Выберите рабочую папку",
            initialdir=self.work_dir.get() or os.path.expanduser("~")
        )
        if dirname:
            self.work_dir.set(dirname)
            self.config.set("work_dir", dirname)
            self.log(f"Рабочая папка: {dirname}")
            self.check_source_folder()
    
    def browse_speaker_wav(self):
        filename = filedialog.askopenfilename(
            title="Выберите WAV файл с голосом для клонирования",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
            initialdir=self.work_dir.get() or os.path.expanduser("~")
        )
        if filename:
            self.speaker_wav.set(filename)
            self.config.set("speaker_wav", filename)
            self.log(f"Файл для клонирования: {filename}")
    
    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
    
    def update_step_status(self):
        work_dir = self.work_dir.get()
        if not work_dir or not os.path.exists(work_dir):
            return
        
        extracted_dir = Path(work_dir) / "01_extracted_text"
        replaced_dir = Path(work_dir) / "02_replaced_text"
        fragments_dir = Path(work_dir) / "03_text_fragments"
        
        self.step1_btn.config(state='normal')
        
        if extracted_dir.exists() and list(extracted_dir.glob("*.txt")):
            self.step2_btn.config(state='normal')
        else:
            self.step2_btn.config(state='disabled')
        
        if replaced_dir.exists() and list(replaced_dir.glob("*.txt")):
            self.step3_btn.config(state='normal')
        else:
            self.step3_btn.config(state='disabled')
        
        if fragments_dir.exists() and list(fragments_dir.glob("*/*.txt")):
            self.step4_btn.config(state='normal')
        else:
            self.step4_btn.config(state='disabled')
    
    def open_stress_dict(self):
        work_dir = self.work_dir.get()
        if not work_dir:
            messagebox.showerror("Ошибка", "Сначала выберите рабочую папку!")
            return
        
        dict_file = Path(work_dir) / "config" / "stress_dict.json"
        
        try:
            import sys
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            editor = AccentEditor(str(dict_file))
            editor.show()
            app.exec_()
        except Exception as e:
            self.log(f"Ошибка запуска редактора: {e}")
            messagebox.showerror("Ошибка", f"Не удалось запустить редактор:\n{e}")
    
    def create_example_dict(self):
        work_dir = self.work_dir.get()
        if not work_dir:
            messagebox.showerror("Ошибка", "Сначала выберите рабочую папку!")
            return
        
        dict_file = Path(work_dir) / "config" / "stress_dict.json"
        
        if dict_file.exists():
            reply = messagebox.askyesno(
                "Подтверждение",
                f"Файл {dict_file.name} уже существует.\nПерезаписать его примером?"
            )
            if not reply:
                return
        
        example = {
            "препод+обный": "преподо+бный",
            "+авва": "а+вва",
            "Господ+а": "Г+оспода"
        }
        
        try:
            dict_file.parent.mkdir(parents=True, exist_ok=True)
            with open(dict_file, 'w', encoding='utf-8') as f:
                json.dump(example, f, ensure_ascii=False, indent=2)
            self.log(f"Создан пример словаря: {dict_file}")
            messagebox.showinfo("Успех", f"Создан пример словаря:\n{dict_file}")
        except Exception as e:
            self.log(f"Ошибка создания словаря: {e}")
            messagebox.showerror("Ошибка", f"Не удалось создать словарь: {e}")
    
    def open_synth_params(self):
        """Открыть окно настроек параметров синтеза"""
        if not self.work_dir.get():
            messagebox.showerror("Ошибка", "Сначала выберите рабочую папку!")
            return
        
        ParamsDialog(self.root, self.config)
    
    def run_step1(self):
        if not self.work_dir.get():
            messagebox.showerror("Ошибка", "Выберите рабочую папку!")
            return
        
        def task():
            try:
                self.status_var.set("Извлечение текста...")
                self.progress.start()
                
                extractor = TextExtractor(self.work_dir.get())
                results = extractor.extract_all()
                
                self.log(f"Обработано файлов: {len(results)}")
                self.update_step_status()
                self.status_var.set("Готов")
                
            except Exception as e:
                self.log(f"ОШИБКА: {e}")
                self.status_var.set("Ошибка")
            finally:
                self.progress.stop()
        
        threading.Thread(target=task, daemon=True).start()
    
    def run_step2(self):
        if not self.work_dir.get():
            messagebox.showerror("Ошибка", "Выберите рабочую папку!")
            return
        
        def task():
            try:
                self.status_var.set("Обработка текста...")
                self.progress.start()
                
                processor = TextProcessor(self.work_dir.get())
                results = processor.process_all()
                
                self.log(f"Обработано файлов: {len(results)}")
                self.update_step_status()
                self.status_var.set("Готов")
                
            except Exception as e:
                self.log(f"ОШИБКА: {e}")
                self.status_var.set("Ошибка")
            finally:
                self.progress.stop()
        
        threading.Thread(target=task, daemon=True).start()
    
    def run_step3(self):
        if not self.work_dir.get():
            messagebox.showerror("Ошибка", "Выберите рабочую папку!")
            return
        
        def task():
            try:
                self.status_var.set("Разбиение на фрагменты...")
                self.progress.start()
                
                processor = TextProcessor(self.work_dir.get())
                results = processor.split_all()
                
                total = sum(len(f) for f in results.values())
                self.log(f"Разбито файлов: {len(results)}, фрагментов: {total}")
                self.update_step_status()
                self.status_var.set("Готов")
                
            except Exception as e:
                self.log(f"ОШИБКА: {e}")
                self.status_var.set("Ошибка")
            finally:
                self.progress.stop()
        
        threading.Thread(target=task, daemon=True).start()
    
    def _progress_callback(self, current, total, elapsed_str):
        """Callback для обновления прогресса генерации"""
        self.log(f"создано {current} файлов из {total}. прошло времени с начала работы: {elapsed_str}")
    
    def run_step4(self):
        """Запуск генерации аудио с субтитрами"""
        if not self.work_dir.get():
            messagebox.showerror("Ошибка", "Выберите рабочую папку!")
            return
        
        self.config.set("speaker", self.speaker.get())
        self.config.set("speed", self.speed.get())
        self.config.set("output_format", self.output_format.get())
        self.config.set("speaker_wav", self.speaker_wav.get())
        self.config.set("fragment_pause", self.fragment_pause.get())
        self.config.set("initial_pause", self.initial_pause.get())
        
        def task():
            try:
                self.status_var.set("Генерация аудио...")
                self.progress.start()
                
                self.log(f"Загрузка XTTS модели...")
                self.log(f"  Голос: {self.speaker.get() if not self.speaker_wav.get() else 'Клонирование: ' + self.speaker_wav.get()}")
                self.log(f"  Скорость: {self.speed.get():.1f}x")
                self.log(f"  Пауза между фрагментами: {self.fragment_pause.get():.1f} сек")
                self.log(f"  Пауза в начале: {self.initial_pause.get():.1f} сек")
                self.log(f"  Формат: {self.output_format.get().upper()}")
                self.log(f"  Субтитры: включены")
                
                # Выводим параметры синтеза
                self.log(f"  Параметры синтеза:")
                self.log(f"    temperature: {self.config.get('temperature', 0.85)}")
                self.log(f"    repetition_penalty: {self.config.get('repetition_penalty', 2.0)}")
                self.log(f"    length_penalty: {self.config.get('length_penalty', 1.0)}")
                self.log(f"    top_k: {self.config.get('top_k', 50)}")
                self.log(f"    top_p: {self.config.get('top_p', 0.85)}")
                self.log(f"    gpt_cond_len: {self.config.get('gpt_cond_len', 12)} сек")
                self.log(f"    sound_norm_refs: {self.config.get('sound_norm_refs', True)}")
                
                generator = AudioGenerator(
                    self.work_dir.get(),
                    speaker=self.speaker.get(),
                    speed=self.speed.get(),
                    output_format=self.output_format.get(),
                    speaker_wav=self.speaker_wav.get() or None,
                    fragment_pause=self.fragment_pause.get(),
                    initial_pause=self.initial_pause.get(),
                    progress_callback=self._progress_callback,
                    start_time=self.program_start_time,
                    generate_subtitles=True,
                    temperature=self.config.get("temperature", 0.85),
                    repetition_penalty=self.config.get("repetition_penalty", 2.0),
                    length_penalty=self.config.get("length_penalty", 1.0),
                    top_k=self.config.get("top_k", 50),
                    top_p=self.config.get("top_p", 0.85),
                    gpt_cond_len=self.config.get("gpt_cond_len", 12),
                    sound_norm_refs=self.config.get("sound_norm_refs", True)
                )
                
                audio_files, subtitle_files = generator.generate_all()
                
                self.log(f"Сгенерировано аудиофайлов: {len(audio_files)}")
                self.log(f"Создано файлов субтитров: {len(subtitle_files)}")
                self.update_step_status()
                self.status_var.set("Готов")
                
            except Exception as e:
                self.log(f"ОШИБКА: {e}")
                self.status_var.set("Ошибка")
            finally:
                self.progress.stop()
        
        threading.Thread(target=task, daemon=True).start()
    
    def run_all_steps(self):
        """Выполнить все этапы последовательно"""
        if not self.work_dir.get():
            messagebox.showerror("Ошибка", "Выберите рабочую папку!")
            return
        
        def task():
            try:
                self.status_var.set("Выполнение всех этапов...")
                self.progress.start()
                self.log("=" * 50)
                self.log("ЗАПУСК ВСЕХ ЭТАПОВ")
                self.log("=" * 50)
                
                # Этап 1
                self.log("\n--- ЭТАП 1: Извлечение текста ---")
                extractor = TextExtractor(self.work_dir.get())
                extracted = extractor.extract_all()
                self.log(f"Обработано файлов: {len(extracted)}")
                
                if not extracted:
                    self.log("Нет файлов для обработки!")
                    return
                
                # Этап 2
                self.log("\n--- ЭТАП 2: Обработка текста ---")
                processor = TextProcessor(self.work_dir.get())
                processed = processor.process_all()
                self.log(f"Обработано файлов: {len(processed)}")
                
                # Этап 3
                self.log("\n--- ЭТАП 3: Разбиение на фрагменты ---")
                fragments = processor.split_all()
                total = sum(len(f) for f in fragments.values())
                self.log(f"Разбито файлов: {len(fragments)}, фрагментов: {total}")
                
                # Этап 4
                self.log("\n--- ЭТАП 4: Генерация аудио и субтитров ---")
                self.log(f"  Параметры синтеза:")
                self.log(f"    temperature: {self.config.get('temperature', 0.85)}")
                self.log(f"    repetition_penalty: {self.config.get('repetition_penalty', 2.0)}")
                self.log(f"    length_penalty: {self.config.get('length_penalty', 1.0)}")
                self.log(f"    top_k: {self.config.get('top_k', 50)}")
                self.log(f"    top_p: {self.config.get('top_p', 0.85)}")
                self.log(f"    gpt_cond_len: {self.config.get('gpt_cond_len', 12)} сек")
                self.log(f"    sound_norm_refs: {self.config.get('sound_norm_refs', True)}")
                
                generator = AudioGenerator(
                    self.work_dir.get(),
                    speaker=self.speaker.get(),
                    speed=self.speed.get(),
                    output_format=self.output_format.get(),
                    speaker_wav=self.speaker_wav.get() or None,
                    fragment_pause=self.fragment_pause.get(),
                    initial_pause=self.initial_pause.get(),
                    progress_callback=self._progress_callback,
                    start_time=self.program_start_time,
                    generate_subtitles=True,
                    temperature=self.config.get("temperature", 0.85),
                    repetition_penalty=self.config.get("repetition_penalty", 2.0),
                    length_penalty=self.config.get("length_penalty", 1.0),
                    top_k=self.config.get("top_k", 50),
                    top_p=self.config.get("top_p", 0.85),
                    gpt_cond_len=self.config.get("gpt_cond_len", 12),
                    sound_norm_refs=self.config.get("sound_norm_refs", True)
                )
                audio_files, subtitle_files = generator.generate_all()
                self.log(f"Сгенерировано аудиофайлов: {len(audio_files)}")
                self.log(f"Создано файлов субтитров: {len(subtitle_files)}")
                
                elapsed = time.time() - self.program_start_time
                elapsed_str = self._format_time(elapsed)
                self.log(f"\nВСЕГО ВЫПОЛНЕНО ЗА: {elapsed_str}")
                self.log("=" * 50)
                self.log("ВСЕ ЭТАПЫ ВЫПОЛНЕНЫ УСПЕШНО!")
                self.log("=" * 50)
                
                self.update_step_status()
                self.status_var.set("Готов")
                messagebox.showinfo("Готово", 
                    f"Все этапы выполнены!\n"
                    f"Аудиофайлов: {len(audio_files)}\n"
                    f"Файлов субтитров: {len(subtitle_files)}\n"
                    f"Общее время: {elapsed_str}")
                
            except Exception as e:
                self.log(f"ОШИБКА: {e}")
                self.status_var.set("Ошибка")
                messagebox.showerror("Ошибка", f"Ошибка при выполнении:\n{e}")
            finally:
                self.progress.stop()
        
        threading.Thread(target=task, daemon=True).start()
    
    def on_closing(self):
        geometry = self.root.geometry()
        self.config.set("window_geometry", geometry)
        self.config.set("last_step", self.current_step)
        self.config.set("language", self.language.get())
        self.config.set("auto_save", self.auto_save.get())
        self.config.set("speaker", self.speaker.get())
        self.config.set("speed", self.speed.get())
        self.config.set("output_format", self.output_format.get())
        self.config.set("speaker_wav", self.speaker_wav.get())
        self.config.set("fragment_pause", self.fragment_pause.get())
        self.config.set("initial_pause", self.initial_pause.get())
        
        self.config.save()
        self.root.destroy()