import cv2
import mediapipe as mp
import threading
import pyautogui

from voice.voice_control import start_voice_control
from vision.eye_control import process_eye_control
from vision.hand_control import process_hand_control
from utils.shared_state import running

# ==============================
# NOMBRE TBD – Main
# Punto de entrada del sistema
# ==============================

print("🧠 Iniciando NOMBRE TBD (Offline)")
print("🎙️ Voz + 👀 Ojos + 🖐️ Mano ligera")

# ------------------------------
# Hilo de voz (offline)
# ------------------------------
voice_thread = threading.Thread(target=start_voice_control)
voice_thread.start()

# ------------------------------
# Cámara y MediaPipe
# ------------------------------
camera = cv2.VideoCapture(0)

mp_face = mp.solutions.face_mesh
mp_hands = mp.solutions.hands

face_mesh = mp_face.FaceMesh(refine_landmarks=True)
hands = mp_hands.Hands(max_num_hands=1)

# Tamaño de pantalla
screen_w, screen_h = pyautogui.size()

# ------------------------------
# Loop principal
# ------------------------------
while running:
    ret, frame = camera.read()
    if not ret:
        break

    # Espejo para interacción natural
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    face_result = face_mesh.process(rgb_frame)
    hand_result = hands.process(rgb_frame)

    # --------------------------
    # Control ocular
    # --------------------------
    if face_result.multi_face_landmarks:
        landmarks = face_result.multi_face_landmarks[0].landmark
        process_eye_control(landmarks, screen_w, screen_h)

    # --------------------------
    # Control de mano (ligero)
    # --------------------------
    if hand_result.multi_hand_landmarks:
        process_hand_control(hand_result.multi_hand_landmarks[0])

    # Ventana de visualización
    cv2.imshow("NOMBRE TBD ", frame)

# ------------------------------
# Cierre limpio
# ------------------------------
camera.release()
cv2.destroyAllWindows()
print("👋 NOMBRE TBD finalizado")
