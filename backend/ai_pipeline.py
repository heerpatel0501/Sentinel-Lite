import os
import re
import cv2
import torch
import hashlib
import numpy as np
from datetime import datetime
from ultralytics import YOLO

_original_torch_load = torch.load
def _patched_load(*args, **kwargs):
    kwargs.setdefault("weights_only", False)
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_load

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except Exception as e:
    EASYOCR_AVAILABLE = False
    print(f"[AI Warning] EasyOCR import failed: {e}")

class SentinelAIEngine:
    """
    Production AI Computer Vision Pipeline:
    RTSP Frame -> Vehicle Detection (YOLOv8) -> Dedicated Plate Detector -> OCR (EasyOCR) -> Evidence Snapshot
    """
    def __init__(self, yolo_weights=None, snapshot_dir=None, use_gpu=False):
        if yolo_weights is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            yolo_weights = os.path.join(base_dir, "yolov8n.pt")
            if not os.path.exists(yolo_weights):
                yolo_weights = "yolov8n.pt"
        self.vehicle_model = YOLO(yolo_weights)
        
        self.plate_detector_type = "EasyOCR-CRAFT-DeepText"

        self.ocr_reader = None
        if EASYOCR_AVAILABLE:
            try:
                gpu_flag = use_gpu and torch.cuda.is_available()
                self.ocr_reader = easyocr.Reader(["en"], gpu=gpu_flag)
                print(f"[AI Engine] EasyOCR reader initialized (GPU={gpu_flag})")
            except Exception as ex:
                print(f"[AI Warning] Could not instantiate EasyOCR reader: {ex}")

        if snapshot_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            snapshot_dir = os.path.join(base_dir, "evidence", "snapshots")
        self.snapshot_dir = snapshot_dir
        os.makedirs(self.snapshot_dir, exist_ok=True)

        self.plate_pattern = re.compile(r"([A-Z]{2})[ -]?([0-9]{1,2})[ -]?([A-Z]{1,3})[ -]?([0-9]{4})")

    def normalize_plate_text(self, raw_text: str):
        if not raw_text:
            return ("", "", 0.0)
            
        cleaned = re.sub(r"[^A-Z0-9]", "", raw_text.upper())
        match = self.plate_pattern.search(cleaned)
        if match:
            state, rto, series, number = match.groups()
            normalized = f"{state}{int(rto):02d}-{series}-{number}"
            return (cleaned, normalized, 0.95)
            
        if len(cleaned) >= 6:
            return (cleaned, cleaned, 0.70)
            
        return (cleaned, cleaned, 0.50)

    def locate_plate_in_vehicle(self, vehicle_bgr: np.ndarray):
        """
        Dedicated license-plate localization using CRAFT deep learning text region detection
        with geometric aspect ratio filtering, falling back to vehicle bumper ROI.
        """
        vh, vw = vehicle_bgr.shape[:2]
        if vh < 20 or vw < 30:
            return (vehicle_bgr, [0, 0, vw, vh], 0.4)

        if self.ocr_reader is not None:
            try:
                # Target the lower 65% of vehicle where license plates reside
                roi_y_start = int(vh * 0.35)
                sub_crop = vehicle_bgr[roi_y_start:vh, :]
                
                h_boxes, _ = self.ocr_reader.detect(sub_crop)
                boxes = h_boxes[0] if (h_boxes and len(h_boxes) > 0) else []
                valid_plate_boxes = []
                for box in boxes:
                    if len(box) == 4:
                        xmin, xmax, ymin, ymax = box
                        bw = xmax - xmin
                        bh = ymax - ymin
                        if bh > 8 and bw > 18:
                            aspect = bw / float(bh)
                            # License plates typically have aspect ratio 1.4 to 6.5
                            if 1.4 <= aspect <= 6.5:
                                valid_plate_boxes.append((xmin, ymin + roi_y_start, bw, bh))
                
                if valid_plate_boxes:
                    best_box = max(valid_plate_boxes, key=lambda b: b[2] * b[3])
                    px, py, pw, ph = best_box
                    pad_x = int(pw * 0.08)
                    pad_y = int(ph * 0.08)
                    x1 = max(0, px - pad_x)
                    y1 = max(0, py - pad_y)
                    x2 = min(vw, px + pw + pad_x)
                    y2 = min(vh, py + ph + pad_y)
                    plate_crop = vehicle_bgr[y1:y2, x1:x2]
                    return (plate_crop, [int(x1), int(y1), int(x2 - x1), int(y2 - y1)], 0.92)
            except Exception as e:
                pass

        # Fallback bumper ROI
        roi_y = int(vh * 0.55)
        roi_h = vh - roi_y
        roi_x = int(vw * 0.15)
        roi_w = int(vw * 0.70)
        plate_crop = vehicle_bgr[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
        return (plate_crop, [roi_x, roi_y, roi_w, roi_h], 0.65)

    def extract_ocr_from_plate(self, plate_crop: np.ndarray):
        if self.ocr_reader is None or plate_crop.size == 0:
            return ("", 0.0)

        try:
            gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
            enhanced = cv2.bilateralFilter(gray, 9, 75, 75)
            
            results = self.ocr_reader.readtext(enhanced, detail=1, paragraph=False)
            if not results:
                results = self.ocr_reader.readtext(plate_crop, detail=1, paragraph=False)

            if results:
                best_text = " ".join([res[1] for res in results if res[2] > 0.3])
                avg_conf = sum([res[2] for res in results]) / len(results)
                return (best_text.strip(), float(avg_conf))
        except Exception as e:
            print(f"[AI Engine OCR Error] {e}")

        return ("", 0.0)

    def save_evidence_snapshot(self, frame_bgr: np.ndarray, vehicle_box: list, plate_text: str, camera_id: int, pts: float):
        h, w = frame_bgr.shape[:2]
        x1, y1, x2, y2 = [int(v) for v in vehicle_box]
        pad_x = int((x2 - x1) * 0.1)
        pad_y = int((y2 - y1) * 0.1)
        cx1 = max(0, x1 - pad_x)
        cy1 = max(0, y1 - pad_y)
        cx2 = min(w, x2 + pad_x)
        cy2 = min(h, y2 + pad_y)

        crop = frame_bgr[cy1:cy2, cx1:cx2].copy()
        
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(crop, f"CAM-{camera_id:02d} | PTS:{pts:.1f}s | {timestamp_str}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        if plate_text:
            cv2.putText(crop, f"PLATE: {plate_text}", (10, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        safe_plate = re.sub(r"[^A-Z0-9]", "", plate_text) if plate_text else "UNKNOWN"
        filename = f"evidence_cam{camera_id}_{int(pts*100)}_{safe_plate}_{int(datetime.now().timestamp())}.jpg"
        file_path = os.path.join(self.snapshot_dir, filename)
        
        cv2.imwrite(file_path, crop, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        sha256 = ""
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                sha256 = hashlib.sha256(f.read()).hexdigest()

        uri_reference = f"/evidence/snapshots/{filename}"
        return (file_path, uri_reference, sha256, file_size)

    def process_frame(self, frame_bgr: np.ndarray, camera_id: int = 1, pts: float = 0.0):
        h, w = frame_bgr.shape[:2]
        detections = []

        results = self.vehicle_model(frame_bgr, verbose=False)
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                label = self.vehicle_model.names[cls_id]

                if label in ["car", "truck", "bus", "motorcycle"]:
                    vx1, vy1, vx2, vy2 = box.xyxy[0].tolist()
                    vx1, vy1, vx2, vy2 = max(0, int(vx1)), max(0, int(vy1)), min(w, int(vx2)), min(h, int(vy2))
                    
                    if (vx2 - vx1) < 20 or (vy2 - vy1) < 20:
                        continue

                    vehicle_crop = frame_bgr[vy1:vy2, vx1:vx2]

                    plate_crop, [px, py, pw, ph], plate_det_conf = self.locate_plate_in_vehicle(vehicle_crop)

                    raw_text, ocr_conf = self.extract_ocr_from_plate(plate_crop)

                    cleaned_text, normalized_plate, norm_conf = self.normalize_plate_text(raw_text)

                    file_path, uri_ref, sha256, file_size = self.save_evidence_snapshot(
                        frame_bgr, [vx1, vy1, vx2, vy2], normalized_plate, camera_id, pts
                    )

                    detections.append({
                        "vehicle_type": label,
                        "confidence_score": round(conf, 3),
                        "vehicle_box_norm": [round(vx1/w, 4), round(vy1/h, 4), round(vx2/w, 4), round(vy2/h, 4)],
                        "plate_text": cleaned_text or "DETECTED_VEHICLE",
                        "normalized_plate": normalized_plate or "",
                        "ocr_confidence": round(ocr_conf if ocr_conf > 0 else norm_conf, 3),
                        "plate_box_norm": [
                            round((vx1 + px)/w, 4), round((vy1 + py)/h, 4),
                            round((vx1 + px + pw)/w, 4), round((vy1 + py + ph)/h, 4)
                        ],
                        "evidence_file_path": file_path,
                        "evidence_uri": uri_ref,
                        "sha256_hash": sha256,
                        "file_size_bytes": file_size,
                        "pts_timestamp": round(pts, 2)
                    })

        return detections
