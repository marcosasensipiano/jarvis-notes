"""Webcam loop. Needs `pip install opencv-python mediapipe` and a camera on the machine running Jarvis.
Everything it decides is done by the pure-Python engine; this file only moves pixels in and actions out."""
import time
from .engine import GestureEngine, load_config


def run(camera=0, dry_run=False):
    try:
        import cv2
        import mediapipe as mp
    except ImportError:
        print("Gesture control needs a camera library. Install it with:\n  pip install opencv-python mediapipe")
        return 1
    from ..devices import tv as tvmod
    tv = tvmod.DryRunTV() if dry_run else tvmod.load_tv()
    if tv is None:
        print("No TV configured. Use --dry-run to test, or set up config/devices.json (see `jarvis discover`).")
        return 1
    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        print(f"Could not open camera {camera}.")
        return 1
    engine = GestureEngine(load_config())
    hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.6)
    print("Gesture control running. Hold a pose ~1s or swipe an open palm. Press q in the window to quit.")
    last = ""
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)  # mirror so +x is the user's right
            res = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            lm = None
            if res.multi_hand_landmarks:
                lm = [(p.x, p.y) for p in res.multi_hand_landmarks[0].landmark]
            hit = engine.update(time.monotonic(), lm)
            if hit:
                gesture, action = hit
                last = f"{gesture} -> {action}: {tv.send(action)}"
                print(last)
            cv2.putText(frame, last[-60:], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (46, 230, 255), 2)
            cv2.imshow("Jarvis gestures", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
    return 0
