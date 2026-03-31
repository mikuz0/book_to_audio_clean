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
    
    def split_text(self, text):
        """Разбить текст на фрагменты по маркерам . : ;"""
        temp_text = text.replace(':', '.').replace(';', '.')
        raw_fragments = temp_text.split('.')
        
        fragments = []
        for frag in raw_fragments:
            frag = frag.strip()
            if len(frag) < 10:
                continue
            
            if frag and frag[0].islower():
                frag = frag[0].upper() + frag[1:]
            
            if not frag.endswith('.'):
                frag = frag + '.'
            
            fragments.append(frag)
        
        return fragments
    
    def split_file(self, input_file):
        """Разбить файл на фрагменты"""
        input_file = Path(input_file)
        
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text.strip():
            return []
        
        fragments = self.split_text(text)
        
        output_dir = self.fragments_dir / input_file.stem
        output_dir.mkdir(exist_ok=True)
        
        saved_files = []
        for i, frag in enumerate(fragments, 1):
            frag_file = output_dir / f"fragment_{i:03d}.txt"
            with open(frag_file, 'w', encoding='utf-8') as f:
                f.write(frag)
            saved_files.append(frag_file)
        
        return saved_files
    
    def split_all(self):
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
                fragments = self.split_file(f)
                results[f.name] = fragments
                print(f"  Разбито на {len(fragments)} фрагментов")
            except Exception as e:
                print(f"  ОШИБКА: {e}")
        
        return results