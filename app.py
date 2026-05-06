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

PRIMARY_COLOR = "#005bff"
PRIMARY_HOVER = "#0047cc"
DANGER_COLOR = "#E53935"
DANGER_HOVER = "#C62828"

class VoiceAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Боря - Голосовой ассистент")
        self.root.geometry("400x280")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.running = False
        self.thread = None
        self.current_theme = "dark"

        self.q = queue.Queue()
        self.model = vosk.Model('model_small')
        self.device = sd.default.device
        self.samplerate = int(sd.query_devices(self.device[0], 'input')['default_samplerate'])

        self.vectorizer = CountVectorizer()
        vectors = self.vectorizer.fit_transform(list(words.data_set.keys()))
        self.clf = LogisticRegression()
        self.clf.fit(vectors, list(words.data_set.values()))
        del words.data_set

        self.setup_ui()

    def setup_ui(self):
        self.main_frame = ctk.CTkFrame(
            self.root,
            corner_radius=16,
            fg_color=("#F5F5F5", "#1A1A1A")
        )
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.settings_button = ctk.CTkButton(
            self.main_frame,
            text="⚙",
            width=30,
            height=30,
            corner_radius=8,
            fg_color="transparent",
            hover_color=("#E0E0E0", "#2A2A2A"),
            font=ctk.CTkFont(size=18),
            command=self.show_settings
        )
        self.settings_button.place(x=310, y=10)

        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="🎤 Боря",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white",
        )
        self.title_label.pack(pady=(20, 5))

        self.subtitle_label = ctk.CTkLabel(
            self.main_frame,
            text="Твой персональный ассистент",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.subtitle_label.pack(pady=(0, 15))

        self.status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.status_frame.pack(pady=5)

        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color="#FF5252"
        )
        self.status_indicator.pack(side="left", padx=(0, 8))

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Остановлен",
            font=ctk.CTkFont(size=14),
            text_color="white"
        )
        self.status_label.pack(side="left")

        self.btn = ctk.CTkButton(
            self.main_frame,
            text="Запустить ассистента",
            command=self.toggle,
            width=250,
            height=80,
            corner_radius=20,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=PRIMARY_COLOR,
            hover_color=PRIMARY_HOVER,
            border_width=2,
            border_color=PRIMARY_COLOR
        )
        self.btn.pack(pady=15, padx=30)

        self.hint_label = ctk.CTkLabel(
            self.main_frame,
            text="Скажите \"Боря\" для активации",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.hint_label.pack(pady=(10, 15))

        self.settings_frame = ctk.CTkFrame(
            self.root,
            corner_radius=16,
            fg_color=("#F5F5F5", "#1A1A1A")
        )

        self.back_button = ctk.CTkButton(
            self.settings_frame,
            text="←",
            width=30,
            height=30,
            corner_radius=8,
            fg_color="transparent",
            hover_color=("#E0E0E0", "#2A2A2A"),
            font=ctk.CTkFont(size=18),
            command=self.show_main
        )
        self.back_button.place(x=10, y=10)

        self.settings_title = ctk.CTkLabel(
            self.settings_frame,
            text="Настройки",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        )
        self.settings_title.pack(pady=(20, 30))

        self.theme_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.theme_frame.pack(pady=10)

        self.theme_label = ctk.CTkLabel(
            self.theme_frame,
            text="Темная тема",
            font=ctk.CTkFont(size=16),
            text_color="white"
        )
        self.theme_label.pack(side="left", padx=(0, 20))

        self.theme_switch = ctk.CTkSwitch(
            self.theme_frame,
            text="",
            command=self.toggle_theme,
            button_color=PRIMARY_COLOR,
            button_hover_color=PRIMARY_HOVER,
            progress_color=PRIMARY_COLOR
        )
        self.theme_switch.pack(side="left")
        self.theme_switch.select()

    def show_settings(self):
        self.main_frame.pack_forget()
        self.settings_frame.pack(pady=20, padx=20, fill="both", expand=True)

    def show_main(self):
        self.settings_frame.pack_forget()
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

    def toggle_theme(self):
        if self.theme_switch.get():
            ctk.set_appearance_mode("dark")
            self.current_theme = "dark"
            self.theme_label.configure(text="Темная тема")
        else:
            ctk.set_appearance_mode("light")
            self.current_theme = "light"
            self.theme_label.configure(text="Светлая тема")

    def toggle(self):
        if not self.running:
            self.start()
        else:
            self.stop()

    def start(self):
        self.running = True
        self.btn.configure(
            text="█  Остановить ассистента",
            fg_color=DANGER_COLOR,
            hover_color=DANGER_HOVER,
            border_color=DANGER_COLOR
        )
        self.status_indicator.configure(text_color="#4CAF50")
        self.status_label.configure(text="Активен - слушаю...")
        self.hint_label.configure(text="Говорите команду после слова \"Боря\"")

        self.thread = threading.Thread(target=self._run_assistant, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self.btn.configure(
            text="Запустить ассистента",
            fg_color=PRIMARY_COLOR,
            hover_color=PRIMARY_HOVER,
            border_color=PRIMARY_COLOR
        )
        self.status_indicator.configure(text_color="#FF5252")
        self.status_label.configure(text="Остановлен")
        self.hint_label.configure(text="Скажите \"Боря\" для активации")
        self.title_label.configure(text="🎤 Боря")
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