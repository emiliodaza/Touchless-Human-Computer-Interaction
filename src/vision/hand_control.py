import pyautogui
import time
import math
from config.user_profile import USER_PROFILE

# hand control

_last_gesture_time = 0
_last_scroll_time = 0
_is_dragging = False
_pinch_was_active = False
_last_gesture_name = ""

# desactiva pausa de seguridad de pyautogui para fluidez
pyautogui.PAUSE = 0.01
pyautogui.FAILSAFE = True  # esquina superior izquierda para emergencia


def _distance(p1, p2):
    # distancia euclidiana entre dos landmarks.
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


def _count_fingers(hand_landmarks):
   # cuenta dedos levantados (sin pulgar).
    fingers_up = 0
    tips = [8, 12, 16, 20]
    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers_up += 1
    return fingers_up


def _is_thumb_up(hand_landmarks):
    # detecta si el pulgar está levantado.
    thumb_tip = hand_landmarks.landmark[4]
    thumb_ip = hand_landmarks.landmark[3]
    # pulgar levantado si está más arriba que la articulación
    return thumb_tip.y < thumb_ip.y


def _is_pinching(hand_landmarks):
    # detecta pinch (pulgar + índice juntos).
    thumb_tip = hand_landmarks.landmark[4]
    index_tip = hand_landmarks.landmark[8]
    dist = _distance(thumb_tip, index_tip)
    return dist < USER_PROFILE["pinch_threshold"]


def process_hand_control(hand_landmarks):
    """
    Procesa gestos de mano y ejecuta acciones.
    Retorna el nombre del gesto detectado para la UI.

    Gestos:
    Pinch (pulgar + índice): Clic izquierdo
    Pinch sostenido + mover: Arrastrar (drag)
    2 dedos (paz): Clic derecho
    3+ dedos: Scroll abajo
    Puño cerrado: Scroll arriba
    Pulgar arriba + puño: Doble clic
    """
    global _last_gesture_time, _last_scroll_time
    global _is_dragging, _pinch_was_active, _last_gesture_name

    now = time.time()
    fingers = _count_fingers(hand_landmarks)
    thumb_up = _is_thumb_up(hand_landmarks)
    pinching = _is_pinching(hand_landmarks)

    gesture_cooldown = USER_PROFILE["gesture_cooldown"]
    scroll_cooldown = USER_PROFILE["scroll_cooldown"]
    # dragging
    if pinching:
        if not _pinch_was_active:
            # inicio de pinch: clic
            if now - _last_gesture_time > gesture_cooldown:
                pyautogui.click()
                _last_gesture_time = now
                _last_gesture_name = "CLIC"
        else:
            # pinch sostenido: podría ser drag
            # (el cursor se mueve con eye tracking)
            if not _is_dragging and now - _last_gesture_time > 0.4:
                pyautogui.mouseDown()
                _is_dragging = True
                _last_gesture_name = "ARRASTRANDO"
        _pinch_was_active = True
        return _last_gesture_name

    # si se suelta el pinch
    if _pinch_was_active and not pinching:
        if _is_dragging:
            pyautogui.mouseUp()
            _is_dragging = False
            _last_gesture_name = "SOLTAR"
        _pinch_was_active = False
        return _last_gesture_name

    if thumb_up and fingers == 0:
        if now - _last_gesture_time > gesture_cooldown:
            pyautogui.doubleClick()
            _last_gesture_time = now
            _last_gesture_name = "DOBLE CLIC"
        return _last_gesture_name

    if fingers == 2:
        if now - _last_gesture_time > gesture_cooldown:
            pyautogui.rightClick()
            _last_gesture_time = now
            _last_gesture_name = "CLIC DERECHO"
        return _last_gesture_name

    if fingers >= 3:
        if now - _last_scroll_time > scroll_cooldown:
            pyautogui.scroll(-USER_PROFILE["scroll_amount"])
            _last_scroll_time = now
            _last_gesture_name = "SCROLL ABAJO"
        return _last_gesture_name

    if fingers == 0 and not thumb_up:
        if now - _last_scroll_time > scroll_cooldown:
            pyautogui.scroll(USER_PROFILE["scroll_amount"])
            _last_scroll_time = now
            _last_gesture_name = "SCROLL ARRIBA"
        return _last_gesture_name

    if fingers == 1:
        _last_gesture_name = "APUNTANDO"
        return _last_gesture_name

    _last_gesture_name = ""
    return _last_gesture_name