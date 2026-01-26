import pyautogui
from config.user_profile import USER_PROFILE

def process_eye_control(landmarks, screen_w, screen_h):
    eye = landmarks[475]
    pyautogui.moveTo(
        screen_w * eye.x * USER_PROFILE["cursor_speed"],
        screen_h * eye.y * USER_PROFILE["cursor_speed"]
    )

    if (landmarks[145].y - landmarks[159].y) < USER_PROFILE["click_threshold"]:
        pyautogui.click()
        pyautogui.sleep(USER_PROFILE["click_delay"])