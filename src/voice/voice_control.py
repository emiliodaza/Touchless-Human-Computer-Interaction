import pyautogui
import speech_recognition as sr

from utils.shared_state import running, dictation_mode
from config.user_profile import USER_PROFILE

# ==============================
# Nombre TBD – Voice Module
# Español + Inglés (offline)
# ==============================

EXIT_PHRASE = "ya termine"

# Idioma actual del dictado
# "es" = español | "en" = inglés
current_language = "es"

def start_voice_control():
    global running, dictation_mode, current_language

    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    # Ajuste de ruido ambiente
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        print("🎙️ Voz offline activa")
        print("🗣️ Comandos disponibles:")
        print("- dictado español")
        print("- dictado ingles")
        print("- detener dictado")
        print("- clic / doble clic")
        print("- scroll arriba / scroll abajo")
        print("- ya termine")

    while running:
        try:
            with microphone as source:
                audio = recognizer.listen(source, phrase_time_limit=4)

            # --------------------------
            # RECONOCIMIENTO OFFLINE
            # --------------------------
            # Por ahora usamos PocketSphinx
            # Cuando migres a Vosk, esta línea cambia
            text = recognizer.recognize_sphinx(audio).lower()
            print("🗣️ Detectado:", text)

            # --------------------------
            # SALIR DEL SISTEMA
            # --------------------------
            if EXIT_PHRASE in text:
                print("👋 Cerrando AURA Control...")
                running = False
                break

            # --------------------------
            # CAMBIO DE IDIOMA
            # --------------------------
            if "dictado ingles" in text:
                current_language = "en"
                dictation_mode = True
                print("🇬🇧 Dictado en INGLÉS activado")
                continue

            if "dictado español" in text:
                current_language = "es"
                dictation_mode = True
                print("🇪🇸 Dictado en ESPAÑOL activado")
                continue

            if "detener dictado" in text:
                dictation_mode = False
                print("🛑 Dictado detenido")
                continue

            # --------------------------
            # ACCIONES DE CONTROL
            # --------------------------
            if "doble clic" in text:
                pyautogui.doubleClick()
                continue

            if "clic" in text:
                pyautogui.click()
                continue

            if "scroll arriba" in text:
                pyautogui.scroll(USER_PROFILE["scroll_amount"])
                continue

            if "scroll abajo" in text:
                pyautogui.scroll(-USER_PROFILE["scroll_amount"])
                continue

            # --------------------------
            # DICTADO DE TEXTO
            # --------------------------
            if dictation_mode:
                # En esta versión, el texto reconocido se escribe tal cual
                # Con Vosk aquí se diferenciará la transcripción ES / EN
                pyautogui.write(text + " ")

        except sr.UnknownValueError:
            # Silencio o ruido no reconocido
            pass
        except Exception as e:
            print("⚠️ Error en voz:", e)
