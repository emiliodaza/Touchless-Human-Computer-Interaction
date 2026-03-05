import cv2
import mediapipe as mp
import threading
import pyautogui
import time
import numpy as np

from voice.voice_control import start_voice_control
from vision.eye_control import process_eye_control
from vision.hand_control import process_hand_control
import utils.shared_state as state
from config.user_profile import USER_PROFILE

# Touchless

print("🧠 Iniciando NOMBRE TBD (Offline)")
print("🎙️ Voz + 👀 Ojos + 🖐️ Mano ligera")
print("")
print("Atajos de teclado:")
print("  ESC / Q  : Salir")
print("  H        : Mostrar/ocultar ayuda")
print("  P        : Pausar/reanudar tracking")
print("  D        : Activar/desactivar dictado")
print("")

voice_thread = threading.Thread(target=start_voice_control, daemon=True)
voice_thread.start()

class CameraThread:
    """camera capture in separate thread"""
    def __init__(self, index, width, height):
        self.cap = cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self.ret = False
        self.frame = None
        self.lock = threading.Lock()
        self.running = True

        # Warm-up
        time.sleep(2)
        for _ in range(60):
            self.cap.read()

        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            ret, frame = self.cap.read()
            with self.lock:
                self.ret = ret
                self.frame = frame

    def read(self):
        with self.lock:
            if self.frame is None:
                return False, None
            return self.ret, self.frame.copy()

    def release(self):
        self.running = False
        self.thread.join(timeout=2)
        self.cap.release()


camera = CameraThread(
    USER_PROFILE["camera_index"],
    USER_PROFILE["camera_width"],
    USER_PROFILE["camera_height"]
)

mp_face = mp.solutions.face_mesh
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

face_mesh = mp_face.FaceMesh(
    refine_landmarks=True,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5,
)

# screen size
screen_w, screen_h = pyautogui.size()

LEFT_IRIS = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]
LEFT_EYE_CONTOUR = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_CONTOUR = [362, 385, 387, 263, 373, 380]

# loop state
frame_count = 0
fps = 0
fps_timer = time.time()
fps_frame_count = 0

current_hand_gesture = ""
face_detected = False
hand_detected = False
last_face_lm = None
last_hand_lm = None

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 720

def draw_eye_tracking(frame, face_landmarks, frame_w, frame_h):
    """dibuja iris y contorno de ojos."""
    landmarks = face_landmarks.landmark

    for eye_indices in [LEFT_EYE_CONTOUR, RIGHT_EYE_CONTOUR]:
        points = []
        for idx in eye_indices:
            x = int(landmarks[idx].x * frame_w)
            y = int(landmarks[idx].y * frame_h)
            points.append((x, y))
        for i in range(len(points)):
            cv2.line(frame, points[i], points[(i + 1) % len(points)], (0, 255, 200), 1)

    for iris_indices in [LEFT_IRIS, RIGHT_IRIS]:
        iris_points = []
        for idx in iris_indices:
            x = int(landmarks[idx].x * frame_w)
            y = int(landmarks[idx].y * frame_h)
            iris_points.append((x, y))
        cx = int(sum(p[0] for p in iris_points) / len(iris_points))
        cy = int(sum(p[1] for p in iris_points) / len(iris_points))
        radius = max(int(abs(iris_points[0][0] - iris_points[2][0]) / 2), 2)
        cv2.circle(frame, (cx, cy), radius, (0, 255, 0), 1)
        cv2.circle(frame, (cx, cy), 2, (0, 255, 0), -1)


def draw_hand_tracking(frame, hand_landmarks, gesture_name):
    """dibuja esqueleto de mano y gesto actual"""
    mp_drawing.draw_landmarks(
        frame,
        hand_landmarks,
        mp_hands.HAND_CONNECTIONS,
        mp_drawing_styles.get_default_hand_landmarks_style(),
        mp_drawing_styles.get_default_hand_connections_style()
    )

    if gesture_name in ["CLIC", "ARRASTRANDO"]:
        frame_h, frame_w = frame.shape[:2]
        thumb = hand_landmarks.landmark[4]
        index = hand_landmarks.landmark[8]
        tx, ty = int(thumb.x * frame_w), int(thumb.y * frame_h)
        ix, iy = int(index.x * frame_w), int(index.y * frame_h)
        cv2.line(frame, (tx, ty), (ix, iy), (0, 255, 255), 2)
        cv2.circle(frame, (tx, ty), 6, (0, 255, 255), -1)
        cv2.circle(frame, (ix, iy), 6, (0, 255, 255), -1)

    if gesture_name:
        frame_h, frame_w = frame.shape[:2]
        wrist = hand_landmarks.landmark[0]
        wx = int(wrist.x * frame_w)
        wy = int(wrist.y * frame_h) - 30

        color_map = {
            "CLIC": (0, 255, 255),
            "DOBLE CLIC": (0, 255, 0),
            "CLIC DERECHO": (255, 100, 0),
            "ARRASTRANDO": (0, 165, 255),
            "SOLTAR": (200, 200, 200),
            "SCROLL ARRIBA": (255, 100, 0),
            "SCROLL ABAJO": (0, 100, 255),
            "APUNTANDO": (200, 200, 200),
        }
        color = color_map.get(gesture_name, (200, 200, 200))
        cv2.putText(frame, gesture_name, (wx - 50, wy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)


def draw_status_bar(frame):
    """barra de estado superior."""
    frame_h, frame_w = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame_w, 44), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    cv2.putText(frame, "NOMBRE TBD", (10, 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 200), 1)

    parts = [f"FPS: {fps}"]
    if state.paused:
        parts.append("PAUSADO")
    else:
        parts.append("VOZ: ON")
    if state.dictation_mode:
        parts.append(f"DICTADO: {state.current_language.upper()}")

    status = "  |  ".join(parts)
    cv2.putText(frame, status, (10, 36),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 180, 180), 1)

    if state.last_voice_command:
        cmd_text = f'"{state.last_voice_command}"'
        text_size = cv2.getTextSize(cmd_text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
        cv2.putText(frame, cmd_text, (frame_w - text_size[0] - 10, 36),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 200, 0), 1)

    if state.dictation_mode:
        cv2.circle(frame, (frame_w - 15, 15), 6, (0, 0, 255), -1)

    if state.paused:
        cv2.putText(frame, "|| PAUSA", (frame_w // 2 - 40, frame_h // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)


def draw_tracking_indicators(frame, face_active, hand_active):
    """Indicators en la barra inferior"""
    frame_h, frame_w = frame.shape[:2]

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, frame_h - 36), (frame_w, frame_h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    indicators = [
        ("OJOS", face_active, (0, 255, 200)),
        ("MANO", hand_active, (0, 200, 255)),
        ("VOZ", state.running, (255, 200, 0)),
    ]

    x = 10
    y = frame_h - 12
    for label, active, color in indicators:
        dot_color = color if active else (60, 60, 60)
        text_color = (220, 220, 220) if active else (80, 80, 80)
        cv2.circle(frame, (x + 5, y), 4, dot_color, -1)
        cv2.putText(frame, label, (x + 14, y + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, text_color, 1)
        x += 90

    keys = "H=Ayuda  P=Pausa  Q=Salir"
    text_size = cv2.getTextSize(keys, cv2.FONT_HERSHEY_SIMPLEX, 0.38, 1)[0]
    cv2.putText(frame, keys, (frame_w - text_size[0] - 10, y + 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (120, 120, 120), 1)


def draw_instructions_panel(frame):
    """Panel de instructions."""
    frame_h, frame_w = frame.shape[:2]

    panel_w = 250
    panel_h = 330
    x1 = frame_w - panel_w - 10
    y1 = 50
    x2 = frame_w - 10
    y2 = y1 + panel_h

    if y2 > frame_h - 40:
        y2 = frame_h - 40

    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 80, 80), 1)

    cv2.putText(frame, "CONTROLES", (x1 + 10, y1 + 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 200), 1)
    cv2.line(frame, (x1 + 8, y1 + 30), (x2 - 8, y1 + 30), (60, 60, 60), 1)

    instructions = [
        ("MANO", (0, 200, 255), True),
        ("Pinch = Clic", (170, 170, 170), False),
        ("Pinch largo = Arrastrar", (170, 170, 170), False),
        ("Paz (2) = Clic der.", (170, 170, 170), False),
        ("Pulgar = Doble clic", (170, 170, 170), False),
        ("3+ dedos = Scroll -", (170, 170, 170), False),
        ("Puno = Scroll +", (170, 170, 170), False),
        ("", None, False),
        ("OJOS", (0, 255, 200), True),
        ("Mirada = Cursor", (170, 170, 170), False),
        ("", None, False),
        ("VOZ", (255, 200, 0), True),
        ("clic / copiar / pegar", (170, 170, 170), False),
        ("captura / nueva pestana", (170, 170, 170), False),
        ("dictado espanol/ingles", (170, 170, 170), False),
        ("", None, False),
        ("TECLADO", (100, 100, 255), True),
        ("ESC/Q=Salir  H=Ayuda", (170, 170, 170), False),
        ("P=Pausa  D=Dictado", (170, 170, 170), False),
    ]

    y = y1 + 45
    for text, color, is_header in instructions:
        if y > y2 - 8:
            break
        if text == "":
            y += 5
            continue
        if is_header:
            cv2.putText(frame, text, (x1 + 10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        else:
            cv2.putText(frame, text, (x1 + 18, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)
        y += 15


# window details
cv2.namedWindow("Touchless", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Touchless", WINDOW_WIDTH, WINDOW_HEIGHT)

print("Sistema listo")
print("")

while state.running:
    ret, frame = camera.read()
    if not ret or frame is None:
        continue

    frame = cv2.flip(frame, 1)
    frame_count += 1

    # FPS
    fps_frame_count += 1
    elapsed = time.time() - fps_timer
    if elapsed >= 1.0:
        fps = fps_frame_count
        fps_frame_count = 0
        fps_timer = time.time()

    # process media every N frames
    should_process = (frame_count % USER_PROFILE["process_every_n_frames"] == 0)

    if not state.paused and should_process:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        face_result = face_mesh.process(rgb_frame)
        hand_result = hands.process(rgb_frame)

        # eye control
        if face_result.multi_face_landmarks:
            face_detected = True
            last_face_lm = face_result.multi_face_landmarks[0]
            process_eye_control(last_face_lm.landmark, screen_w, screen_h)
        else:
            face_detected = False
            last_face_lm = None

        # hand control
        if hand_result.multi_hand_landmarks:
            hand_detected = True
            last_hand_lm = hand_result.multi_hand_landmarks[0]
            current_hand_gesture = process_hand_control(last_hand_lm)
        else:
            hand_detected = False
            last_hand_lm = None
            current_hand_gesture = ""

    # Resize for bigger screen
    frame = cv2.resize(frame, (WINDOW_WIDTH, WINDOW_HEIGHT))
    frame_h, frame_w = frame.shape[:2]

    # dibuja landmarks
    if last_face_lm:
        draw_eye_tracking(frame, last_face_lm, frame_w, frame_h)
    if last_hand_lm:
        draw_hand_tracking(frame, last_hand_lm, current_hand_gesture)

    # UI overlays
    draw_status_bar(frame)
    draw_tracking_indicators(frame, face_detected, hand_detected)

    if state.show_help:
        draw_instructions_panel(frame)

    # show window
    cv2.imshow("NOMBRE TBD", frame)

    # Keyboard controls
    key = cv2.waitKey(1) & 0xFF

    if key == 27 or key == ord('q') or key == ord('Q'):
        print("👋 Saliendo por teclado...")
        state.running = False
        break

    elif key == ord('h') or key == ord('H'):
        state.show_help = not state.show_help

    elif key == ord('p') or key == ord('P'):
        state.paused = not state.paused
        status = "pausado" if state.paused else "reanudado"
        print(f"{'⏸️' if state.paused else '▶️'} Tracking {status}")

    elif key == ord('d') or key == ord('D'):
        state.dictation_mode = not state.dictation_mode
        status = "activado" if state.dictation_mode else "desactivado"
        print(f"📝 Dictado {status}")


# cierre
state.running = False
camera.release()
face_mesh.close()
hands.close()
cv2.destroyAllWindows()
print("👋 NOMBRE TBD finalizado")