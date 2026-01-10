from datetime import datetime

class CapacityChecker:
    def __init__(self, max_capacity, alert_manager):
        self.max_capacity = max_capacity
        self.alert_manager = alert_manager

    def check(self, current_count, plate_number=None, entry_time=None):
        """
        Check if capacity is exceeded and send alert.
        
        Args:
            current_count: Current number of vehicles parked
            plate_number: Plate number of vehicle that caused exceed (optional)
            entry_time: Entry time of vehicle (optional)
        """
        if current_count > self.max_capacity:
            print("🚨 MCD ALERT: Parking capacity exceeded!")
            self.alert_manager.send_capacity_alert(
                current_count, 
                self.max_capacity,
                plate_number=plate_number,
                entry_time=entry_time
            )
            return True
        return False