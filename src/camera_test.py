import cv2
import time
import numpy as np

for idx in range(5):
    print(f"\nTrying camera index {idx}...")
    cap = cv2.VideoCapture(idx, cv2.CAP_AVFOUNDATION)
    time.sleep(2)
    
    if not cap.isOpened():
        print(f"  Index {idx}: could not open")
        cap.release()
        continue
    
    for _ in range(60):
        cap.read()
    
    ret, frame = cap.read()
    if ret:
        brightness = np.mean(frame)
        print(f"  Index {idx}: OK, shape={frame.shape}, brightness={brightness:.2f}")
        if brightness > 5:
            cv2.imwrite(f"test_cam_{idx}.jpg", frame)
            print(f"This one looks real! Saved test_cam_{idx}.jpg")
    else:
        print(f"  Index {idx}: no frames")
    
    cap.release()