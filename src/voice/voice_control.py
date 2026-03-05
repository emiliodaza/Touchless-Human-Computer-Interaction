import pyautogui
import speech_recognition as sr
import platform

import utils.shared_state as state
from config.user_profile import USER_PROFILE

# ==============================
# Nombre TBD – Voice Module
# Español + Inglés (offline)
# ==============================

EXIT_PHRASE = "ya termine"

# Detectar SO para tecla modificadora
IS_MAC = platform.system() == "Darwin"
MOD_KEY = "command" if IS_MAC else "ctrl"


def start_voice_control():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        print("🎙️ Voz offline activa")
        print("🗣️ Comandos disponibles:")
        print("─" * 35)
        print("  SISTEMA:")
        print("    ya termine      → Salir")
        print("    pausar          → Pausar tracking")
        print("    reanudar        → Reanudar tracking")
        print("  MOUSE:")
        print("    clic / doble clic / clic derecho")
        print("    scroll arriba / scroll abajo")
        print("  TECLADO:")
        print("    enter / escape / tab / espacio")
        print("    borrar / seleccionar todo")
        print("  EDICION:")
        print("    copiar / pegar / cortar")
        print("    deshacer / rehacer")
        print("  VENTANAS:")
        print("    cambiar ventana / cerrar ventana")
        print("    minimizar / pantalla completa")
        print("    captura / captura pantalla")
        print("  NAVEGACION:")
        print("    nueva pestana / cerrar pestana")
        print("    siguiente pestana / anterior pestana")
        print("    atras / adelante")
        print("  DICTADO:")
        print("    dictado espanol / dictado ingles")
        print("    detener dictado")
        print("─" * 35)

    while state.running:
        try:
            with microphone as source:
                audio = recognizer.listen(
                    source,
                    phrase_time_limit=USER_PROFILE["phrase_time_limit"]
                )

            text = recognizer.recognize_sphinx(audio).lower()
            print("🗣️ Detectado:", text)
            state.last_voice_command = text

            # ==========================
            # SISTEMA
            # ==========================
            if EXIT_PHRASE in text:
                print("👋 Cerrando sistema...")
                state.running = False
                break

            if "pausar" in text:
                state.paused = True
                print("⏸️ Tracking pausado")
                continue

            if "reanudar" in text:
                state.paused = False
                print("▶️ Tracking reanudado")
                continue

            # ==========================
            # DICTADO
            # ==========================
            if "dictado ingles" in text or "dictado english" in text:
                state.current_language = "en"
                state.dictation_mode = True
                print("🇬🇧 Dictado en INGLÉS activado")
                continue

            if "dictado espanol" in text or "dictado español" in text:
                state.current_language = "es"
                state.dictation_mode = True
                print("🇪🇸 Dictado en ESPAÑOL activado")
                continue

            if "detener dictado" in text:
                state.dictation_mode = False
                print("🛑 Dictado detenido")
                continue

            # ==========================
            # MOUSE
            # ==========================
            if "doble clic" in text:
                pyautogui.doubleClick()
                continue

            if "clic derecho" in text:
                pyautogui.rightClick()
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

            # ==========================
            # TECLAS BASICAS
            # ==========================
            if "enter" in text:
                pyautogui.press("enter")
                continue

            if "escape" in text:
                pyautogui.press("escape")
                continue

            if "tab" in text and "pestana" not in text and "pestana" not in text:
                pyautogui.press("tab")
                continue

            if "espacio" in text:
                pyautogui.press("space")
                continue

            if "borrar" in text:
                pyautogui.press("backspace")
                continue

            if "seleccionar todo" in text:
                pyautogui.hotkey(MOD_KEY, "a")
                continue

            # ==========================
            # EDICION
            # ==========================
            if "copiar" in text:
                pyautogui.hotkey(MOD_KEY, "c")
                continue

            if "pegar" in text:
                pyautogui.hotkey(MOD_KEY, "v")
                continue

            if "cortar" in text:
                pyautogui.hotkey(MOD_KEY, "x")
                continue

            if "deshacer" in text:
                pyautogui.hotkey(MOD_KEY, "z")
                continue

            if "rehacer" in text:
                pyautogui.hotkey(MOD_KEY, "shift", "z")
                continue

            # ==========================
            # VENTANAS
            # ==========================
            if "cambiar ventana" in text:
                pyautogui.hotkey(MOD_KEY, "tab")
                continue

            if "cerrar ventana" in text:
                pyautogui.hotkey(MOD_KEY, "w")
                continue

            if "minimizar" in text:
                pyautogui.hotkey(MOD_KEY, "m")
                continue

            if "pantalla completa" in text:
                if IS_MAC:
                    pyautogui.hotkey("ctrl", MOD_KEY, "f")
                else:
                    pyautogui.press("f11")
                continue

            # ==========================
            # CAPTURAS
            # ==========================
            if "captura pantalla" in text:
                if IS_MAC:
                    pyautogui.hotkey(MOD_KEY, "shift", "3")
                else:
                    pyautogui.press("printscreen")
                print("📸 Captura de pantalla completa")
                continue

            if "captura" in text:
                if IS_MAC:
                    pyautogui.hotkey(MOD_KEY, "shift", "4")
                else:
                    pyautogui.hotkey("win", "shift", "s")
                print("📸 Captura de región")
                continue

            # ==========================
            # NAVEGACION (browser)
            # ==========================
            if "nueva pestana" in text or "nueva pestaña" in text:
                pyautogui.hotkey(MOD_KEY, "t")
                continue

            if "cerrar pestana" in text or "cerrar pestaña" in text:
                pyautogui.hotkey(MOD_KEY, "w")
                continue

            if "siguiente pestana" in text or "siguiente pestaña" in text:
                pyautogui.hotkey(MOD_KEY, "shift", "]") if IS_MAC else pyautogui.hotkey("ctrl", "tab")
                continue

            if "anterior pestana" in text or "anterior pestaña" in text:
                pyautogui.hotkey(MOD_KEY, "shift", "[") if IS_MAC else pyautogui.hotkey("ctrl", "shift", "tab")
                continue

            if "atras" in text or "atrás" in text:
                pyautogui.hotkey(MOD_KEY, "[") if IS_MAC else pyautogui.hotkey("alt", "left")
                continue

            if "adelante" in text:
                pyautogui.hotkey(MOD_KEY, "]") if IS_MAC else pyautogui.hotkey("alt", "right")
                continue

            # ==========================
            # DICTADO
            # ==========================
            if state.dictation_mode:
                pyautogui.write(text + " ")

        except sr.UnknownValueError:
            pass
        except Exception as e:
            print("⚠️ Error en voz:", e)