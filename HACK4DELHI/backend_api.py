"""
Backend API for Smart Parking System
Serves CSV data and parking status to UI dashboards
"""
from flask import Flask, jsonify, send_file
from flask_cors import CORS
import os
import pandas as pd
import glob
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
MAX_CAPACITY = 2  # Should match main.py
HOURLY_RATE = 50  # Should match main.py

def get_latest_csv_file():
    """Find the most recent parking log CSV file"""
    csv_pattern = os.path.join(PROJECT_ROOT, "parking_log_*.csv")
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        return None
    
    # Get the most recent file
    latest_file = max(csv_files, key=os.path.getmtime)
    return latest_file

def parse_csv_data(csv_path):
    """Parse CSV file and return structured data"""
    if not csv_path or not os.path.exists(csv_path):
        return {
            'entries': [],
            'total_entries': 0,
            'total_exits': 0,
            'active_parked': 0,
            'revenue': 0,
            'max_capacity': MAX_CAPACITY,
            'hourly_rate': HOURLY_RATE
        }
    
    try:
        df = pd.read_csv(csv_path)
        
        # Convert to list of dictionaries
        entries = []
        active_parked = 0
        total_revenue = 0
        
        for _, row in df.iterrows():
            entry_time_val = row.get('Entry Time', '')
            exit_time_val = row.get('Exit Time', '')
            plate_val = row.get('Plate Number', '')
            duration_val = row.get('Duration (hours)', '')
            fare_val = row.get('Fare (₹)', '')
            
            # Convert to string, handling NaN values
            entry_time = str(entry_time_val) if pd.notna(entry_time_val) else ''
            exit_time = str(exit_time_val) if pd.notna(exit_time_val) else ''
            plate = str(plate_val) if pd.notna(plate_val) else ''
            
            # Clean up 'nan' strings
            if entry_time == 'nan' or entry_time == 'NaN' or entry_time == 'None':
                entry_time = ''
            if exit_time == 'nan' or exit_time == 'NaN' or exit_time == 'None':
                exit_time = ''
            if plate == 'nan' or plate == 'NaN' or plate == 'None':
                plate = ''
            
            # Check if vehicle is still parked (has entry but no exit)
            if entry_time != '' and exit_time == '':
                active_parked += 1
            
            # Calculate revenue (only from completed exits)
            if pd.notna(fare_val) and fare_val != '':
                try:
                    fare_float = float(fare_val)
                    if not pd.isna(fare_float):
                        total_revenue += fare_float
                except (ValueError, TypeError):
                    pass
            
            # Parse duration and fare
            duration_hours = None
            if pd.notna(duration_val) and duration_val != '':
                try:
                    duration_hours = float(duration_val)
                    if pd.isna(duration_hours):
                        duration_hours = None
                except (ValueError, TypeError):
                    duration_hours = None
            
            fare_amount = None
            if pd.notna(fare_val) and fare_val != '':
                try:
                    fare_amount = float(fare_val)
                    if pd.isna(fare_amount):
                        fare_amount = None
                except (ValueError, TypeError):
                    fare_amount = None
            
            entries.append({
                'entry_time': entry_time,
                'exit_time': exit_time,
                'plate_number': plate,
                'duration_hours': duration_hours,
                'fare': fare_amount
            })
        
        # Count total entries (rows with entry_time) and exits (rows with both entry and exit)
        total_entries = len([e for e in entries if e['entry_time'] != ''])
        total_exits = len([e for e in entries if e['entry_time'] != '' and e['exit_time'] != ''])
        
        return {
            'entries': entries,
            'total_entries': total_entries,
            'total_exits': total_exits,
            'active_parked': active_parked,
            'revenue': round(total_revenue, 2),
            'max_capacity': MAX_CAPACITY,
            'hourly_rate': HOURLY_RATE,
            'available_spots': max(0, MAX_CAPACITY - active_parked),
            'capacity_percentage': round((active_parked / MAX_CAPACITY * 100) if MAX_CAPACITY > 0 else 0, 1),
            'is_over_capacity': active_parked > MAX_CAPACITY
        }
    except Exception as e:
        print(f"Error parsing CSV: {e}")
        return {
            'entries': [],
            'total_entries': 0,
            'total_exits': 0,
            'active_parked': 0,
            'revenue': 0,
            'max_capacity': MAX_CAPACITY,
            'hourly_rate': HOURLY_RATE,
            'available_spots': MAX_CAPACITY,
            'capacity_percentage': 0,
            'is_over_capacity': False,
            'error': str(e)
        }

@app.route('/api/parking/status', methods=['GET'])
def get_parking_status():
    """Get current parking status and statistics"""
    csv_file = get_latest_csv_file()
    data = parse_csv_data(csv_file)
    
    # Add file info
    if csv_file:
        data['csv_filename'] = os.path.basename(csv_file)
        data['csv_file_path'] = csv_file
    else:
        data['csv_filename'] = None
        data['csv_file_path'] = None
    
    return jsonify(data)

@app.route('/api/parking/entries', methods=['GET'])
def get_parking_entries():
    """Get all parking entries from CSV"""
    csv_file = get_latest_csv_file()
    data = parse_csv_data(csv_file)
    return jsonify({'entries': data['entries'], 'total': len(data['entries'])})

@app.route('/api/parking/csv', methods=['GET'])
def download_csv():
    """Download the CSV file"""
    csv_file = get_latest_csv_file()
    if csv_file and os.path.exists(csv_file):
        return send_file(csv_file, as_attachment=True, download_name=os.path.basename(csv_file))
    return jsonify({'error': 'CSV file not found'}), 404

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get system configuration"""
    return jsonify({
        'max_capacity': MAX_CAPACITY,
        'hourly_rate': HOURLY_RATE
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    print("🚀 Starting Smart Parking Backend API...")
    print(f"📁 Project root: {PROJECT_ROOT}")
    print("🌐 API will be available at: http://localhost:5000")
    print("\nAvailable endpoints:")
    print("  GET /api/parking/status - Get parking status and statistics")
    print("  GET /api/parking/entries - Get all parking entries")
    print("  GET /api/parking/csv - Download CSV file")
    print("  GET /api/config - Get system configuration")
    print("  GET /api/health - Health check")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
