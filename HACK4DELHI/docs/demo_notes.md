# Smart Parking System – Demo Notes

## 1. Project Title
Smart Parking Capacity Enforcement System for Municipal Corporations

---

## 2. Problem Overview
Municipal parking lots are usually operated by private contractors.  
Many times, contractors park more vehicles than the approved capacity, which leads to traffic congestion, safety risks, revenue loss, and lack of accountability.

The existing system is mostly manual and does not provide real-time enforcement.

---

## 3. Proposed Solution
We developed an AI-based Smart Parking System that automatically:

- Detects vehicles using a camera
- Identifies vehicle ENTRY and EXIT
- Maintains a live vehicle count
- Enforces a maximum parking capacity
- Sends automatic email alerts to authorities when capacity is exceeded
- Displays live parking status for monitoring

The system is real-time, automated, and tamper-resistant.

---

## 4. System Components

### Camera Input
- Live CCTV / laptop webcam feed
- Continuous frame capture using OpenCV

### Vehicle Detection
- AI Model: YOLO11n
- Detects cars, bikes, buses, and trucks
- Implemented in vehicle_detector.py

### Entry / Exit Detection
- A virtual horizontal line is drawn on the screen
- Vehicle crossing direction decides:
  - ENTRY
  - EXIT
- Implemented in LineCrossing.py

### Vehicle Counter
- ENTRY increases count
- EXIT decreases count
- Count never goes negative
- Implemented in counter.py

### Capacity Enforcement
- Maximum capacity is predefined
- System checks for violations in real time
- Implemented in capacity_check.py

### Alert System
- Sends automatic email alerts when capacity is exceeded
- Uses secure Gmail SMTP with App Password
- Implemented in alert_manager.py

### Dashboard
- Shows current vehicle count
- Shows maximum capacity
- Displays NORMAL or OVER CAPACITY status
- Implemented in dashboard/app.py

---

## 5. Live Demo Flow

### Step 1: Start System
- Run main.py
- Camera feed opens
- Entry/Exit line is visible

### Step 2: Vehicle Entry
- Vehicle crosses the line in ENTRY direction
- Terminal prints ENTRY message
- Vehicle count increases on screen

### Step 3: Vehicle Exit
- Vehicle crosses back
- Terminal prints EXIT message
- Vehicle count decreases correctly

### Step 4: Capacity Violation
- Multiple vehicles enter
- When count exceeds capacity:
  - System detects violation
  - Email alert is sent automatically
  - On-screen warning turns red

---

## 6. Accuracy of the System
- Uses AI-based detection instead of manual counting
- Direction-based logic avoids double counting
- Fully automated, no human intervention
- Real-time processing ensures immediate enforcement

---

## 7. Benefits to Municipal Corporations
- Prevents illegal overparking
- Reduces traffic congestion
- Improves revenue transparency
- Enables real-time monitoring
- Improves accountability of contractors

---

## 8. Scalability and Future Scope
- Multiple parking gates
- Centralized city-wide dashboard
- Parking fee calculation based on duration
- SMS and WhatsApp alerts
- Cloud deployment
- Smart City integration

---

## 9. One-Line Summary
An AI-powered real-time parking enforcement system that detects vehicle entry and exit, prevents overcapacity, and automatically alerts municipal authorities.

---

## 10. Technology Stack
- Python
- OpenCV
- YOLO11n
- SMTP (Email Alerts)
- Streamlit Dashboard

---

## 11. Conclusion
This project demonstrates how AI and automation can be used to solve real-world urban infrastructure problems by improving efficiency, transparency, and governance.