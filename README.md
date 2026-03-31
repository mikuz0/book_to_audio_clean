markdown

# Книги в аудио — Конвертер текста в речь с XTTS

Программа для автоматического преобразования книг (PDF, EPUB, FB2, TXT) в аудиофайлы с субтитрами. Использует нейросеть **XTTS-v2** для высококачественного синтеза речи с возможностью клонирования голоса.

## ✨ Возможности

- **Извлечение текста** из PDF, EPUB, FB2, TXT
- **Коррекция ударений** с помощью словаря замен
- **Разбиение на фрагменты** по предложениям для стабильной генерации
- **Синтез речи** через XTTS-v2:
  - Выбор из 58+ встроенных голосов
  - Клонирование голоса по WAV-образцу (5-15 секунд)
  - Регулировка скорости речи
  - Настройка параметров синтеза (температура, штраф за повторы, top_k, top_p и др.)
- **Субтитры** в формате SRT (синхронизированы с аудио)
- **Паузы** между фрагментами и в начале файла
- **Графический интерфейс** на tkinter + PyQt5 для редактирования словаря
- **Сохранение настроек** между сессиями
- **Пакетная обработка** нескольких книг

## 📁 Структура рабочей папки

рабочая_папка/
├── source/ # исходные книги
├── config/ # конфигурация
│ └── stress_dict.json # словарь ударений
├── 01_extracted_text/ # извлечённый текст
├── 02_replaced_text/ # текст после замен
├── 03_text_fragments/ # фрагменты для генерации
├── 04_audio/ # готовые аудиофайлы
└── 05_subtitles/ # субтитры (SRT)
text


## 🚀 Установка

### Системные требования

- **Python 3.11** (собирается локально)
- **ОЗУ:** 8 ГБ (рекомендуется 16 ГБ)
- **Диск:** 10–15 ГБ свободного места
- **ОС:** Linux (Ubuntu 20.04+, Debian 11+)

### Автоматическая установка

```bash
# 1. Создайте чистую папку
mkdir ~/book_to_audio
cd ~/book_to_audio

# 2. Скачайте скрипт установки
wget https://raw.githubusercontent.com/your-repo/install.sh
chmod +x install.sh

# 3. Запустите установку (10–20 минут)
./install.sh

Скрипт выполнит:

    Проверку системных зависимостей

    Скачивание и сборку Python 3.11.9

    Создание виртуального окружения

    Установку PyTorch (CPU-версия)

    Установку всех зависимостей

Ручная установка
bash

# 1. Установите системные зависимости
sudo apt update
sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev libncurses-dev libgdbm-dev \
    libdb5.3-dev libexpat1-dev liblzma-dev tk-dev libffi-dev \
    wget curl git ffmpeg

# 2. Скачайте и соберите Python 3.11.9
cd ~/src
wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
tar -xzf Python-3.11.9.tgz
cd Python-3.11.9
./configure --enable-optimizations
make -j$(nproc)

# 3. Создайте виртуальное окружение
cd ~/book_to_audio
~/src/Python-3.11.9/python -m venv xtts_env
source xtts_env/bin/activate

# 4. Установите зависимости
pip install --upgrade pip
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install TTS PyPDF2 ebooklib beautifulsoup4 lxml scipy numpy PyQt5
pip install transformers==4.38.0

# 5. Скачайте модель XTTS (при первом запуске)
python -c "from TTS.api import TTS; tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=False)"

▶️ Запуск
bash

# Активация окружения
cd ~/book_to_audio
source activate_env.sh   # или ./run.sh

# Запуск программы
python main.py

🖥️ Использование

    Выберите рабочую папку (кнопка "Обзор")

    Поместите книги в папку source внутри рабочей папки

    Настройте параметры:

        Голос: выберите из списка или укажите WAV-файл для клонирования

        Скорость речи (0.5–2.0)

        Паузы между фрагментами и в начале

        Параметры синтеза (кнопка "⚙ Настройки")

    Запустите этапы:

        По отдельности: "1. Извлечь текст" → "2. Обработать текст" → "3. Разбить на фрагменты" → "4. Создать аудио"

        Все сразу: "▶ Выполнить все этапы"

🎛️ Параметры синтеза
Параметр	Диапазон	По умолчанию	Описание
temperature	0.1–1.5	0.85	Креативность модели. Меньше = предсказуемее
repetition_penalty	1.0–5.0	2.0	Штраф за повторы. Увеличивайте для борьбы с хвостами
length_penalty	0.5–2.0	1.0	Положительные значения укорачивают фразы
top_k	10–100	50	Ограничение выбора токенов. Меньше = предсказуемее
top_p	0.5–1.0	0.85	Ядерная выборка. Меньше = предсказуемее
gpt_cond_len	3–30 сек	12	Длина образца для клонирования голоса
sound_norm_refs	True/False	True	Авто-нормализация громкости образца
📝 Редактор словаря ударений

Словарь stress_dict.json хранится в папке config рабочей папки. Формат:
json

{
  "препод+обный": "преподо+бный",
  "+авва": "а+вва",
  "Господ+а": "Г+оспода"
}

    Ключ — неправильный вариант от ruaccent (с +)

    Значение — правильный вариант (с +)

    Словарь применяется на этапе 2, исправляя ошибки ruaccent

Редактор открывается кнопкой "📝 Открыть словарь". Требуется PyQt5.
🐛 Устранение проблем
Ошибка BeamSearchScorer not found
bash

pip install transformers==4.38.0

Ошибка weights_only при загрузке модели
bash

pip install torch==2.4.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cpu

Модель скачивается каждый раз

Удалите кэш TTS:
bash

rm -rf ~/.local/share/tts/

Нет звука / проблемы с FFmpeg
bash

sudo apt install ffmpeg

📦 Зависимости

    torch==2.4.0 — PyTorch (CPU-версия)

    TTS — Coqui XTTS

    transformers==4.38.0 — для совместимости

    PyPDF2, ebooklib, beautifulsoup4, lxml — извлечение текста

    scipy, numpy — обработка аудио

    PyQt5 — редактор словаря

    ffmpeg — конвертация в MP3

📄 Лицензия

Программа использует XTTS-v2 под лицензией CPML (Coqui Public Model License), разрешающей некоммерческое использование. Для коммерческого использования требуется приобретение лицензии у Coqui.ai.
🤝 Благодарности

    Coqui.ai за модель XTTS-v2

    snakers4 за Silero (использовалась в ранних версиях)

    ruaccent за расстановку ударений

📞 Поддержка

При возникновении вопросов создавайте issue в репозитории.

Автор: mikuz
Версия: 2.0 (XTTS + субтитры)
Дата: март 2026
