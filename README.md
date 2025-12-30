Smart Parking Capacity Enforcement System
Overview
The Smart Parking Capacity Enforcement System is an AI-based solution designed to monitor parking lots in real time, prevent overcapacity violations, and improve accountability for Municipal Corporations.

The system automatically detects vehicles, identifies entry and exit events, maintains a live vehicle count, enforces parking capacity limits, and sends automatic alerts to authorities when violations occur.

Problem Statement
Municipal parking areas are often managed by private contractors.
Many contractors exceed the permitted parking capacity to increase revenue, leading to:

Traffic congestion
Safety hazards
Revenue loss for authorities
Lack of transparency and enforcement
Current systems rely on manual checks, which are slow, error-prone, and easy to manipulate.

Solution
This project provides a real-time, automated, and tamper-resistant parking enforcement system that:

Detects vehicles using AI
Automatically counts vehicles entering and exiting
Enforces a predefined parking capacity
Sends email alerts to authorities when capacity is exceeded
Displays live parking status for monitoring
Key Features
Real-time vehicle detection using YOLO11n
Automatic ENTRY and EXIT detection using line-crossing logic
Live vehicle counting with capacity enforcement
Email alerts for capacity violations
On-screen visual feedback
Dashboard for monitoring parking status
Modular and scalable system design
System Architecture
The system follows this pipeline:

Camera captures live video
YOLO11n detects vehicles in each frame
Line crossing logic determines ENTRY or EXIT
Vehicle counter updates current count
Capacity checker detects violations
Email alert is sent to authorities
Dashboard displays live status
How It Works
The camera continuously captures frames.
Vehicles are detected using YOLO11n.
A virtual line determines whether a vehicle is entering or exiting.
The system updates the vehicle count accordingly.
If the count exceeds the allowed capacity:
A violation is detected
An email alert is sent automatically
Live status is displayed on screen and dashboard.
Installation and Setup
Prerequisites
Python 3.8 or higher
Webcam or CCTV camera
Internet connection (for email alerts)
Install Dependencies
pip install -r requirements.txt
