import os
import subprocess
import tempfile
from pathlib import Path
import time
import numpy as np
import torch
from scipy.io.wavfile import write as write_wav
from TTS.api import TTS

class AudioGenerator:
    """Генерация аудио через XTTS с поддержкой фрагментов, пауз и субтитров"""
    
    def __init__(self, work_dir, speaker='Claribel Dervla', speed=1.0, 
                 output_format='mp3', speaker_wav=None, 
                 fragment_pause=0.2, initial_pause=0.0,
                 progress_callback=None, start_time=None,
                 generate_subtitles=True,
                 temperature=0.85,
                 repetition_penalty=2.0,
                 length_penalty=1.0,
                 top_k=50,
                 top_p=0.85,
                 num_beams=1,
                 gpt_cond_len=12,
                 sound_norm_refs=True):
        self.work_dir = Path(work_dir)
        self.fragments_dir = self.work_dir / "03_text_fragments"
        self.audio_dir = self.work_dir / "04_audio"
        self.subtitles_dir = self.work_dir / "05_subtitles"
        self.audio_dir.mkdir(exist_ok=True)
        self.subtitles_dir.mkdir(exist_ok=True)
        
        self.speaker = speaker
        self.speed = speed
        self.output_format = output_format.lower()
        self.speaker_wav = speaker_wav
        self.fragment_pause = fragment_pause
        self.initial_pause = initial_pause
        self.generate_subtitles = generate_subtitles
        
        self.temperature = temperature
        self.repetition_penalty = repetition_penalty
        self.length_penalty = length_penalty
        self.top_k = top_k
        self.top_p = top_p
        self.num_beams = num_beams
        self.gpt_cond_len = gpt_cond_len
        self.sound_norm_refs = sound_norm_refs
        
        self.progress_callback = progress_callback
        self.start_time = start_time or time.time()
        
        print(f"Загрузка XTTS модели...")
        print(f"  Голос: {speaker if not speaker_wav else 'Клонирование: ' + speaker_wav}")
        print(f"  Скорость: {speed}x")
        print(f"  Пауза между фрагментами: {fragment_pause} сек")
        print(f"  Пауза в начале: {initial_pause} сек")
        print(f"  Формат: {self.output_format.upper()}")
        print(f"  Субтитры: {'включены' if generate_subtitles else 'выключены'}")
        print(f"  Параметры синтеза:")
        print(f"    temperature: {temperature}")
        print(f"    repetition_penalty: {repetition_penalty}")
        print(f"    length_penalty: {length_penalty}")
        print(f"    top_k: {top_k}")
        print(f"    top_p: {top_p}")
        print(f"    num_beams: {num_beams}")
        print(f"    gpt_cond_len: {gpt_cond_len} сек")
        print(f"    sound_norm_refs: {sound_norm_refs}")
        
        self._load_model()
    
    def _format_time(self, seconds):
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        if minutes > 0:
            return f"{minutes} минут {secs} секунд"
        return f"{secs} секунд"
    
    def _format_srt_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _update_progress(self, current, total):
        if self.progress_callback:
            elapsed = time.time() - self.start_time
            elapsed_str = self._format_time(elapsed)
            self.progress_callback(current, total, elapsed_str)
    
    def _load_model(self):
        """Загрузка XTTS модели с пользовательскими параметрами"""
        try:
            # Загружаем стандартную модель
            self.tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=False)
            
            # Обновляем параметры в загруженной модели
            if hasattr(self.tts, 'synthesizer') and hasattr(self.tts.synthesizer, 'tts_model'):
                model = self.tts.synthesizer.tts_model
                model.temperature = self.temperature
                model.repetition_penalty = self.repetition_penalty
                model.length_penalty = self.length_penalty
                model.top_k = self.top_k
                model.top_p = self.top_p
                model.num_beams = self.num_beams
                model.gpt_cond_len = self.gpt_cond_len
                model.sound_norm_refs = self.sound_norm_refs
                print("XTTS модель загружена с пользовательскими параметрами")
            else:
                print("XTTS модель загружена (стандартная)")
                
        except Exception as e:
            print(f"Ошибка загрузки XTTS: {e}")
            raise
    
    def _save_audio(self, audio_data, output_path, sample_rate=24000):
        if hasattr(audio_data, 'cpu'):
            audio_data = audio_data.cpu().numpy()
        
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        if self.output_format == 'wav':
            write_wav(str(output_path), sample_rate, audio_int16)
            return output_path
        
        if self.output_format == 'mp3':
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_wav = tmp.name
            
            try:
                write_wav(tmp_wav, sample_rate, audio_int16)
                mp3_path = output_path.with_suffix('.mp3')
                cmd = ['ffmpeg', '-y', '-i', tmp_wav, '-b:a', '192k', '-ar', str(sample_rate), str(mp3_path)]
                subprocess.run(cmd, capture_output=True, check=True)
                return mp3_path
            finally:
                if os.path.exists(tmp_wav):
                    os.unlink(tmp_wav)
        
        return output_path
    
    def _clean_text(self, text):
        text = text.replace('+', '')
        import unicodedata
        text = unicodedata.normalize('NFD', text)
        text = ''.join(ch for ch in text if not unicodedata.combining(ch))
        return text
    
    def _generate_fragment(self, text):
        tts_params = {
            'text': text,
            'language': 'ru',
            'speed': self.speed,
            'temperature': self.temperature,
            'repetition_penalty': self.repetition_penalty,
            'length_penalty': self.length_penalty,
            'top_k': self.top_k,
            'top_p': self.top_p,
            'num_beams': self.num_beams,
            'gpt_cond_len': self.gpt_cond_len,
            'sound_norm_refs': self.sound_norm_refs
        }
        
        if self.speaker_wav and os.path.exists(self.speaker_wav):
            tts_params['speaker_wav'] = self.speaker_wav
        else:
            tts_params['speaker'] = self.speaker
        
        tts_params['file_path'] = None
        audio = self.tts.tts(**tts_params)
        
        if isinstance(audio, np.ndarray):
            return torch.from_numpy(audio)
        return audio
    
    def generate_all(self):
        if not self.fragments_dir.exists():
            print(f"Папка {self.fragments_dir} не найдена")
            return [], []
        
        fragment_folders = [d for d in self.fragments_dir.iterdir() if d.is_dir()]
        
        if not fragment_folders:
            print("Нет папок с фрагментами")
            return [], []
        
        results = []
        subtitles_results = []
        total_files = len(fragment_folders)
        sample_rate = 24000
        
        for idx, folder in enumerate(fragment_folders, 1):
            print(f"\n--- Обработка: {folder.name} ---")
            
            fragment_files = sorted(folder.glob("fragment_*.txt"))
            print(f"  Найдено фрагментов: {len(fragment_files)}")
            
            audio_parts = []
            fragments_data = []
            current_time = self.initial_pause
            pause_samples = int(sample_rate * self.fragment_pause)
            initial_pause_samples = int(sample_rate * self.initial_pause)
            
            if self.initial_pause > 0:
                audio_parts.append(torch.zeros(initial_pause_samples))
            
            for i, frag_file in enumerate(fragment_files, 1):
                with open(frag_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                if not text.strip():
                    continue
                
                print(f"    Фрагмент {i}/{len(fragment_files)}")
                audio = self._generate_fragment(text)
                
                if isinstance(audio, np.ndarray):
                    audio = torch.from_numpy(audio)
                elif isinstance(audio, list) and len(audio) > 0:
                    audio = audio[0] if isinstance(audio[0], torch.Tensor) else torch.from_numpy(np.array(audio))
                
                duration = audio.shape[0] / sample_rate
                
                if self.generate_subtitles:
                    fragments_data.append({
                        'index': len(fragments_data) + 1,
                        'start': current_time,
                        'end': current_time + duration,
                        'text': self._clean_text(text)
                    })
                
                audio_parts.append(audio)
                current_time += duration
                
                if i < len(fragment_files) and self.fragment_pause > 0:
                    audio_parts.append(torch.zeros(pause_samples))
                    current_time += self.fragment_pause
            
            if not audio_parts:
                print(f"  Нет сгенерированных фрагментов")
                continue
            
            final_audio = torch.cat(audio_parts)
            
            output_name = folder.name.replace('_replaced', '')
            extension = '.mp3' if self.output_format == 'mp3' else '.wav'
            output_file = self.audio_dir / f"{output_name}{extension}"
            self._save_audio(final_audio, output_file, sample_rate)
            results.append(output_file)
            print(f"  Сохранено аудио: {output_file.name}")
            
            if self.generate_subtitles and fragments_data:
                srt_file = self.subtitles_dir / f"{output_name}.srt"
                with open(srt_file, 'w', encoding='utf-8') as f:
                    for frag in fragments_data:
                        start_str = self._format_srt_time(frag['start'])
                        end_str = self._format_srt_time(frag['end'])
                        f.write(f"{frag['index']}\n")
                        f.write(f"{start_str} --> {end_str}\n")
                        f.write(f"{frag['text']}\n\n")
                subtitles_results.append(srt_file)
                print(f"  Сохранены субтитры: {srt_file.name} ({len(fragments_data)} записей)")
            
            self._update_progress(idx, total_files)
        
        return results, subtitles_results
    
    def get_audio_files(self):
        extension = '.mp3' if self.output_format == 'mp3' else '.wav'
        return list(self.audio_dir.glob(f"*{extension}"))
    
    def get_subtitle_files(self):
        return list(self.subtitles_dir.glob("*.srt"))