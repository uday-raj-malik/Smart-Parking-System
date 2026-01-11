"""
Backend API for Smart Parking System
Serves CSV data and parking status to UI dashboards
"""
from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import os
import pandas as pd
import glob
import json
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config.json")

# Illegal exit alerts storage (in-memory, cleared on restart)
illegal_exit_alerts = []

def load_config():
    """Load configuration from config.json file"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('max_capacity', 2), config.get('hourly_rate', 50)
    except Exception as e:
        print(f"Error loading config: {e}")
    return 2, 50  # Default values

def save_config(max_capacity, hourly_rate):
    """Save configuration to config.json file"""
    try:
        config = {
            'max_capacity': int(max_capacity),
            'hourly_rate': float(hourly_rate)
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

# Load initial config
MAX_CAPACITY, HOURLY_RATE = load_config()

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
    # Reload config to get latest values
    max_cap, rate = load_config()
    
    if not csv_path or not os.path.exists(csv_path):
        return {
            'entries': [],
            'total_entries': 0,
            'total_exits': 0,
            'active_parked': 0,
            'revenue': 0,
            'max_capacity': max_cap,
            'hourly_rate': rate,
            'parked_vehicles': [],
            'all_vehicles': []
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
            if entry_time != '' and exit_time != '':
                active_parked -= 1
            
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
        total_entries = len([e for e in entries if e['entry_time'] != '' and e['exit_time'] == ''])
        total_exits = len([e for e in entries if e['entry_time'] != '' and e['exit_time'] != ''])
        
        # Get list of all vehicles (both parked and completed) for user UI dropdown
        all_vehicles = []
        parked_vehicles = []
        for entry in entries:
            if entry['entry_time'] != '':
                status = 'Pending' if entry['exit_time'] == '' else 'Completed'
                vehicle_info = {
                    'plate_number': entry['plate_number'],
                    'entry_time': entry['entry_time'],
                    'exit_time': entry['exit_time'] if entry['exit_time'] else None,
                    'status': status,
                    'duration_hours': entry.get('duration_hours'),
                    'fare': entry.get('fare')
                }
                all_vehicles.append(vehicle_info)
                
                # Also keep separate list of currently parked vehicles
                if entry['exit_time'] == '':
                    parked_vehicles.append({
                        'plate_number': entry['plate_number'],
                        'entry_time': entry['entry_time']
                    })
        
        return {
            'entries': entries,
            'total_entries': total_entries,
            'total_exits': total_exits,
            'active_parked': active_parked,
            'revenue': round(total_revenue, 2),
            'max_capacity': max_cap,
            'hourly_rate': rate,
            'available_spots': max(0, max_cap - active_parked),
            'capacity_percentage': round((active_parked / max_cap * 100) if max_cap > 0 else 0, 1),
            'is_over_capacity': active_parked > max_cap,
            'parked_vehicles': parked_vehicles,  # Currently parked only (for backward compatibility)
            'all_vehicles': all_vehicles  # All vehicles with status (for user UI dropdown)
        }
    except Exception as e:
        print(f"Error parsing CSV: {e}")
        max_cap, rate = load_config()
        return {
            'entries': [],
            'total_entries': 0,
            'total_exits': 0,
            'active_parked': 0,
            'revenue': 0,
            'max_capacity': max_cap,
            'hourly_rate': rate,
            'available_spots': max_cap,
            'capacity_percentage': 0,
            'is_over_capacity': False,
            'parked_vehicles': [],
            'all_vehicles': [],
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
    
    # Add illegal exit alerts
    data['illegal_exit_alerts'] = illegal_exit_alerts[-10:]  # Last 10 alerts
    
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
    max_cap, rate = load_config()  # Always reload from file
    return jsonify({
        'max_capacity': max_cap,
        'hourly_rate': rate
    })

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update system configuration"""
    try:
        data = request.get_json()
        max_capacity = data.get('max_capacity')
        hourly_rate = data.get('hourly_rate')
        
        if max_capacity is None or hourly_rate is None:
            return jsonify({'error': 'max_capacity and hourly_rate are required'}), 400
        
        if save_config(max_capacity, hourly_rate):
            global MAX_CAPACITY, HOURLY_RATE
            MAX_CAPACITY, HOURLY_RATE = load_config()
            return jsonify({
                'success': True,
                'max_capacity': MAX_CAPACITY,
                'hourly_rate': HOURLY_RATE
            })
        else:
            return jsonify({'error': 'Failed to save config'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/parking/parked', methods=['GET'])
def get_parked_vehicles():
    """Get list of currently parked vehicles (legacy endpoint)"""
    csv_file = get_latest_csv_file()
    data = parse_csv_data(csv_file)
    return jsonify({'parked_vehicles': data.get('parked_vehicles', [])})

@app.route('/api/parking/all-vehicles', methods=['GET'])
def get_all_vehicles():
    """Get list of all vehicles (parked and completed) with status for user UI dropdown"""
    csv_file = get_latest_csv_file()
    data = parse_csv_data(csv_file)
    return jsonify({'all_vehicles': data.get('all_vehicles', [])})

@app.route('/api/alerts/illegal-exit', methods=['POST'])
def add_illegal_exit_alert():
    """Add an illegal exit alert"""
    try:
        data = request.get_json()
        plate_number = data.get('plate_number', 'UNKNOWN')
        exit_time = data.get('exit_time', datetime.now().isoformat())
        
        alert = {
            'id': len(illegal_exit_alerts) + 1,
            'type': 'illegal_exit',
            'plate_number': plate_number,
            'exit_time': exit_time,
            'timestamp': datetime.now().isoformat(),
            'message': f'🚨 Illegal exit: Vehicle {plate_number} attempted to exit without entry record at {exit_time}'
        }
        
        illegal_exit_alerts.append(alert)
        # Keep only last 50 alerts
        if len(illegal_exit_alerts) > 50:
            illegal_exit_alerts.pop(0)
        
        return jsonify({'success': True, 'alert': alert})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
