import cv2
from detection.vehicle_detector import VehicleDetector
from detection.LineCrossing import LineCrossing
from logic.counter import VehicleCounter
from logic.capacity_check import CapacityChecker
from alerts.alert_manager import AlertManager

# --- NEW IMPORT FOR DEEPSORT ---
from deep_sort_realtime.deepsort_tracker import DeepSort


def main():
    # -------- CONFIG --------
    MODEL_PATH = "models/yolo11n.pt"
    MAX_CAPACITY = 5
    SENDER_EMAIL = "vk.meta.1092@gmail.com"
    SENDER_PASSWORD = "ldzr svoz qvhu cort"
    RECEIVER_EMAIL = "gaoka123789@gmail.com"

    # -------- SETUP ALERT SYSTEM --------
    alert_manager = AlertManager(SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL)
    capacity_checker = CapacityChecker(MAX_CAPACITY, alert_manager)

    # -------- INITIALIZE AI & LOGIC --------
    detector = VehicleDetector(MODEL_PATH)
    counter = VehicleCounter(MAX_CAPACITY)

    # --- INITIALIZE DEEPSORT TRACKER ---
    # max_age=30: If a car disappears, remember it for 30 frames before deleting ID
    object_tracker = DeepSort(
        max_age=30,
        n_init=2,
        nms_max_overlap=1.0,
        max_cosine_distance=0.3,
        nn_budget=None,
        override_track_class=None,
        embedder="mobilenet",
        half=True,
        bgr=True,
        embedder_gpu=True
    )

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

    print("✅ System Ready with DeepSORT. Press 'q' to quit.\n")

    last_event_msg = ""
    event_timer = 0

    while True:
        ret, frame = cap.read()
        if not ret: break

        # 1. Get Detections from YOLO
        # We expect detector.detect to return: (x1, y1, x2, y2, label, conf, raw_id)
        detections = detector.detect(frame)

        # 2. Format for DeepSORT
        # DeepSORT expects: [[left, top, w, h], confidence, detection_class]
        deepsort_inputs = []
        for (x1, y1, x2, y2, label, conf, _) in detections:
            w = x2 - x1
            h = y2 - y1
            deepsort_inputs.append([[x1, y1, w, h], conf, label])

        # 3. Update Tracker
        # This is where the magic happens. The tracker figures out the IDs.
        tracks = object_tracker.update_tracks(deepsort_inputs, frame=frame)

        # Draw Line
        cv2.line(frame, (0, line_y), (width, line_y), (0, 0, 255), 2)

        # 4. Loop over TRACKS (not raw detections)
        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id

            # Get the bounding box from the tracker
            ltrb = track.to_ltrb()  # returns left, top, right, bottom
            x1, y1, x2, y2 = int(ltrb[0]), int(ltrb[1]), int(ltrb[2]), int(ltrb[3])

            cy = int((y1 + y2) / 2)
            cx = int((x1 + x2) / 2)

            # Check for Crossing Event
            event = line_cross.check(track_id, cy)

            if event:
                counter.process_event(event)
                capacity_checker.check(counter.get_count())

                last_event_msg = f"Vehicle {track_id}: {event}"
                event_timer = 30
                print(f"📢 {last_event_msg}")

            # Draw DeepSORT bounding boxes (usually smoother)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)  # Blue box for tracked
            cv2.putText(frame, f"ID:{track_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # VISUAL FEEDBACK
        if event_timer > 0:
            cv2.putText(frame, last_event_msg, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            event_timer -= 1

        # DISPLAY LIVE COUNT
        count_text = f"Parking: {counter.get_count()} / {MAX_CAPACITY}"
        color = (0, 0, 255) if counter.get_count() >= MAX_CAPACITY else (0, 255, 0)
        cv2.putText(frame, count_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        cv2.imshow("Smart Parking (DeepSORT)", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()