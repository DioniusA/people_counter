from fastapi import FastAPI, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from .db import (
    init_db, insert_stream, update_stream_row, delete_stream_row,
    get_all_streams_from_db, get_stream_from_db
)
from .services.stream_manager import StreamManager

app = FastAPI(title="Multi-Stream Head Counter")

class StreamIn(BaseModel):
    name: str
    url: str

class StreamUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None

class StreamOut(BaseModel):
    id: int
    name: str
    url: str
    last_count: Optional[int] = None
    last_update: Optional[datetime] = None

manager: Optional[StreamManager] = None

@app.on_event("startup")
def startup_event():
    global manager
    init_db()
    from ultralytics import YOLO
    from .config import MODEL_PATH
    model = YOLO(MODEL_PATH)
    manager = StreamManager(model)
    manager.load_all_from_db()

@app.get("/streams", response_model=List[StreamOut])
def list_streams():
    rows = get_all_streams_from_db()
    return [
        StreamOut(
            id=r["id"],
            name=r["name"],
            url=r["url"],
            last_count=r.get("last_count"),
            last_update=r.get("last_update")
        ) for r in rows
    ]

@app.post("/streams", response_model=StreamOut)
def create_stream(stream_in: StreamIn):
    stream_id = insert_stream(stream_in.name, stream_in.url)
    try:
        manager.start_worker(stream_id, stream_in.name, stream_in.url)
    except Exception as e:
        print(f"Warning: starting worker failed: {e}")
    row = get_stream_from_db(stream_id)
    return StreamOut(
        id=row["id"],
        name=row["name"],
        url=row["url"],
        last_count=row.get("last_count"),
        last_update=row.get("last_update")
    )

@app.put("/streams/{stream_id}", response_model=StreamOut)
def edit_stream(stream_id: int, update: StreamUpdate):
    row = get_stream_from_db(stream_id)
    if not row:
        raise HTTPException(status_code=404, detail="Stream not found")
    update_stream_row(stream_id, update.name, update.url)
    new_name = update.name if update.name is not None else row["name"]
    new_url = update.url if update.url is not None else row["url"]
    try:
        manager.restart_worker(stream_id, new_name, new_url)
    except Exception as e:
        print(f"Warning: restart worker failed: {e}")
    row = get_stream_from_db(stream_id)
    return StreamOut(
        id=row["id"],
        name=row["name"],
        url=row["url"],
        last_count=row.get("last_count"),
        last_update=row.get("last_update")
    )

@app.delete("/streams/{stream_id}")
def delete_stream(stream_id: int):
    row = get_stream_from_db(stream_id)
    if not row:
        raise HTTPException(status_code=404, detail="Stream not found")
    try:
        if stream_id in manager.workers:
            manager.stop_worker(stream_id)
    except Exception as e:
        print(f"Warning stopping worker on delete: {e}")
    delete_stream_row(stream_id)
    return {"detail": "deleted"}

@app.get("/streams/{stream_id}", response_model=StreamOut)
def get_stream(stream_id: int):
    row = get_stream_from_db(stream_id)
    if not row:
        raise HTTPException(status_code=404, detail="Stream not found")
    return StreamOut(
        id=row["id"],
        name=row["name"],
        url=row["url"],
        last_count=row.get("last_count"),
        last_update=row.get("last_update")
    )

@app.post("/streams/{stream_id}/start")
def start_stream_manual(stream_id: int):
    row = get_stream_from_db(stream_id)
    if not row:
        raise HTTPException(status_code=404, detail="Stream not found")
    try:
        manager.start_worker(stream_id, row["name"], row["url"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"detail": "started"}

@app.post("/streams/{stream_id}/stop")
def stop_stream_manual(stream_id: int):
    try:
        manager.stop_worker(stream_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"detail": "stopped"}
