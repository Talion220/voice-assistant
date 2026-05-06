import threading
import customtkinter as ctk
from PIL import Image
import os

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
import sounddevice as sd
import vosk

import json
import queue
import sys
import traceback

import words
from skills import *
import voice

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VoiceAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Боря - Голосовой ассистент")
        self.root.geometry("400x250")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Переменные для управления потоком
        self.running = False
        self.thread = None

        # Настройки аудио и модели
        self.q = queue.Queue()
        self.model = vosk.Model('model_small')
        self.device = sd.default.device
        self.samplerate = int(sd.query_devices(self.device[0], 'input')['default_samplerate'])

        # Обучение классификатора
        self.vectorizer = CountVectorizer()
        vectors = self.vectorizer.fit_transform(list(words.data_set.keys()))
        self.clf = LogisticRegression()
        self.clf.fit(vectors, list(words.data_set.values()))
        del words.data_set

        self.setup_ui()

    def setup_ui(self):
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=16)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="🎙️ Боря",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(20, 5))

        self.subtitle_label = ctk.CTkLabel(
            self.main_frame,
            text="Твой персональный ассистент",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.subtitle_label.pack(pady=(0, 20))

        self.status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.status_frame.pack(pady=5)

        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=14),
            text_color="red"
        )
        self.status_indicator.pack(side="left", padx=(0, 5))

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Остановлен",
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(side="left")

        self.btn = ctk.CTkButton(
            self.main_frame,
            text="🚀 Запустить ассистента",
            command=self.toggle,
            width=200,
            height=50,
            corner_radius=16,
            font=ctk.CTkFont(size=16, weight="bold"),
            hover_color="#1E88E5",
        )
        self.btn.pack(pady=20)

        self.hint_label = ctk.CTkLabel(
            self.main_frame,
            text="Скажите \"Боря\" для активации",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.hint_label.pack(pady=(5, 10))

    def toggle(self):
        if not self.running:
            self.start()
        else:
            self.stop()

    def start(self):
        self.running = True
        self.btn.configure(text="⏹ Остановить ассистента", fg_color="#E53935", hover_color="#C62828")
        self.status_indicator.configure(text_color="green")
        self.status_label.configure(text="Активен - слушаю...")
        self.hint_label.configure(text="Говорите команду после слова \"Боря\"")
        self.title_label.configure(text="🎙️ Боря (активен)")

        self.thread = threading.Thread(target=self._run_assistant, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.btn.configure(text="🚀 Запустить ассистента", fg_color="#1E88E5", hover_color="#1565C0")
        self.status_indicator.configure(text_color="red")
        self.status_label.configure(text="Остановлен")
        self.hint_label.configure(text="Скажите \"Боря\" для активации")
        self.title_label.configure(text="🎙️ Боря")
        print("Остановка ассистента...")

    def on_closing(self):
        self.running = False
        self.root.destroy()
        sys.exit(0)

    def _callback(self, indata, frames, time, status):
        self.q.put(bytes(indata))

    def _recognize(self, data):
        print(f"Распознанная команда: '{data}'")

        trg = words.TRIGGERS.intersection(data.split())
        if not trg:
            return
        for trigger in trg:
            data = data.replace(trigger, '')
        data = data.strip()
        if not data:
            return

        text_vector = self.vectorizer.transform([data]).toarray()[0]
        answer = self.clf.predict([text_vector])[0]

        func_name = answer.split()[0]
        response_text = answer.replace(func_name, '').strip()

        if response_text:
            voice.speaker(response_text)

        try:
            exec(f"{func_name}()")
        except Exception as e:
            print(f"Ошибка выполнения функции {func_name}: {e}")
            voice.speaker("Произошла ошибка при выполнении команды")

    def _run_assistant(self):
        print("Ассистент готов. Скажите 'Боря' для активации...")
        rec = vosk.KaldiRecognizer(self.model, self.samplerate)

        stream = sd.RawInputStream(
            samplerate=self.samplerate,
            blocksize=16000,
            device=self.device[0],
            dtype='int16',
            channels=1,
            callback=self._callback
        )

        with stream:
            print("Микрофон активирован.")
            while self.running:
                try:
                    data = self.q.get(timeout=0.5)
                except queue.Empty:
                    continue

                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get('text', '').strip().lower()
                    if text:
                        print(f"Распознано: {text}")
                        self._recognize(text)

        print("Поток ассистента завершён.")


if __name__ == '__main__':
    root = ctk.CTk()
    app = VoiceAssistantApp(root)
    root.mainloop()