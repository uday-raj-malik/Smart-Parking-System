from ultralytics import YOLO

class VehicleDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)
        self.vehicle_classes = [2, 3, 5, 7]  # car, motorcycle, bus, truck

    def detect(self, frame):
        results = self.model.track(frame, persist=True, verbose=False)
        
        # Handle case where results might be empty
        if not results or len(results) == 0:
            return []
        
        result = results[0]
        detections = []

        boxes = result.boxes.xyxy.tolist()
        confs = result.boxes.conf.tolist()
        cls_ids = result.boxes.cls.tolist()

        # Get track IDs - handle None case properly
        if result.boxes.id is not None:
            track_ids = [int(id.item()) for id in result.boxes.id]
        else:
            track_ids = [None] * len(boxes)

        for box, conf, cls_id, track_id in zip(boxes, confs, cls_ids, track_ids):
            # Filter by vehicle classes
            if int(cls_id) not in self.vehicle_classes:
                continue
            
            # Filter low confidence detections
            if conf < 0.25:  # Minimum confidence threshold
                continue

            x1, y1, x2, y2 = map(int, box)

            # 🔥 CLAMP (prevents giant / invalid boxes)
            h, w, _ = frame.shape
            x1 = max(0, min(x1, w - 1))
            x2 = max(0, min(x2, w - 1))
            y1 = max(0, min(y1, h - 1))
            y2 = max(0, min(y2, h - 1))

            if x2 - x1 < 30 or y2 - y1 < 30:
                continue

            label = self.model.names[int(cls_id)]

            detections.append(
                (x1, y1, x2, y2, label, conf, track_id)
            )

        return detections
