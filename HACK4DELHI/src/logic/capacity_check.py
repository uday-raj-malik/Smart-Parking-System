
import sys
import os

# FIX: Append the path directly. Do not use dirname() on a hardcoded string.
sys.path.append(r"C:\Users\ANURAG\HACK4DELHI\src")

# Now this will work because 'src' is in the path
from alerts.alert_manager import AlertManager

class CapacityChecker:
    def __init__(self, max_capacity, alert_manager):
        self.max_capacity = max_capacity
        self.alert_manager = alert_manager
        self.alert_triggered = False

    def check(self, current_count):
        if current_count > self.max_capacity:
            if not self.alert_triggered:
                print("🚨 MCD ALERT: Parking capacity exceeded!")
                self.alert_manager.send_capacity_alert(
                    current_count, self.max_capacity
                )
                self.alert_triggered = True
            return True

        self.alert_triggered = False
        return False