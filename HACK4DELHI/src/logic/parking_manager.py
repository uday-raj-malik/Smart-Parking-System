import time
from datetime import datetime


class ParkingManager:
    def __init__(self, hourly_rate=50):
        self.hourly_rate = hourly_rate
        # Database to store active parking sessions
        # Format: { "DL3CAM1234": timestamp }
        self.active_sessions = {}

    def register_entry(self, plate_number):
        if not plate_number:
            return "No Plate Detected"

        if plate_number in self.active_sessions:
            return f"⚠️ {plate_number} is already inside!"

        self.active_sessions[plate_number] = time.time()
        return f"🎟️ Ticket Issued: {plate_number} at {datetime.now().strftime('%H:%M')}"

    def register_exit(self, plate_number):
        if not plate_number:
            return "No Plate Detected"

        if plate_number not in self.active_sessions:
            return f"⚠️ {plate_number} entry record not found!"

        # Calculate duration
        start_time = self.active_sessions.pop(plate_number)
        duration_sec = time.time() - start_time

        # Calculate price (For demo: 1 sec = 1 hour)
        price = max(10, int(duration_sec * self.hourly_rate))

        return f"💰 RECEIPT: {plate_number} | Pay: ₹{price}"