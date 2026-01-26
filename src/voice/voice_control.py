import speech_recognition as sr
import pyautogui
from utils.shared_state import running, dictation_mode
from config.user_profile import USER_PROFILE

EXIT_PHRASE = "ya termine"


def start_voice_control():
    global running, dictation_mode
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)

    while running:
        try:
            with mic as source:
                audio = recognizer.listen(source, phrase_time_limit=4)
            text = recognizer.recognize_sphinx(audio).lower()

            if EXIT_PHRASE in text:
                running = False
                break

            if "clic" in text:
                pyautogui.click()

            if "doble clic" in text:
                pyautogui.doubleClick()

            if "scroll arriba" in text:
                pyautogui.scroll(USER_PROFILE["scroll_amount"])

            if "scroll abajo" in text:
                pyautogui.scroll(-USER_PROFILE["scroll_amount"])

            if "dictado" in text:
                dictation_mode = True

            if "detener dictado" in text:
                dictation_mode = False

            if dictation_mode and text not in ["dictado", "detener dictado"]:
                pyautogui.write(text + " ")

        except:
            pass
