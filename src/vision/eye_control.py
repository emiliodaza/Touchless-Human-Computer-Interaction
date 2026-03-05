import pyautogui
from config.user_profile import USER_PROFILE

# estado interno para suavizado
_prev_x = 0
_prev_y = 0

pyautogui.PAUSE = 0.01


def _remap(value, in_min, in_max, out_min, out_max):
    """remapea un valor de un rango a otro."""
    clamped = max(in_min, min(in_max, value))
    return out_min + (clamped - in_min) / (in_max - in_min) * (out_max - out_min)


def process_eye_control(landmarks, screen_w, screen_h):
    global _prev_x, _prev_y

    # centro del iris izquierdo
    eye = landmarks[475]

    # rango del movimiento del iris a la pantalla
    sens = USER_PROFILE["cursor_speed"]
    center_x = 0.5
    center_y = 0.5
    range_x = 0.15 / sens  
    range_y = 0.10 / sens

    target_x = _remap(eye.x,
                       center_x - range_x, center_x + range_x,
                       0, screen_w)
    target_y = _remap(eye.y,
                       center_y - range_y, center_y + range_y,
                       0, screen_h)

    # suavizado exponencial
    smooth = USER_PROFILE["cursor_smoothing"]
    if _prev_x == 0 and _prev_y == 0:
        _prev_x = target_x
        _prev_y = target_y

    new_x = _prev_x + (target_x - _prev_x) * (1 - smooth)
    new_y = _prev_y + (target_y - _prev_y) * (1 - smooth)

    _prev_x = new_x
    _prev_y = new_y

    pyautogui.moveTo(int(new_x), int(new_y), _pause=False)