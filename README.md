# Multi-Stream Head Counter

This project counts heads on multiple video streams using a YOLO model with a FastAPI backend.

---

## Quick Start Guide

### 1. Clone the project

Clone the repository to your local machine using:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
````

Or download the ZIP archive from GitHub and extract it.

---

### 2. Set up PostgreSQL database

* Open pgAdmin or your preferred PostgreSQL client.
* Create a new database (e.g., `headcounter`).
* Execute the SQL scripts from the `db_scripts/` folder to create the necessary tables:

```sql
CREATE TABLE streams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    last_count INTEGER DEFAULT 0,
    last_update TIMESTAMP NULL
);

CREATE TABLE counts (
    id SERIAL PRIMARY KEY,
    stream_id INTEGER NOT NULL REFERENCES streams(id) ON DELETE CASCADE,
    camera_name VARCHAR(255) NOT NULL,
    people_count INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    image_path TEXT NULL
);
```

---

### 3. Configure the `.env` file

Create a `.env` file in the project root directory with the following content, and fill in your own values:

```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=headcounter
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# Model
MODEL_PATH=weights/head.pt
CONFIDENCE_THRESHOLD=0.4
CHECK_INTERVAL=60

# Output
OUTPUT_DIR=output

# Cameras
CAMERA_1_NAME=Camera-101
CAMERA_1_URL=rtsp://your_camera_1_stream_url

CAMERA_2_NAME=Camera-102
CAMERA_2_URL=rtsp://your_camera_2_stream_url
```

---

### 4. Install dependencies

It is recommended to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

Install required packages:

```bash
pip install -r requirements.txt
```

---

### 5. Run the server

Start the FastAPI server:

```bash
python main.py
```

The API will be accessible at [http://localhost:8000](http://localhost:8000).

---

### 6. Usage

* Use the API endpoints to add, edit, or delete video streams.
* The server manages separate workers to process each stream and count heads.
* Results are stored in the database; annotated images are saved in the `output/` folder.

---

## Notes

* The `output/` folder is ignored by Git to avoid uploading image files.
* Ensure the YOLO model file exists at the path specified in `.env`.
* A stable network connection is required for RTSP stream processing.

---

## API Documentation

Once the server is running, explore the interactive API docs at:
[http://localhost:8000/docs](http://localhost:8000/docs)

---

If you encounter any issues or have questions, feel free to open an issue or contact the maintainer.