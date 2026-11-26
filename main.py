
import cv2
import mediapipe as mp
import pyttsx3
import sqlite3
import time
from datetime import datetime

# SMART TRANSLATION SYSTEM

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Demonstration gesture translations
GESTURES = {
    "OPEN_PALM": "Hello! How are you?",
    "FIST": "Thank you",
    "POINT": "I need help",
    "PEACE": "Nice to meet you"
}

# Text to speech
speaker = pyttsx3.init()
speaker.setProperty("rate", 145)

# DATABASE SETUP
connection = sqlite3.connect("translations.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gesture TEXT,
    translated_text TEXT,
    created_at TEXT
)
""")
connection.commit()


def save_translation(gesture, text):
    cursor.execute("""
    INSERT INTO history
    (gesture, translated_text, created_at)
    VALUES (?, ?, ?)
    """, (
        gesture,
        text,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    connection.commit()


# HAND GESTURE RECOGNITION
def recognize_gesture(hand_landmarks):

    landmarks = hand_landmarks.landmark

    fingers = []

    finger_tips = [8, 12, 16, 20]
    finger_pips = [6, 10, 14, 18]

    for tip, pip in zip(finger_tips, finger_pips):
        if landmarks[tip].y < landmarks[pip].y:
            fingers.append(1)
        else:
            fingers.append(0)

    if fingers == [1, 1, 1, 1]:
        return "OPEN_PALM"

    elif fingers == [0, 0, 0, 0]:
        return "FIST"

    elif fingers == [1, 0, 0, 0]:
        return "POINT"

    elif fingers == [1, 1, 0, 0]:
        return "PEACE"

    return "UNKNOWN"


# MAIN APPLICATION
def main():

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Error: Camera not found.")
        return

    last_gesture = None
    last_saved = 0
    last_spoken = 0

    candidate = None
    stable_frames = 0

    current_text = "Show your hand to the camera"

    print("SMART TRANSLATION SYSTEM STARTED")
    print("Q = Quit")
    print("S = Speak")
    print("C = Clear")

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    ) as hands:

        while True:

            success, frame = camera.read()

            if not success:
                print("Camera frame unavailable")
                break

            frame = cv2.flip(frame, 1)

            rgb_frame = cv2.cvtColor(
                frame, cv2.COLOR_BGR2RGB
            )

            results = hands.process(rgb_frame)

            detected_gesture = "UNKNOWN"

            if results.multi_hand_landmarks:

                for hand_landmarks in results.multi_hand_landmarks:

                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS
                    )

                    detected_gesture = recognize_gesture(
                        hand_landmarks
                    )

            if detected_gesture != "UNKNOWN":

                if detected_gesture == candidate:
                    stable_frames += 1
                else:
                    candidate = detected_gesture
                    stable_frames = 1

                if stable_frames >= 8:

                    translated = GESTURES.get(
                        detected_gesture
                    )

                    if translated:

                        current_text = translated
                        now = time.time()

                        if detected_gesture != last_gesture:

                            if now - last_spoken >= 2:
                                speaker.say(translated)
                                speaker.runAndWait()
                                last_spoken = time.time()

                            last_gesture = detected_gesture

                        if now - last_saved >= 2:
                            save_translation(
                                detected_gesture,
                                translated
                            )
                            last_saved = now

            else:
                candidate = None
                stable_frames = 0

            # DISPLAY INTERFACE

            cv2.rectangle(
                frame,
                (0, 0),
                (frame.shape[1], 105),
                (25, 25, 25),
                -1
            )

            cv2.putText(
                frame,
                "SMART TRANSLATION SYSTEM",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

            cv2.putText(
                frame,
                "Gesture: " + detected_gesture,
                (20, 68),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                "Translation: " + current_text,
                (20, 145),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                "Q: Quit | S: Speak | C: Clear",
                (20, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1
            )

            cv2.imshow(
                "Smart Translation System",
                frame
            )

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

            elif key == ord("s"):
                speaker.say(current_text)
                speaker.runAndWait()

            elif key == ord("c"):
                current_text = "Show your hand to the camera"
                last_gesture = None

    camera.release()
    cv2.destroyAllWindows()
    connection.close()

    print("APPLICATION CLOSED")


if __name__ == "__main__":
    main()
