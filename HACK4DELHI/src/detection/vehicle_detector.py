from ultralytics import YOLO


class VehicleDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def detect(self, frame):
        # ENABLE TRACKING: persist=True keeps IDs stable across frames
        results = self.model.track(frame, persist=True, verbose=False)[0]
        detections = []

        # COCO Classes: 2=car, 3=motorcycle, 5=bus, 7=truck
        vehicle_classes = [2, 3, 5, 7]

        # Check if any objects were detected
        if results.boxes.id is not None:
            # zip() ties the boxes, confidence, classes, and IDs together
            boxes = results.boxes.xyxy.tolist()
            confs = results.boxes.conf.tolist()
            cls_ids = results.boxes.cls.tolist()
            track_ids = results.boxes.id.tolist()

            for box, conf, cls_id, track_id in zip(boxes, confs, cls_ids, track_ids):
                if int(cls_id) in vehicle_classes:
                    x1, y1, x2, y2 = box
                    label = results.names[int(cls_id)]

                    # Return (x1, y1, x2, y2, label, confidence, ID)
                    detections.append((int(x1), int(y1), int(x2), int(y2), label, conf, int(track_id)))

        return detections