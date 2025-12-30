import cv2
from detection.vehicle_detector import VehicleDetector
from detection.LineCrossing import LineCrossing
from logic.counter import VehicleCounter
from logic.capacity_check import CapacityChecker
from alerts.alert_manager import AlertManager

def main():
    # -------- CONFIG --------
    MODEL_PATH = "models/yolo11n.pt"
    MAX_CAPACITY = 5
    SENDER_EMAIL = "vk.meta.1092@gmail.com"
    SENDER_PASSWORD = "ldzr svoz qvhu cort"
    RECEIVER_EMAIL = "gaoka123789@gmail.com"

    # -------- SETUP ALERT SYSTEM --------
    # 1. Create the Alert Manager
    alert_manager = AlertManager(
        SENDER_EMAIL,
        SENDER_PASSWORD,
        RECEIVER_EMAIL
    )

    # 2. Create the Capacity Checker (Pass the alert_manager here)
    capacity_checker = CapacityChecker(MAX_CAPACITY, alert_manager)

    # -------- INITIALIZE AI & LOGIC --------
    detector = VehicleDetector(MODEL_PATH)
    counter = VehicleCounter(MAX_CAPACITY)

    # [REMOVED DUPLICATE LINE] The line that was crashing the code was here.

    # Start Camera
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("❌ Error: Cannot open video")
        return

    # Line Setup
    ret, frame = cap.read()
    if not ret: return
    height, width, _ = frame.shape
    line_y = height // 2
    line_cross = LineCrossing(line_y)

    print("✅ System Ready. Press 'q' to quit.\n")

    # To keep the "Entry/Exit" message on screen for a moment
    last_event_msg = ""
    event_timer = 0

    while True:
        ret, frame = cap.read()
        if not ret: break

        detections = detector.detect(frame)

        # Draw Line
        cv2.line(frame, (0, line_y), (width, line_y), (0, 0, 255), 2)

        for (x1, y1, x2, y2, label, conf, track_id) in detections:
            cy = int((y1 + y2) / 2)
            cx = int((x1 + x2) / 2)

            # Check for Crossing Event
            event = line_cross.check(track_id, cy)

            if event:
                # 3. Process Event (Update Count)
                counter.process_event(event)

                # 4. Check Capacity (Triggers Email if Full)
                capacity_checker.check(counter.get_count())

                # 5. Visual Feedback
                last_event_msg = f"Vehicle {track_id}: {event}"
                event_timer = 30  # Show message for 30 frames
                print(f"📢 {last_event_msg}")

            # Draw normal bounding boxes
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID:{track_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # VISUAL FEEDBACK (Fade out logicq)
        if event_timer > 0:
            cv2.putText(frame, last_event_msg, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            event_timer -= 1

        # DISPLAY LIVE COUNT ON SCREEN
        count_text = f"Parking: {counter.get_count()} / {MAX_CAPACITY}"

        # Change color to RED if full, GREEN otherwise
        color = (0, 0, 255) if counter.get_count() >= MAX_CAPACITY else (0, 255, 0)

        cv2.putText(frame, count_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        cv2.imshow("Smart Parking", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()