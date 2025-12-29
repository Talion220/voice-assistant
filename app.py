'''
Голосовой ассистент "Боря"
python 3.8 и выше.
'''

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

q = queue.Queue()
model = vosk.Model('model_small')
device = sd.default.device
samplerate = int(sd.query_devices(device[0], 'input')['default_samplerate'])

def callback(indata, frames, time, status):
    '''Добавляет в очередь семплы из потока'''
    q.put(bytes(indata))

def recognize(data, vectorizer, clf):
    '''Анализ распознанной речи'''
    print(f"Распознанная команда: '{data}'")  # Для отладки

    # Проверяем наличие триггера
    trg = words.TRIGGERS.intersection(data.split())
    if not trg:
        print("Триггер не найден")
        return

    # Удаляем имя бота из текста
    for trigger in trg:
        data = data.replace(trigger, '')
    data = data.strip()

    if not data:
        print("Пустая команда после триггера")
        return

    # Получаем вектор текста
    text_vector = vectorizer.transform([data]).toarray()[0]
    answer = clf.predict([text_vector])[0]

    print(f"Найден ответ: '{answer}'")  # Для отладки

    # Извлекаем имя функции
    func_name = answer.split()[0]
    response_text = answer.replace(func_name, '').strip()

    # Озвучиваем ответ
    if response_text:
        voice.speaker(response_text)

    # Выполняем функцию
    try:
        exec(f"{func_name}()")
    except Exception as e:
        print(f"Ошибка выполнения функции {func_name}: {e}")
        voice.speaker("Произошла ошибка при выполнении команды")

def main():
    '''Обучаем матрицу ИИ и слушаем микрофон'''
    print("Инициализация ассистента...")

    # Обучение матрицы
    vectorizer = CountVectorizer()
    vectors = vectorizer.fit_transform(list(words.data_set.keys()))

    clf = LogisticRegression()
    clf.fit(vectors, list(words.data_set.values()))

    # Очищаем память
    del words.data_set

    print("Ассистент готов к работе. Скажите 'Боря' для активации...")

    # Создаем распознаватель
    rec = vosk.KaldiRecognizer(model, samplerate)

    # Открываем аудиопоток
    with sd.RawInputStream(samplerate=samplerate,
                          blocksize=16000,
                          device=device[0],
                          dtype='int16',
                          channels=1,
                          callback=callback):

        print("Микрофон активирован. Ожидание команд...")

        while True:
            try:
                # Получаем данные из очереди
                data = q.get()

                if rec.AcceptWaveform(data):
                    # Распознанная речь
                    result = json.loads(rec.Result())
                    text = result.get('text', '').strip().lower()

                    if text:
                        print(f"Распознано: {text}")
                        recognize(text, vectorizer, clf)
                    else:
                        # Частичный результат для отладки
                        partial = json.loads(rec.PartialResult())
                        partial_text = partial.get('partial', '')
                        if partial_text:
                            print(f"Слышу: {partial_text}")

            except KeyboardInterrupt:
                print("\nЗавершение работы...")
                sys.exit(0)
            except Exception as e:
                print(f"Ошибка в основном цикле: {e}")
                traceback.print_exc()
                continue

if __name__ == '__main__':
    main()