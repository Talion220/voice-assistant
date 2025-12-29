import pyttsx3


def speaker(text):
    """Синхронная озвучка текста (без потоков)"""
    if not text:
        return

    print(f"Озвучиваю: {text}")

    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 180)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"Ошибка озвучки: {e}")