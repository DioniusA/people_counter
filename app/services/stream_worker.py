import cv2
import threading
import time
import os
from datetime import datetime
from ultralytics import YOLO
from app.db import update_count_in_db, insert_count_history
from app.config import CONFIDENCE_THRESHOLD, CHECK_INTERVAL, OUTPUT_DIR

class StreamWorker(threading.Thread):
    def __init__(self, stream_id: int, name: str, url: str, model: YOLO, model_lock: threading.Lock):
        super().__init__(daemon=True)
        self.stream_id = stream_id
        self.name = name
        self.url = url
        self.model = model
        self.model_lock = model_lock
        self._running = threading.Event()
        self._running.set()
        self.last_check_time = 0
        self.head_index = None
        for i, cname in enumerate(self.model.names):
            if str(cname).lower() == "head":
                self.head_index = i
                break

    def stop(self):
        self._running.clear()

    def run(self):
        print(f"[{self.name}] Starting worker for URL: {self.url}")
        cap = cv2.VideoCapture(self.url)
        if not cap.isOpened():
            print(f"[{self.name}] ERROR: cannot open stream: {self.url}")
            return

        while self._running.is_set():
            ret, frame = cap.read()
            if not ret:
                time.sleep(1)
                continue

            now = time.time()
            if now - self.last_check_time >= CHECK_INTERVAL:
                self.last_check_time = now
                try:
                    with self.model_lock:
                        results = self.model(frame, verbose=False)

                    people_count = 0
                    if len(results) > 0 and hasattr(results[0], "boxes"):
                        for box in results[0].boxes:
                            conf = float(box.conf[0])
                            cls = int(box.cls[0])
                            if conf < CONFIDENCE_THRESHOLD:
                                continue
                            if self.head_index is not None:
                                if cls != self.head_index:
                                    continue
                            else:
                                label = self.model.names[cls] if cls < len(self.model.names) else ''
                                if str(label).lower() != "head":
                                    continue
                            people_count += 1

                    update_count_in_db(self.stream_id, people_count)
                    print(f"[{self.name}] Counted: {people_count} people")

                    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    camera_output_dir = os.path.join(OUTPUT_DIR, self.name)
                    os.makedirs(camera_output_dir, exist_ok=True)
                    filename = f"{self.name}_{timestamp_str}.jpg"
                    save_path = os.path.join(camera_output_dir, filename)

                    annotated_frame = frame.copy()
                    if len(results) > 0 and hasattr(results[0], "boxes"):
                        for box in results[0].boxes:
                            conf = float(box.conf[0])
                            cls = int(box.cls[0])
                            if conf < CONFIDENCE_THRESHOLD:
                                continue
                            if self.head_index is not None and cls != self.head_index:
                                continue
                            label = f"{self.model.names[cls]} {conf:.2f}"
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(annotated_frame, label, (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

                    cv2.imwrite(save_path, annotated_frame)
                    print(f"[{self.name}] Saved annotated frame to {save_path}")

                    insert_count_history(self.stream_id, self.name, people_count, save_path)

                except Exception as e:
                    print(f"[{self.name}] ERROR during inference: {e}")

        cap.release()
        print(f"[{self.name}] Worker stopped")
