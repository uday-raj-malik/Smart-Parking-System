# Smart Parking System - UI Integration Guide

## Overview
This Smart Parking System now includes a complete backend API and integrated UI dashboards that display real-time parking data from your OpenCV model.

## Features Added

### 1. Backend API (`backend_api.py`)
- RESTful API using Flask
- Serves parking status and CSV data to UI dashboards
- Auto-detects most recent CSV log file
- Provides endpoints for:
  - `/api/parking/status` - Current parking status and statistics
  - `/api/parking/entries` - All parking entries
  - `/api/parking/csv` - Download CSV file
  - `/api/config` - System configuration
  - `/api/health` - Health check

### 2. MCD UI (`MCD_UI.html`)
- **Removed**: Test buttons (capacity alert, invalid exit alert, add/remove car buttons)
- **Added**: 
  - Real-time CSV data display table showing all entry/exit logs
  - Capacity and occupied spaces display
  - Auto-refresh every 5 seconds
  - Download CSV functionality
  - Integrated alerts from backend

### 3. User UI (`userUI.html`)
- **Added**:
  - Real-time capacity and occupied spaces from backend
  - Parking availability display with progress bar
  - Auto-refresh every 5 seconds
  - Shows max capacity, occupied spots, and available spots

## How to Run

### Step 1: Start the Backend API
```bash
cd /path/to/HACK4DELHI
python backend_api.py
```

The API will start on `http://localhost:5000`

### Step 2: Run Your OpenCV Model
In a separate terminal:
```bash
cd /path/to/HACK4DELHI
python src/main.py
```

This will create CSV log files as vehicles enter/exit.

### Step 3: Open the UI Dashboards

**MCD Dashboard** (for Municipal Corporation):
- Open `MCD_UI.html` in your web browser
- Or serve it via: `python -m http.server 8000` then open `http://localhost:8000/MCD_UI.html`

**User Dashboard**:
- Open `userUI.html` in your web browser
- Or serve it via: `http://localhost:8000/userUI.html`

## API Endpoints

### GET `/api/parking/status`
Returns current parking status:
```json
{
  "entries": [...],
  "total_entries": 5,
  "total_exits": 3,
  "active_parked": 2,
  "revenue": 150.0,
  "max_capacity": 2,
  "hourly_rate": 50,
  "available_spots": 0,
  "capacity_percentage": 100.0,
  "is_over_capacity": true,
  "csv_filename": "parking_log_20260110_224446.csv"
}
```

### GET `/api/parking/entries`
Returns all parking entries from CSV.

### GET `/api/parking/csv`
Downloads the CSV file.

## CSV Format
The system uses this CSV format (created by `main.py`):
```
Entry Time,Exit Time,Plate Number,Duration (hours),Fare (₹)
2026-01-10 22:45:20,,R183JF,,
2026-01-10 22:45:20,2026-01-10 22:45:32,R183JF,0.0,50.0
```

- **Entry Time**: Timestamp when vehicle entered
- **Exit Time**: Timestamp when vehicle exited (empty if still parked)
- **Plate Number**: Vehicle license plate (or UNKNOWN_{track_id} if not detected)
- **Duration (hours)**: Parking duration (only filled on exit)
- **Fare (₹)**: Parking fee (only filled on exit)

## Integration Features

### Real-time Updates
- Both UIs automatically refresh every 5 seconds
- MCD UI shows live parking entries/exits table
- User UI shows live capacity status

### Capacity Monitoring
- Displays current occupancy vs max capacity
- Visual progress bar with color coding:
  - Green: < 80% capacity
  - Yellow: 80-100% capacity
  - Red: Over capacity
- Automatic alerts when capacity is exceeded

### CSV Data Display
- MCD UI shows all parking transactions in a searchable table
- Highlights vehicles still parked (yellow background)
- Shows entry/exit times, plate numbers, duration, and fare
- Download CSV button to export data

## Troubleshooting

### Backend API not starting
- Make sure Flask and flask-cors are installed: `pip install flask flask-cors`
- Check if port 5000 is already in use
- Verify you're in the correct directory with CSV files

### UI not connecting to backend
- Ensure backend API is running on `http://localhost:5000`
- Check browser console for CORS errors
- If accessing from different machine, update `API_BASE_URL` in HTML files

### No CSV data showing
- Make sure `main.py` has created at least one CSV file
- CSV files should be in format: `parking_log_YYYYMMDD_HHMMSS.csv`
- Check backend API logs for parsing errors

## Configuration

### Max Capacity
Currently set to **2** in:
- `main.py` (line 47)
- `backend_api.py` (line 11)

To change, update both files.

### Hourly Rate
Currently set to **₹50/hour** in:
- `main.py` (line 48)
- `backend_api.py` (line 12)

To change, update both files.

## Notes

- The backend automatically finds the most recent CSV file
- Active parked vehicles are calculated by counting entries without exit times
- Revenue is calculated only from completed exits with fare information
- Both UIs work independently and can be used simultaneously
