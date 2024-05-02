import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import mediapipe as mp
import pyautogui

# Initialize OpenCV camera
cap = cv2.VideoCapture(0)

# Create a Tkinter window
window = tk.Tk()
window.title("Hand Gesture Control")

# Create a canvas to display the video feed
canvas = tk.Canvas(window, width=640, height=480)
canvas.pack()

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

# Constants for gesture detection
GESTURE_AREA_TOP = 50
GESTURE_AREA_BOTTOM = 450
GESTURE_AREA_LEFT = 50
GESTURE_AREA_RIGHT = 590

# Flag to track if fingers are close together
fingers_close = False

# List to store hand positions history for scrolling gesture
hand_positions_history = []


def detect_hands(frame):
    # Convert the BGR frame to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame with MediaPipe Hands
    results = hands.process(rgb_frame)

    # Draw landmarks on the frame and get hand positions
    hand_positions = []
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            for landmark in hand_landmarks.landmark:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                hand_positions.append((x, y))
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

    return frame, hand_positions


def map_position(hand_position):
    width, height = pyautogui.size()
    mapped_x = int(hand_position[0] * width / (GESTURE_AREA_RIGHT - GESTURE_AREA_LEFT))
    mapped_y = int(hand_position[1] * height / (GESTURE_AREA_BOTTOM - GESTURE_AREA_TOP))
    return mapped_x, mapped_y


def perform_mouse_action(action):
    if action == "left_click":
        pyautogui.click(button='left')
    elif action == "right_click":
        pyautogui.click(button='right')
    elif action == "scroll_up":
        pyautogui.scroll(100)  # Scroll up
    elif action == "scroll_down":
        pyautogui.scroll(-100)  # Scroll down
    elif action == "alt_tab":
        pyautogui.hotkey('alt', 'tab')  # Alt + Tab
    elif action == "alt_f4":
        pyautogui.hotkey('alt', 'f4')  # Alt + F4


def update_video():
    global fingers_close, hand_positions_history
    ret, frame = cap.read()
    if ret:
        frame = cv2.flip(frame, 1)
        frame_with_hands, hand_positions = detect_hands(frame)

        # Check if thumb and index finger are close together for left-click
        if len(hand_positions) >= 2:
            thumb_x, thumb_y = hand_positions[4]  # Thumb landmark
            index_x, index_y = hand_positions[8]  # Index finger landmark
            if abs(thumb_x - index_x) < 30 and abs(thumb_y - index_y) < 30:
                if not fingers_close:
                    perform_mouse_action("left_click")
                    fingers_close = True
            else:
                fingers_close = False

            # Check if thumb touches pinky finger for scrolling down
            pinky_x, pinky_y = hand_positions[20]  # Pinky finger landmark
            if abs(thumb_x - pinky_x) < 30 and abs(thumb_y - pinky_y) < 30:
                perform_mouse_action("scroll_down")

            # Check if ring finger touches thumb for scrolling up
            ring_x, ring_y = hand_positions[16]  # Ring finger landmark
            if abs(ring_x - thumb_x) < 30 and abs(ring_y - thumb_y) < 30:
                perform_mouse_action("scroll_up")

            # Check if thumb and middle finger are close together for right-click
            middle_x, middle_y = hand_positions[12]  # Middle finger landmark
            if abs(thumb_x - middle_x) < 30 and abs(thumb_y - middle_y) < 30:
                perform_mouse_action("right_click")

            # Check if tip of index and middle finger touch for Alt + Tab
            if abs(index_x - middle_x) < 20 and abs(index_y - middle_y) < 20:
                perform_mouse_action("alt_tab")

            # Check if middle or ring finger touches wrist for Alt + F4
            wrist_x, wrist_y = hand_positions[0]  # Wrist landmark
            middle_tip_x, middle_tip_y = hand_positions[12]  # Middle finger tip landmark
            ring_tip_x, ring_tip_y = hand_positions[16]  # Ring finger tip landmark
            if (abs(middle_tip_x - wrist_x) < 30 and abs(middle_tip_y - wrist_y) < 30) or \
                    (abs(ring_tip_x - wrist_x) < 30 and abs(ring_tip_y - wrist_y) < 30):
                perform_mouse_action("alt_f4")

        # Move the mouse based on hand positions
        if hand_positions:
            mapped_x, mapped_y = map_position(hand_positions[0])
            pyautogui.moveTo(mapped_x, mapped_y, duration=0.01)  # Reduced duration for faster movement

        frame_rgb = cv2.cvtColor(frame_with_hands, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img_tk = ImageTk.PhotoImage(image=img)
        canvas.img_tk = img_tk
        canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)

    # Schedule the next update with reduced delay (e.g., 1 ms)
    window.after(1, update_video)  # Reduced delay for faster refresh rate


# Start the Tkinter event loop
window.after(1, update_video)  # Start the update_video loop with reduced delay
window.mainloop()

# Release the camera
cap.release()
