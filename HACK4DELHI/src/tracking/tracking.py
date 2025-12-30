from ultralytics import YOLO
import cv2


class VehicleTracker:
    def __init__(self, model_path):
        # Load the model once
        self.model = YOLO(model_path)

    def detect_and_track(self, frame):
        """
        Runs YOLO tracking on the frame.
        Returns a list of tuples: (x1, y1, x2, y2, label, conf, track_id)
        """
        # persist=True is CRITICAL: it tells YOLO to remember objects between frames
        results = self.model.track(frame, persist=True, verbose=False)

        processed_detections = []

        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Only process if an ID is assigned
                if box.id is not None:
                    track_id = int(box.id.item())

                    # Get coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Get confidence and class
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = self.model.names[cls]

                    # Filter for specific classes if needed (e.g., cars/trucks only)
                    # if label in ['car', 'truck', 'bus', 'motorcycle']:
                    processed_detections.append((x1, y1, x2, y2, label, conf, track_id))

        return processed_detections