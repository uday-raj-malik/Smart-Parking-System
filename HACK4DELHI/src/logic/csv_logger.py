import pandas as pd
import os
from datetime import datetime
from typing import Optional, Tuple, Dict


class ParkingCSVLogger:
    """
    Manages CSV logging of parking entries and exits with fare calculation.
    """
    
    def __init__(self, csv_path: str, hourly_rate: float = 50.0):
        """
        Initialize CSV logger.
        
        Args:
            csv_path: Path to CSV file
            hourly_rate: Parking fee per hour in rupees
        """
        self.csv_path = csv_path
        self.hourly_rate = hourly_rate
        
        # Track active parking sessions: {plate_number: entry_datetime}
        self.active_sessions: Dict[str, datetime] = {}
        
        # Initialize CSV file with headers if it doesn't exist
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Create CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.csv_path):
            df = pd.DataFrame(columns=[
                'Entry Time',
                'Exit Time',
                'Plate Number',
                'Duration (hours)',
                'Fare (₹)'
            ])
            df.to_csv(self.csv_path, index=False)
            print(f"📝 Created new CSV log file: {self.csv_path}")
    
    def log_entry(self, plate_number: str) -> Tuple[bool, str, Optional[datetime]]:
        """
        Log vehicle entry.
        
        Args:
            plate_number: Vehicle license plate number
            
        Returns:
            Tuple of (success, message, entry_datetime)
        """
        if not plate_number:
            return False, "No plate number provided", None
        
        # Check if vehicle is already parked
        if plate_number in self.active_sessions:
            entry_time = self.active_sessions[plate_number]
            return False, f"⚠️ {plate_number} is already parked (entered at {entry_time.strftime('%H:%M:%S')})", entry_time
        
        # Record entry
        entry_time = datetime.now()
        self.active_sessions[plate_number] = entry_time
        
        return True, f"✅ Entry logged: {plate_number} at {entry_time.strftime('%H:%M:%S')}", entry_time
    
    def log_exit(self, plate_number: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Log vehicle exit and calculate fare.
        
        Args:
            plate_number: Vehicle license plate number
            
        Returns:
            Tuple of (success, message, exit_data_dict)
        """
        if not plate_number:
            return False, "No plate number provided", None
        
        # Check if vehicle has entered
        if plate_number not in self.active_sessions:
            return False, f"⚠️ {plate_number} has no entry record! Cannot log exit.", None
        
        # Get entry time and remove from active sessions
        entry_time = self.active_sessions.pop(plate_number)
        exit_time = datetime.now()
        
        # Calculate duration
        duration = exit_time - entry_time
        duration_hours = duration.total_seconds() / 3600.0
        
        # Calculate fare (minimum charge for 1 hour, then hourly rate)
        if duration_hours < 1.0:
            fare = self.hourly_rate  # Minimum 1 hour charge
        else:
            # Round up to nearest hour
            fare = self.hourly_rate * (int(duration_hours) + (1 if duration_hours % 1 > 0 else 0))
        
        # Prepare data for CSV
        exit_data = {
            'Entry Time': entry_time.strftime('%Y-%m-%d %H:%M:%S'),
            'Exit Time': exit_time.strftime('%Y-%m-%d %H:%M:%S'),
            'Plate Number': plate_number,
            'Duration (hours)': round(duration_hours, 2),
            'Fare (₹)': round(fare, 2)
        }
        
        # Append to CSV
        try:
            df = pd.read_csv(self.csv_path)
            new_row = pd.DataFrame([exit_data])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(self.csv_path, index=False)
            
            message = (f"✅ Exit logged: {plate_number} | "
                      f"Duration: {duration_hours:.2f}h | "
                      f"Fare: ₹{fare:.2f}")
            
            return True, message, exit_data
            
        except Exception as e:
            return False, f"❌ Error writing to CSV: {str(e)}", None
    
    def get_active_parking_count(self) -> int:
        """Get count of currently parked vehicles."""
        return len(self.active_sessions)
    
    def get_active_plates(self) -> list:
        """Get list of currently parked vehicle plates."""
        return list(self.active_sessions.keys())
