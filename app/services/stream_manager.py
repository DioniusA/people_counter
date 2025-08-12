import os
import threading
from typing import Dict
from dotenv import load_dotenv
from app.services.stream_worker import StreamWorker
from app.db import get_all_streams_from_db  

load_dotenv()

class StreamManager:
    def __init__(self, model):
        self.model = model
        self.model_lock = threading.Lock()
        self.workers: Dict[int, StreamWorker] = {}
        self._lock = threading.Lock()

    def load_all_from_env(self):
        index = 1
        while True:
            name_key = f"CAMERA_{index}_NAME"
            url_key = f"CAMERA_{index}_URL"
            name = os.getenv(name_key)
            url = os.getenv(url_key)
            if not name or not url:
                break
            self.start_worker(index, name, url)
            index += 1

    def load_all_from_db(self):
        """Загружает все камеры из базы данных и запускает воркеры."""
        try:
            streams = get_all_streams_from_db()
        except Exception as e:
            print(f"Ошибка при загрузке из БД: {e}")
            streams = []

        for s in streams:
            self.start_worker(s["id"], s["name"], s["url"])

    def start_worker(self, stream_id: int, name: str, url: str):
        with self._lock:
            if stream_id in self.workers:
                raise RuntimeError("Worker already running for this stream_id")
            worker = StreamWorker(stream_id, name, url, self.model, self.model_lock)
            worker.start()
            self.workers[stream_id] = worker
            print(f"Started worker {stream_id} ({name})")

    def stop_worker(self, stream_id: int):
        with self._lock:
            w = self.workers.get(stream_id)
            if not w:
                raise RuntimeError("Worker not found")
            w.stop()
            w.join(timeout=10)
            del self.workers[stream_id]
            print(f"Stopped worker {stream_id}")

    def restart_worker(self, stream_id: int, name: str, url: str):
        with self._lock:
            if stream_id in self.workers:
                self.stop_worker(stream_id)
            self.start_worker(stream_id, name, url)

    def stop_all(self):
        with self._lock:
            ids = list(self.workers.keys())
        for sid in ids:
            try:
                self.stop_worker(sid)
            except Exception as e:
                print(f"Error stopping worker {sid}: {e}")
