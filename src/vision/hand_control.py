import pyautogui
from config.user_profile import USER_PROFILE

def process_hand_control(hand_landmarks):
    fingers_up = 0
    tips = [8, 12, 16, 20]

    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers_up += 1

    if fingers_up >= 3:
        pyautogui.scroll(-USER_PROFILE["scroll_amount"])

    if fingers_up == 0:
        pyautogui.scroll(USER_PROFILE["scroll_amount"])