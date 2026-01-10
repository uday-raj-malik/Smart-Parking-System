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
    
    def log_entry(self, plate_number: str = None, track_id: int = None) -> Tuple[bool, str, Optional[datetime]]:
        """
        Log vehicle entry immediately to CSV.
        
        Args:
            plate_number: Vehicle license plate number (optional)
            track_id: Vehicle tracking ID (used if plate not available)
            
        Returns:
            Tuple of (success, message, entry_datetime)
        """
        # Use plate number if available, otherwise use track_id
        identifier = plate_number if plate_number else (f"UNKNOWN_{track_id}" if track_id else "UNKNOWN")
        
        # Check if vehicle is already parked (has active session with no exit)
        if identifier in self.active_sessions:
            entry_time = self.active_sessions[identifier]
            # Also check CSV to make sure there's no duplicate entry
            try:
                df = pd.read_csv(self.csv_path)
                existing = df[(df['Plate Number'] == identifier) & (df['Exit Time'] == '')]
                if not existing.empty:
                    return False, f"⚠️ {identifier} is already parked (entered at {entry_time.strftime('%H:%M:%S')})", entry_time
            except:
                pass
        
        # Record entry time
        entry_time = datetime.now()
        self.active_sessions[identifier] = entry_time
        
        # Prepare entry data for CSV (exit time, duration, fare will be empty)
        entry_data = {
            'Entry Time': entry_time.strftime('%Y-%m-%d %H:%M:%S'),
            'Exit Time': '',  # Empty until vehicle exits
            'Plate Number': plate_number if plate_number else (f"UNKNOWN_{track_id}" if track_id else "UNKNOWN"),
            'Duration (hours)': '',
            'Fare (₹)': ''
        }
        
        # Write entry to CSV immediately
        try:
            df = pd.read_csv(self.csv_path)
            
            # Double-check: ensure we're not creating a duplicate entry
            # Check if there's already an entry with same identifier and empty exit time
            duplicate_check = df[(df['Plate Number'] == entry_data['Plate Number']) & (df['Exit Time'] == '')]
            if not duplicate_check.empty:
                # Entry already exists, don't create duplicate
                existing_entry_time = duplicate_check.iloc[0]['Entry Time']
                return False, f"⚠️ {identifier} entry already exists in CSV (entered at {existing_entry_time})", entry_time
            
            new_row = pd.DataFrame([entry_data])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(self.csv_path, index=False)
            
            message = f"✅ Entry logged: {identifier} at {entry_time.strftime('%H:%M:%S')}"
            return True, message, entry_time
            
        except Exception as e:
            return False, f"❌ Error writing entry to CSV: {str(e)}", None
    
    def log_exit(self, plate_number: str = None, track_id: int = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Log vehicle exit and update existing CSV row with exit time and fare.
        
        Args:
            plate_number: Vehicle license plate number (optional)
            track_id: Vehicle tracking ID (used if plate not available)
            
        Returns:
            Tuple of (success, message, exit_data_dict)
        """
        # Use plate number if available, otherwise use track_id
        identifier = plate_number if plate_number else (f"UNKNOWN_{track_id}" if track_id else "UNKNOWN")
        
        # Check if vehicle has entered
        if identifier not in self.active_sessions:
            return False, f"⚠️ {identifier} has no entry record! Cannot log exit.", None
        
        # Get entry time and remove from active sessions
        entry_time = self.active_sessions.pop(identifier)
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
        
        # Update existing CSV row instead of creating new one
        try:
            df = pd.read_csv(self.csv_path)
            
            # Find the row with matching identifier and empty exit time
            entry_time_str = entry_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Find the row to update - prioritize exact match by identifier and entry time
            # First try exact match
            mask = (df['Plate Number'] == identifier) & (df['Entry Time'] == entry_time_str) & (df['Exit Time'] == '')
            
            # If not found, try by identifier only (most recent entry with empty exit)
            if not mask.any():
                mask = (df['Plate Number'] == identifier) & (df['Exit Time'] == '')
                # If multiple found, use the one matching entry time, or the last one
                if mask.sum() > 1:
                    # Try to match entry time first
                    time_match = (df['Plate Number'] == identifier) & (df['Entry Time'] == entry_time_str) & (df['Exit Time'] == '')
                    if time_match.any():
                        mask = time_match
                    else:
                        # Use the last row (most recent entry)
                        matching_rows = df[mask]
                        last_idx = matching_rows.index[-1]
                        mask = df.index == last_idx
            
            # If still not found and we have track_id, check for UNKNOWN_track_id (plate updated after entry)
            if not mask.any() and track_id:
                unknown_id = f"UNKNOWN_{track_id}"
                # Try exact match first
                mask_unknown = (df['Plate Number'] == unknown_id) & (df['Entry Time'] == entry_time_str) & (df['Exit Time'] == '')
                # If not found, try any entry with empty exit
                if not mask_unknown.any():
                    mask_unknown = (df['Plate Number'] == unknown_id) & (df['Exit Time'] == '')
                    if mask_unknown.sum() > 1:
                        # Use the last matching row
                        matching_rows = df[mask_unknown]
                        last_idx = matching_rows.index[-1]
                        mask_unknown = df.index == last_idx
                
                # If found, update plate number and use this row
                if mask_unknown.any():
                    idx = df[mask_unknown].index[0]
                    df.at[idx, 'Plate Number'] = identifier
                    mask = mask_unknown
            
            if mask.any():
                # Update the existing row
                idx = df[mask].index[0]
                df.at[idx, 'Exit Time'] = exit_time.strftime('%Y-%m-%d %H:%M:%S')
                df.at[idx, 'Duration (hours)'] = round(duration_hours, 2)
                df.at[idx, 'Fare (₹)'] = round(fare, 2)
            else:
                # If row not found, create new row (fallback - should not happen normally)
                exit_data = {
                    'Entry Time': entry_time_str,
                    'Exit Time': exit_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'Plate Number': identifier,
                    'Duration (hours)': round(duration_hours, 2),
                    'Fare (₹)': round(fare, 2)
                }
                new_row = pd.DataFrame([exit_data])
                df = pd.concat([df, new_row], ignore_index=True)
            
            df.to_csv(self.csv_path, index=False)
            
            exit_data = {
                'Entry Time': entry_time_str,
                'Exit Time': exit_time.strftime('%Y-%m-%d %H:%M:%S'),
                'Plate Number': identifier,
                'Duration (hours)': round(duration_hours, 2),
                'Fare (₹)': round(fare, 2)
            }
            
            message = (f"✅ Exit logged: {identifier} | "
                      f"Duration: {duration_hours:.2f}h | "
                      f"Fare: ₹{fare:.2f}")
            
            return True, message, exit_data
            
        except Exception as e:
            return False, f"❌ Error updating CSV: {str(e)}", None
    
    def update_plate_number(self, old_identifier: str, new_plate_number: str, entry_time: datetime = None) -> bool:
        """
        Update plate number in CSV if vehicle was logged as UNKNOWN.
        
        Args:
            old_identifier: Original identifier (UNKNOWN_track_id)
            new_plate_number: Detected plate number
            entry_time: Entry time to match specific row (optional)
            
        Returns:
            True if updated successfully
        """
        try:
            df = pd.read_csv(self.csv_path)
            
            # Find rows with old identifier and empty exit time
            mask = (df['Plate Number'] == old_identifier) & (df['Exit Time'] == '')
            
            # If entry_time provided, match that too for more precise update
            if entry_time:
                entry_time_str = entry_time.strftime('%Y-%m-%d %H:%M:%S')
                mask = mask & (df['Entry Time'] == entry_time_str)
            
            if mask.any():
                df.loc[mask, 'Plate Number'] = new_plate_number
                df.to_csv(self.csv_path, index=False)
                
                # Update active_sessions key
                if old_identifier in self.active_sessions:
                    entry_time_stored = self.active_sessions.pop(old_identifier)
                    self.active_sessions[new_plate_number] = entry_time_stored
                
                return True
            return False
            
        except Exception as e:
            print(f"⚠️ Error updating plate number: {e}")
            return False
    
    def find_entry_by_track_id(self, track_id: int) -> Optional[datetime]:
        """
        Find entry time for a vehicle by track_id (UNKNOWN_track_id).
        
        Args:
            track_id: Vehicle tracking ID
            
        Returns:
            Entry datetime if found, None otherwise
        """
        identifier = f"UNKNOWN_{track_id}"
        return self.active_sessions.get(identifier)
    
    def get_active_parking_count(self) -> int:
        """Get count of currently parked vehicles."""
        return len(self.active_sessions)
    
    def get_active_plates(self) -> list:
        """Get list of currently parked vehicle plates."""
        return list(self.active_sessions.keys())
