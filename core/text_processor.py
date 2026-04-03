import re
from pathlib import Path
from core.stress_dict import StressDictionary

class TextProcessor:
    """Обработка текста: исправление ударений и разбиение на фрагменты"""
    
    def __init__(self, work_dir):
        self.work_dir = Path(work_dir)
        self.extracted_dir = self.work_dir / "01_extracted_text"
        self.replaced_dir = self.work_dir / "02_replaced_text"
        self.fragments_dir = self.work_dir / "03_text_fragments"
        
        self.replaced_dir.mkdir(exist_ok=True)
        self.fragments_dir.mkdir(exist_ok=True)
        
        self.stress_dict = StressDictionary(work_dir)
    
    def apply_replacements(self, text):
        """Применить исправления из словаря"""
        return self.stress_dict.apply(text)
    
    def convert_to_unicode(self, text):
        """Преобразовать + в Unicode ударения"""
        STRESS_MAP = {
            'а': 'а́', 'А': 'А́', 'е': 'е́', 'Е': 'Е́', 'ё': 'ё́', 'Ё': 'Ё́',
            'и': 'и́', 'И': 'И́', 'о': 'о́', 'О': 'О́', 'у': 'у́', 'У': 'У́',
            'ы': 'ы́', 'Ы': 'Ы́', 'э': 'э́', 'Э': 'Э́', 'ю': 'ю́', 'Ю': 'Ю́', 'я': 'я́', 'Я': 'Я́'
        }
        
        result = text
        
        # + перед гласной
        result = re.sub(r'\+([аеёиоуыэюя])',
                        lambda m: STRESS_MAP.get(m.group(1).lower(), m.group(1)),
                        result, flags=re.I)
        
        # гласная + гласная
        result = re.sub(r'([аеёиоуыэюя])\+([аеёиоуыэюя])',
                        lambda m: m.group(1) + STRESS_MAP.get(m.group(2).lower(), m.group(2)),
                        result, flags=re.I)
        
        # гласная + в конце
        result = re.sub(r'([аеёиоуыэюя])\+',
                        lambda m: STRESS_MAP.get(m.group(1).lower(), m.group(1)),
                        result, flags=re.I)
        
        result = result.replace('+', '')
        return result
    
    def normalize_spaces(self, text):
        """Нормализация пробелов в тексте"""
        if not text:
            return text
        
        # Удаляем двойные и более пробелы
        text = re.sub(r' +', ' ', text)
        
        # Убираем пробелы перед знаками препинания
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        # Добавляем пробел после знаков препинания (если нет)
        text = re.sub(r'([.,!?;:])([^\s])', r'\1 \2', text)
        
        # Убираем пробел перед точкой в конце
        text = re.sub(r'\s+\.', '.', text)
        
        # Убираем пробел перед запятой
        text = re.sub(r'\s+,', ',', text)
        
        # Удаляем двойные и более точки
        text = re.sub(r'\.{2,}', '.', text)
        
        # После точки должен быть пробел и заглавная буква
        text = re.sub(r'\.\s*([а-яё])', lambda m: '. ' + m.group(1).upper(), text, flags=re.I)
        
        return text.strip()
    
    def find_original_segment(self, fragment, original_text):
        """
        Находит фрагмент в исходном тексте и возвращает оригинальный отрезок.
        Возвращает (найденный_отрезок, начало_позиция, конец_позиция) или (None, -1, -1)
        """
        if not fragment or not original_text:
            return None, -1, -1
        
        # Очищаем фрагмент для поиска
        search_fragment = fragment.strip()
        search_fragment = re.sub(r'\s+', ' ', search_fragment)
        
        # Ищем точное вхождение
        pos = original_text.find(search_fragment)
        if pos != -1:
            end_pos = pos + len(search_fragment)
            return original_text[pos:end_pos], pos, end_pos
        
        # Пробуем искать по началу и концу
        start_part = search_fragment[:50] if len(search_fragment) > 50 else search_fragment
        end_part = search_fragment[-50:] if len(search_fragment) > 50 else search_fragment
        
        start_pos = original_text.find(start_part)
        if start_pos == -1:
            return None, -1, -1
        
        end_pos = original_text.rfind(end_part)
        if end_pos == -1:
            return None, -1, -1
        
        end_pos = end_pos + len(end_part)
        if end_pos > start_pos:
            return original_text[start_pos:end_pos], start_pos, end_pos
        
        return None, -1, -1
    
    def fix_fragment_end(self, text, terminator="."):
        """
        Корректировка конца фрагмента.
        terminator - символ завершения (может быть пустой строкой, пробелом, точкой и т.д.)
        """
        if not text:
            return text
        
        text = text.rstrip()
        if not text:
            return text
        
        last_char = text[-1]
        
        # Заменяем ; : , на точку в конце (всегда)
        if last_char in ';:,':
            text = text[:-1] + '.'
            last_char = '.'
        
        # Если terminator пустой - ничего не добавляем
        if terminator == "":
            return text
        
        # Если terminator - пробел
        if terminator == " ":
            if last_char not in '.!?':
                text = text + ' '
            return text
        
        # Если terminator - точка, восклицательный знак, вопросительный знак или другое
        # Проверяем, заканчивается ли уже на terminator
        if text.endswith(terminator):
            return text
        
        # Проверяем, заканчивается ли на допустимый знак (.!?) и terminator не точка
        if terminator != '.' and last_char in '.!?':
            # Заменяем существующий знак на terminator
            text = text[:-1] + terminator
        else:
            # Добавляем terminator в конец
            text = text + terminator
        
        return text
    
    def fix_fragment_start(self, text):
        """Корректировка начала фрагмента"""
        if not text:
            return text
        
        # Удаляем недопустимые символы в начале
        while text and text[0] in ' .,;:':
            text = text[1:]
        
        # Удаляем многоточие в начале
        if text.startswith('...'):
            text = text[3:].lstrip()
        elif text.startswith('..'):
            text = text[2:].lstrip()
        
        # Делаем первую букву заглавной
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        return text
    
    def restore_fragment(self, fragment, original_text, terminator="."):
        """
        Восстанавливает фрагмент по исходному тексту:
        - Находит отрезок в исходном тексте
        - Корректирует конец
        - Корректирует начало
        - Нормализует пробелы
        """
        if not fragment:
            return ""
        
        # Находим оригинальный отрезок
        original_segment, start_pos, end_pos = self.find_original_segment(fragment, original_text)
        
        if original_segment:
            result = original_segment
        else:
            # Если не нашли, используем фрагмент как есть
            result = fragment
        
        # Корректировка конца
        result = self.fix_fragment_end(result, terminator)
        
        # Корректировка начала
        result = self.fix_fragment_start(result)
        
        # Нормализация пробелов
        result = self.normalize_spaces(result)
        
        return result
    
    def merge_short_fragments(self, fragments, min_length):
        """
        Объединяет короткие фрагменты с соседними.
        Возвращает новый список фрагментов.
        """
        if not fragments:
            return []
        
        merged = []
        buffer = ""
        
        for frag in fragments:
            if buffer:
                buffer += " " + frag
            else:
                buffer = frag
            
            if len(buffer) >= min_length:
                merged.append(buffer.strip())
                buffer = ""
        
        # Обработка остатка
        if buffer:
            if merged and len(buffer) < min_length:
                merged[-1] = merged[-1] + " " + buffer
            else:
                merged.append(buffer.strip())
        
        return merged
    
    def split_by_delimiters(self, text, delimiters):
        """
        Разбивает текст по указанным разделителям, сохраняя разделители в конце.
        Возвращает список фрагментов.
        """
        parts = []
        current = ""
        
        for ch in text:
            current += ch
            if ch in delimiters:
                if current.strip():
                    parts.append(current.strip())
                current = ""
        
        if current.strip():
            parts.append(current.strip())
        
        return parts
    
    def process_file(self, input_file):
        """Обработать файл: применить замены и конвертировать в Unicode"""
        input_file = Path(input_file)
        
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text.strip():
            return None
        
        text = self.apply_replacements(text)
        text = self.convert_to_unicode(text)
        
        output_file = self.replaced_dir / f"{input_file.stem}_replaced.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        return output_file
    
    def process_all(self):
        """Обработать все извлечённые файлы"""
        if not self.extracted_dir.exists():
            print(f"Папка {self.extracted_dir} не найдена")
            return []
        
        files = list(self.extracted_dir.glob("*.txt"))
        print(f"Найдено файлов: {len(files)}")
        
        results = []
        for f in files:
            print(f"\n--- {f.name} ---")
            try:
                result = self.process_file(f)
                if result:
                    results.append(result)
                    print(f"  Сохранено: {result.name}")
            except Exception as e:
                print(f"  ОШИБКА: {e}")
        
        return results
    
    def split_text(self, text, original_text, min_length=150, max_length=250, 
                   primary_delimiters=".!?", secondary_delimiters=":;", terminator="."):
        """
        Разбить текст на фрагменты с восстановлением по исходному тексту.
        
        Алгоритм:
        1. Разбиение по главным разделителям
        2. Объединение коротких фрагментов (первый проход)
        3. Разбиение длинных фрагментов по второстепенным разделителям
        4. Объединение коротких фрагментов (второй проход)
        5. Восстановление по оригиналу с добавлением terminator
        6. Нормализация
        """
        # Шаг 1: Разбиение по главным разделителям
        parts = self.split_by_delimiters(text, primary_delimiters)
        
        # Шаг 2: Объединение коротких фрагментов (первый проход)
        merged = self.merge_short_fragments(parts, min_length)
        
        # Шаг 3: Разбиение длинных фрагментов по второстепенным разделителям
        final_parts = []
        for part in merged:
            if len(part) <= max_length:
                final_parts.append(part)
            else:
                # Разбиваем длинный фрагмент
                sub_parts = self.split_by_delimiters(part, secondary_delimiters)
                
                if len(sub_parts) == 1:
                    # Если не удалось разбить - принудительное разбиение по длине
                    for i in range(0, len(part), max_length):
                        chunk = part[i:i+max_length]
                        if chunk:
                            final_parts.append(chunk.strip())
                else:
                    final_parts.extend(sub_parts)
        
        # Шаг 4: Объединение коротких фрагментов (второй проход)
        merged_again = self.merge_short_fragments(final_parts, min_length)
        
        # Шаг 5: Восстановление по исходному тексту с добавлением terminator
        restored_parts = []
        for part in merged_again:
            restored = self.restore_fragment(part, original_text, terminator)
            if restored:
                restored_parts.append(restored)
        
        return restored_parts
    
    def split_file(self, input_file, original_text, min_length=150, max_length=250,
                   primary_delimiters=".!?", secondary_delimiters=":;", terminator="."):
        """Разбить файл на фрагменты с заданными параметрами"""
        input_file = Path(input_file)
        
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text.strip():
            return []
        
        fragments = self.split_text(text, original_text, min_length, max_length, 
                                     primary_delimiters, secondary_delimiters, terminator)
        
        output_dir = self.fragments_dir / input_file.stem
        output_dir.mkdir(exist_ok=True)
        
        saved_files = []
        for i, frag in enumerate(fragments, 1):
            frag_file = output_dir / f"fragment_{i:03d}.txt"
            with open(frag_file, 'w', encoding='utf-8') as f:
                f.write(frag)
            saved_files.append(frag_file)
        
        return saved_files
    
    def split_all(self, min_length=150, max_length=250,
                  primary_delimiters=".!?", secondary_delimiters=":;", terminator="."):
        """Разбить все обработанные файлы на фрагменты"""
        if not self.replaced_dir.exists():
            print(f"Папка {self.replaced_dir} не найдена")
            return {}
        
        files = list(self.replaced_dir.glob("*_replaced.txt"))
        print(f"Найдено файлов: {len(files)}")
        
        results = {}
        for f in files:
            print(f"\n--- {f.name} ---")
            try:
                # Загружаем оригинальный текст из extracted_dir для этого файла
                extracted_file = self.extracted_dir / f.name.replace('_replaced', '_extracted')
                if extracted_file.exists():
                    with open(extracted_file, 'r', encoding='utf-8') as ef:
                        original_text = ef.read()
                else:
                    original_text = None
                    print(f"  Предупреждение: не найден оригинальный файл {extracted_file}")
                
                fragments = self.split_file(f, original_text, min_length, max_length,
                                           primary_delimiters, secondary_delimiters, terminator)
                results[f.name] = fragments
                print(f"  Разбито на {len(fragments)} фрагментов")
                if fragments:
                    lengths = [len(frag) for frag in fragments]
                    print(f"  Длина: мин={min(lengths)}, макс={max(lengths)}, средн={sum(lengths)//len(lengths)}")
            except Exception as e:
                print(f"  ОШИБКА: {e}")
        
        return results