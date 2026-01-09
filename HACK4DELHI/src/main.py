import re
import cv2
import easyocr
import os
from ultralytics import YOLO

from detection.vehicle_detector import VehicleDetector
from detection.LineCrossing import LineCrossing
from logic.counter import VehicleCounter
from logic.capacity_check import CapacityChecker
from logic.csv_logger import ParkingCSVLogger
from alerts.alert_manager import AlertManager


# ---------------- UTILS ----------------
def clean_plate_text(text):
    text = text.upper()
    text = re.sub(r'[^A-Z0-9]', '', text)
    return text


def is_valid_plate(text):
    pattern = r'^[A-Z]{2}[0-9]{5}$'
    return re.match(pattern, text)


# ---------------- MAIN ----------------
def main():

    # -------- CONFIG --------
    # Get the project root directory (parent of src/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    VEHICLE_MODEL_PATH = os.path.join(project_root, "models", "yolo11n.pt")
    PLATE_MODEL_PATH = os.path.join(project_root, "models", "plate_detector.pt")
    MAX_CAPACITY = 2
    HOURLY_RATE = 50  # Parking fee per hour in rupees

    SENDER_EMAIL = "vk.meta.1092@gmail.com"
    SENDER_PASSWORD = "ldzr svoz qvhu cort"
    RECEIVER_EMAIL = "gaoka123789@gmail.com"
    
    # CSV logging configuration
    CSV_LOG_PATH = os.path.join(project_root, "parking_logs.csv")

    CAMERA_INDEX = 1  # Change to 0 for default camera, or use video file path like "vid.mp4"
    USE_VIDEO_FILE = True  # Set to True and provide VIDEO_PATH to use video file instead
    VIDEO_PATH = os.path.join(project_root, "vid3_.mp4")  # Path to video file

    # -------- ALERT SYSTEM --------
    alert_manager = AlertManager(
        SENDER_EMAIL,
        SENDER_PASSWORD,
        RECEIVER_EMAIL
    )

    capacity_checker = CapacityChecker(MAX_CAPACITY, alert_manager)
    
    # -------- CSV LOGGER --------
    csv_logger = ParkingCSVLogger(CSV_LOG_PATH, hourly_rate=HOURLY_RATE)

    # -------- AI MODELS --------
    print(f"📦 Loading vehicle model from: {VEHICLE_MODEL_PATH}")
    if not os.path.exists(VEHICLE_MODEL_PATH):
        print(f"❌ Error: Vehicle model not found at {VEHICLE_MODEL_PATH}")
        return
    vehicle_detector = VehicleDetector(VEHICLE_MODEL_PATH)
    print("✅ Vehicle detector loaded")
    
    print(f"📦 Loading plate detector from: {PLATE_MODEL_PATH}")
    if not os.path.exists(PLATE_MODEL_PATH):
        print(f"❌ Error: Plate model not found at {PLATE_MODEL_PATH}")
        return
    plate_detector = YOLO(PLATE_MODEL_PATH)
    print("✅ Plate detector loaded")
    
    print("⏳ Loading OCR reader... (this may take a moment)")
    ocr_reader = easyocr.Reader(['en'], gpu=False)
    print("✅ OCR reader loaded")

    counter = VehicleCounter(MAX_CAPACITY)

    # Store detected plate per vehicle ID
    vehicle_plate_map = {}
    
    # Store vehicle ID to plate mapping for tracking entry/exit
    vehicle_entry_status = {}  # {track_id: {'plate': plate_number, 'entered': bool}}

    # -------- CAMERA/VIDEO --------
    if USE_VIDEO_FILE:
        print(f"📹 Using video file: {VIDEO_PATH}")
        if not os.path.exists(VIDEO_PATH):
            print(f"❌ Error: Video file not found at {VIDEO_PATH}")
            return
        cap = cv2.VideoCapture(VIDEO_PATH)
    else:
        print(f"📹 Using camera index: {CAMERA_INDEX}")
        cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f"❌ Error: Cannot open {'video file' if USE_VIDEO_FILE else 'camera'}")
        if not USE_VIDEO_FILE:
            print("💡 Tip: Try changing CAMERA_INDEX to 0 or check if camera is connected")
        return

    ret, frame = cap.read()
    if not ret:
        print("❌ Error: Could not read first frame")
        return

    height, width, _ = frame.shape
    line_y = height // 2
    line_cross = LineCrossing(line_y)

    print("✅ Smart Parking + ANPR System Running (Press 'q' to quit)")
    print(f"📝 CSV logs will be saved to: {CSV_LOG_PATH}")
    print(f"💰 Hourly rate: ₹{HOURLY_RATE}/hour")

    last_event_msg = ""
    event_timer = 0

    # -------- MAIN LOOP --------
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        detections = vehicle_detector.detect(frame)
        
        # Debug: Print detection count
        if len(detections) > 0:
            print(f"🔍 Detected {len(detections)} vehicle(s)")

        # Draw entry/exit line
        cv2.line(frame, (0, line_y), (width, line_y), (0, 0, 255), 2)

        for (x1, y1, x2, y2, label, conf, track_id) in detections:
            
            # Skip if track_id is None (no tracking available yet)
            if track_id is None:
                continue

            # ---------- LINE CROSSING ----------
            cy = (y1 + y2) // 2
            event = line_cross.check(track_id, cy)

            if event:
                # Get plate number for this vehicle (if available)
                plate_number = vehicle_plate_map.get(track_id, None)
                
                if event == "ENTRY":
                    counter.process_event(event)
                    capacity_checker.check(counter.get_count())
                    
                    # Log entry to CSV if plate is detected
                    if plate_number:
                        success, msg, entry_time = csv_logger.log_entry(plate_number)
                        if success:
                            vehicle_entry_status[track_id] = {
                                'plate': plate_number,
                                'entered': True
                            }
                            last_event_msg = f"{plate_number}: ENTRY | {entry_time.strftime('%H:%M:%S') if entry_time else ''}"
                        else:
                            last_event_msg = f"Vehicle {track_id}: ENTRY (No Plate)"
                    else:
                        # Vehicle entered but plate not detected yet
                        if track_id not in vehicle_entry_status:
                            vehicle_entry_status[track_id] = {'plate': None, 'entered': True}
                        last_event_msg = f"Vehicle {track_id}: ENTRY (Plate detecting...)"
                
                elif event == "EXIT":
                    # Validate: Check if vehicle has really entered
                    if track_id not in vehicle_entry_status or not vehicle_entry_status[track_id].get('entered', False):
                        print(f"⚠️ WARNING: Vehicle {track_id} trying to exit without entry record!")
                        last_event_msg = f"Vehicle {track_id}: EXIT REJECTED (No entry record)"
                    else:
                        counter.process_event(event)
                        
                        # Try to get plate number from entry status if not in current map
                        if not plate_number and track_id in vehicle_entry_status:
                            plate_number = vehicle_entry_status[track_id].get('plate', None)
                        
                        # Log exit to CSV if plate is detected
                        if plate_number:
                            success, msg, exit_data = csv_logger.log_exit(plate_number)
                            if success:
                                last_event_msg = (f"{plate_number}: EXIT | "
                                                f"Fare: ₹{exit_data['Fare (₹)']} | "
                                                f"Duration: {exit_data['Duration (hours)']:.2f}h")
                                # Remove from entry status
                                if track_id in vehicle_entry_status:
                                    del vehicle_entry_status[track_id]
                            else:
                                last_event_msg = f"{plate_number}: EXIT ERROR - {msg}"
                        else:
                            # Exit without plate - still process counter but warn
                            print(f"⚠️ WARNING: Vehicle {track_id} exiting without plate detection!")
                            last_event_msg = f"Vehicle {track_id}: EXIT (No Plate - Not logged)"
                            if track_id in vehicle_entry_status:
                                del vehicle_entry_status[track_id]
                
                event_timer = 30
                print(f"📢 {last_event_msg}")

            # ---------- VEHICLE BOX ----------
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Display vehicle ID
            cv2.putText(frame, f"ID:{track_id}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # ---------- PLATE DETECTION (ONCE PER VEHICLE) ----------
            if track_id not in vehicle_plate_map:
                # Validate vehicle ROI bounds
                h, w = frame.shape[:2]
                x1_clamped = max(0, min(x1, w - 1))
                y1_clamped = max(0, min(y1, h - 1))
                x2_clamped = max(0, min(x2, w - 1))
                y2_clamped = max(0, min(y2, h - 1))
                
                # Check if ROI is valid
                if x2_clamped <= x1_clamped or y2_clamped <= y1_clamped:
                    continue
                
                vehicle_roi = frame[y1_clamped:y2_clamped, x1_clamped:x2_clamped]
                
                # Check if ROI is too small
                roi_h, roi_w = vehicle_roi.shape[:2]
                if roi_h < 30 or roi_w < 30:
                    continue

                try:
                    plate_results = plate_detector(vehicle_roi, conf=0.4, verbose=False)

                    for result in plate_results:
                        for box in result.boxes:
                            px1, py1, px2, py2 = map(int, box.xyxy[0])
                            
                            # Clamp plate coordinates to ROI bounds
                            px1 = max(0, min(px1, roi_w - 1))
                            py1 = max(0, min(py1, roi_h - 1))
                            px2 = max(0, min(px2, roi_w - 1))
                            py2 = max(0, min(py2, roi_h - 1))
                            
                            if px2 <= px1 or py2 <= py1:
                                continue

                            plate_img = vehicle_roi[py1:py2, px1:px2]
                            if plate_img.size == 0:
                                continue
                            
                            # Validate plate image size
                            if plate_img.shape[0] < 10 or plate_img.shape[1] < 10:
                                continue

                            ocr_result = ocr_reader.readtext(plate_img)

                            if ocr_result:
                                raw_text = ocr_result[0][1]
                                plate_text = clean_plate_text(raw_text)
                                
                                print(f"🔍 Raw OCR: {raw_text} -> Cleaned: {plate_text}")

                                if is_valid_plate(plate_text):
                                    vehicle_plate_map[track_id] = plate_text
                                    print(f"🚗 Plate Detected: {plate_text} for Vehicle ID: {track_id}")
                                    
                                    # If vehicle has already entered, update entry status with plate
                                    if track_id in vehicle_entry_status:
                                        vehicle_entry_status[track_id]['plate'] = plate_text
                                        # Log entry if vehicle already crossed line but plate wasn't detected then
                                        if vehicle_entry_status[track_id].get('entered', False):
                                            success, msg, entry_time = csv_logger.log_entry(plate_text)
                                            if success:
                                                print(f"📝 Late entry log: {msg}")
                                else:
                                    print(f"⚠️ Invalid plate format: {plate_text}")
                except Exception as e:
                    print(f"⚠️ Error during plate detection for vehicle {track_id}: {e}")

            # ---------- DRAW PLATE TEXT (Display prominently when detected) ----------
            if track_id in vehicle_plate_map:
                plate_number = vehicle_plate_map[track_id]
                
                # Display plate number prominently below vehicle
                cv2.putText(frame, f"Plate: {plate_number}",
                            (x1, y2 + 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            (0, 255, 255), 2)
                
                # Show entry status if available
                if track_id in vehicle_entry_status and vehicle_entry_status[track_id].get('entered', False):
                    status_text = "PARKED"
                    status_color = (0, 255, 0)  # Green
                    cv2.putText(frame, status_text,
                                (x1, y2 + 45),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                status_color, 2)

        # ---------- EVENT MESSAGE ----------
        if event_timer > 0:
            cv2.putText(frame, last_event_msg, (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 255, 255), 2)
            event_timer -= 1

        # ---------- COUNT DISPLAY ----------
        count_text = f"Parking: {counter.get_count()} / {MAX_CAPACITY}"
        color = (0, 0, 255) if counter.get_count() >= MAX_CAPACITY else (0, 255, 0)

        cv2.putText(frame, count_text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        # Display CSV log file location (top right)
        csv_info = "Log: parking_logs.csv"
        cv2.putText(frame, csv_info, (width - 250, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Display hourly rate
        rate_text = f"Rate: ₹{HOURLY_RATE}/hr"
        cv2.putText(frame, rate_text, (width - 250, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("Smart Parking with ANPR", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
