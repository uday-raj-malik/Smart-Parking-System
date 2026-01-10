import re
import cv2
import easyocr
import os
import time
import json
import numpy as np
import requests
from datetime import datetime
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

def get_vehicle_identity(track_id, vehicle_plate_map):
    """
    Returns the best available identity for this vehicle.
    Plate number is preferred over track_id as it's a permanent identifier.
    """
    if track_id in vehicle_plate_map:
        return vehicle_plate_map[track_id]  # Use plate number as permanent ID
    return f"UNKNOWN_{track_id}"  # Temporary ID until plate is detected (matches CSV logger format)


def is_valid_plate(text):
    pattern = r'^[A-Z]{1}[0-9]{3}[A-Z]{2}$'
    return re.match(pattern, text)


# ---------------- MAIN ----------------
def main():

    # -------- CONFIG --------
    # Get the project root directory (parent of src/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    VEHICLE_MODEL_PATH = os.path.join(project_root, "models", "yolo11n.pt")
    PLATE_MODEL_PATH = os.path.join(project_root, "models", "plate_detector.pt")
    
    # Load config from config.json (created/updated by MCD UI)
    config_file_path = os.path.join(project_root, "config.json")
    MAX_CAPACITY = 2
    HOURLY_RATE = 50
    if os.path.exists(config_file_path):
        try:
            with open(config_file_path, 'r') as f:
                config = json.load(f)
                MAX_CAPACITY = config.get('max_capacity', 2)
                HOURLY_RATE = config.get('hourly_rate', 50)
            print(f"✅ Loaded config: Max Capacity={MAX_CAPACITY}, Hourly Rate=₹{HOURLY_RATE}")
        except Exception as e:
            print(f"⚠️ Error loading config: {e}, using defaults")
    else:
        print(f"⚠️ Config file not found, using defaults: Max Capacity={MAX_CAPACITY}, Hourly Rate=₹{HOURLY_RATE}")

    SENDER_EMAIL = "vk.meta.1092@gmail.com"
    SENDER_PASSWORD = "ldzr svoz qvhu cort"
    RECEIVER_EMAIL = "gaoka123789@gmail.com"
    
    # CSV logging configuration - create file with date/time
    start_time = datetime.now()
    csv_filename = f"parking_log_{start_time.strftime('%Y%m%d_%H%M%S')}.csv"
    CSV_LOG_PATH = os.path.join(project_root, csv_filename)

    CAMERA_INDEX = 0  # Change to 0 for default camera, or use video file path like "vid.mp4"
    USE_VIDEO_FILE = False  # Set to True and provide VIDEO_PATH to use video file instead
    VIDEO_PATH = os.path.join(project_root, "demo3.mp4")  # Path to video file
    SHOW_DISPLAY = True  # Set to False if OpenCV GUI is not available or for headless operation

    # -------- ALERT SYSTEM --------
    alert_manager = AlertManager(
        SENDER_EMAIL,
        SENDER_PASSWORD,
        RECEIVER_EMAIL
    )

    capacity_checker = CapacityChecker(MAX_CAPACITY, alert_manager)
    
    # -------- CSV LOGGER --------
    csv_logger = ParkingCSVLogger(CSV_LOG_PATH, hourly_rate=HOURLY_RATE, config_file_path=config_file_path)

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

    # Store detected plate per vehicle track_id: {track_id: plate_number}
    vehicle_plate_map = {}
    
    # Store track_id to temporary ID mapping (for vehicles without detected plates)
    track_to_temp_id = {}  # {track_id: "UNKNOWN_123"}
    
    # Store entry status using plate number (or temp ID) as key: {identity: {'plate': plate_number, 'entered': bool, 'entry_time': datetime, 'track_id': track_id}}
    vehicle_entry_status = {}  # Uses plate number or UNKNOWN_id as key

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

    # Check if OpenCV GUI is available
    gui_available = False
    if SHOW_DISPLAY:
        try:
            # Try to create and show a small test window to check GUI support
            test_img = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.imshow("test_window", test_img)
            cv2.waitKey(1)
            cv2.destroyWindow("test_window")
            gui_available = True
            print("✅ OpenCV GUI support detected")
        except (cv2.error, AttributeError, Exception) as e:
            print("⚠️ OpenCV GUI not available - running in headless mode")
            print(f"💡 Error: {str(e)}")
            print("💡 To fix this issue, reinstall opencv-python with GUI support:")
            print("   pip uninstall opencv-python opencv-python-headless")
            print("   pip install opencv-python")
            gui_available = False
            SHOW_DISPLAY = False
    
    print("✅ Smart Parking + ANPR System Running" + (" (Press 'q' to quit)" if gui_available else " (Headless mode)"))
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
            
            # Get or create identity for this vehicle (plate number preferred)
            plate_number = vehicle_plate_map.get(track_id, None)
            if plate_number:
                identity = plate_number  # Use plate number as permanent identifier
            else:
                # Use temporary ID if plate not detected yet (matches CSV logger format)
                if track_id not in track_to_temp_id:
                    track_to_temp_id[track_id] = f"UNKNOWN_{track_id}"
                identity = track_to_temp_id[track_id]
            
            event = line_cross.check(identity, cy)

            if event:
                if event == "ENTRY":
                    counter.process_event(event)
                    
                    # Check if this vehicle (by identity) has already entered
                    if identity in vehicle_entry_status and vehicle_entry_status[identity].get('entered', False):
                        print(f"⚠️ WARNING: {identity} is already recorded as entered!")
                        last_event_msg = f"{identity}: ENTRY DUPLICATE (Already entered)"
                    else:
                        # Log entry to CSV immediately (even without plate)
                        success, msg, entry_time = csv_logger.log_entry(plate_number=plate_number, track_id=track_id)
                        
                        if success:
                            vehicle_entry_status[identity] = {
                                'plate': plate_number,
                                'entered': True,
                                'entry_time': entry_time,
                                'track_id': track_id  # Keep track_id for reference
                            }
                            
                            # Check capacity and send alert with plate number and entry time
                            capacity_checker.check(
                                counter.get_count(),
                                plate_number=plate_number if plate_number else identity,
                                entry_time=entry_time
                            )
                            
                            if plate_number:
                                last_event_msg = f"{plate_number}: ENTRY | {entry_time.strftime('%H:%M:%S') if entry_time else ''}"
                            else:
                                last_event_msg = f"{identity}: ENTRY | {entry_time.strftime('%H:%M:%S') if entry_time else ''} (Plate detecting...)"
                        else:
                            last_event_msg = f"{identity}: ENTRY ERROR - {msg}"
                            # Still check capacity even if logging failed
                            capacity_checker.check(counter.get_count())
                
                elif event == "EXIT":
                    # Validate: Check if vehicle has really entered (using identity/plate number)
                    if identity not in vehicle_entry_status or not vehicle_entry_status[identity].get('entered', False):
                        print(f"⚠️ WARNING: {identity} trying to exit without entry record!")
                        last_event_msg = f"{identity}: EXIT REJECTED (No entry record)"
                        
                        # Send illegal exit alert via email
                        alert_manager.send_illegal_parking_alert(identity, datetime.now())
                        
                        # Also send to API for MCD UI display
                        try:
                            api_url = "http://localhost:5000/api/alerts/illegal-exit"
                            requests.post(api_url, json={
                                'plate_number': identity,
                                'exit_time': datetime.now().isoformat()
                            }, timeout=2)
                        except Exception as e:
                            print(f"⚠️ Could not send illegal exit alert to API: {e} (API may not be running)")
                    else:
                        counter.process_event(event)
                        
                        # Get plate number from entry status (might have been updated after entry)
                        entry_info = vehicle_entry_status[identity]
                        exit_plate_number = entry_info.get('plate') or plate_number
                        
                        # Log exit to CSV using the plate number from entry record
                        success, msg, exit_data = csv_logger.log_exit(
                            plate_number=exit_plate_number, 
                            track_id=entry_info.get('track_id', track_id)
                        )
                        
                        if success:
                            identifier = exit_plate_number if exit_plate_number else identity
                            last_event_msg = (f"{identifier}: EXIT | "
                                            f"Fare: ₹{exit_data['Fare (₹)']} | "
                                            f"Duration: {exit_data['Duration (hours)']:.2f}h")
                        else:
                            identifier = exit_plate_number if exit_plate_number else identity
                            last_event_msg = f"{identifier}: EXIT ERROR - {msg}"
                        
                        # Remove from entry status
                        if identity in vehicle_entry_status:
                            del vehicle_entry_status[identity]
                        # Clean up temp ID mapping if it exists
                        if track_id in track_to_temp_id:
                            del track_to_temp_id[track_id]
                
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
                                    
                                    # Check if this vehicle has already entered with a temporary ID
                                    temp_id = track_to_temp_id.get(track_id)
                                    if temp_id and temp_id in vehicle_entry_status:
                                        # Vehicle entered before plate was detected - migrate to plate-based tracking
                                        entry_info = vehicle_entry_status.pop(temp_id)  # Remove old temp entry
                                        
                                        # Update entry status with plate number as key
                                        vehicle_entry_status[plate_text] = {
                                            'plate': plate_text,
                                            'entered': entry_info.get('entered', True),
                                            'entry_time': entry_info.get('entry_time'),
                                            'track_id': track_id
                                        }
                                        
                                        # Update line crossing state to use plate number
                                        if temp_id in line_cross.states:
                                            line_cross.states[plate_text] = line_cross.states.pop(temp_id)
                                        
                                        # Update CSV with plate number
                                        old_identifier = f"UNKNOWN_{track_id}"
                                        entry_time = entry_info.get('entry_time')
                                        if entry_time:
                                            csv_logger.update_plate_number(old_identifier, plate_text, entry_time=entry_time)
                                            print(f"📝 Migrated entry record: {temp_id} -> {plate_text}")
                                            print(f"📝 Updated plate number in CSV: {old_identifier} -> {plate_text}")
                                        
                                        # Clean up temp ID
                                        del track_to_temp_id[track_id]
                                    else:
                                        # Vehicle hasn't entered yet, just store the plate
                                        print(f"✅ Plate {plate_text} stored for Vehicle ID: {track_id} (awaiting entry)")
                                else:
                                    print(f"⚠️ Invalid plate format: {plate_text}")
                except Exception as e:
                    print(f"⚠️ Error during plate detection for vehicle {track_id}: {e}")

            # ---------- DRAW PLATE TEXT (Display prominently when detected) ----------
            # Get identity for display
            plate_number = vehicle_plate_map.get(track_id, None)
            if plate_number:
                identity = plate_number
            else:
                identity = track_to_temp_id.get(track_id, f"UNKNOWN_{track_id}")
            
            # Display plate number if detected, otherwise show identity
            if plate_number:
                cv2.putText(frame, f"Plate: {plate_number}",
                            (x1, y2 + 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            (0, 255, 255), 2)
            else:
                cv2.putText(frame, f"ID: {identity}",
                            (x1, y2 + 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (128, 128, 128), 2)
            
            # Show entry status if available (check by identity, not track_id)
            if identity in vehicle_entry_status and vehicle_entry_status[identity].get('entered', False):
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
        csv_filename_display = os.path.basename(CSV_LOG_PATH)
        cv2.putText(frame, f"Log: {csv_filename_display}", (width - 300, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Display hourly rate
        rate_text = f"Rate: ₹{HOURLY_RATE}/hr"
        cv2.putText(frame, rate_text, (width - 250, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Display frame if GUI is available
        if SHOW_DISPLAY and gui_available:
            try:
                cv2.imshow("Smart Parking with ANPR", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except cv2.error as e:
                print(f"⚠️ Display error: {e}")
                print("⚠️ Switching to headless mode...")
                gui_available = False
                SHOW_DISPLAY = False
        else:
            # Headless mode: process frames but don't display
            # Add a small delay to avoid maxing out CPU
            time.sleep(0.033)  # ~30 FPS

    cap.release()
    if gui_available:
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass  # Ignore errors during cleanup
    
    # -------- SEND CSV REPORT AT END --------
    print("\n" + "="*50)
    print("📊 Program ending - Sending CSV report...")
    print("="*50)
    
    if os.path.exists(CSV_LOG_PATH):
        success = alert_manager.send_csv_report(CSV_LOG_PATH)
        if success:
            print(f"✅ CSV report sent successfully: {os.path.basename(CSV_LOG_PATH)}")
        else:
            print(f"⚠️ Failed to send CSV report, but file is saved at: {CSV_LOG_PATH}")
    else:
        print(f"⚠️ CSV file not found: {CSV_LOG_PATH}")
    
    print("👋 Program terminated.")


if __name__ == "__main__":
    main()
