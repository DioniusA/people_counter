import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional
from .config import POSTGRES_CONFIG, CAMERAS

def get_conn():
    return psycopg2.connect(**POSTGRES_CONFIG)

def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM streams")
            count = cur.fetchone()[0]
            if count == 0:
                for name, url in CAMERAS:
                    insert_stream(name, url)

def insert_stream(name: str, url: str) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO streams (name, url, last_count, last_update) VALUES (%s, %s, %s, %s) RETURNING id",
                (name, url, 0, None)
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id

def update_stream_row(stream_id: int, name: Optional[str], url: Optional[str]):
    fields = []
    values = []
    if name is not None:
        fields.append("name = %s")
        values.append(name)
    if url is not None:
        fields.append("url = %s")
        values.append(url)
    if fields:
        query = "UPDATE streams SET " + ", ".join(fields) + " WHERE id = %s"
        values.append(stream_id)
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                conn.commit()

def delete_stream_row(stream_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM streams WHERE id = %s", (stream_id,))
            conn.commit()

def get_all_streams_from_db():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM streams ORDER BY id")
            return cur.fetchall()

def get_stream_from_db(stream_id: int):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM streams WHERE id = %s", (stream_id,))
            return cur.fetchone()

def update_count_in_db(stream_id: int, count: int):
    now = datetime.now()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE streams SET last_count = %s, last_update = %s WHERE id = %s",
                (count, now, stream_id)
            )
            conn.commit()

def insert_count_history(stream_id: int, camera_name: str, people_count: int, image_path: Optional[str] = None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO counts (stream_id, camera_name, people_count, image_path)
                VALUES (%s, %s, %s, %s)
                """,
                (stream_id, camera_name, people_count, image_path)
            )
            conn.commit()
