import os
import csv
from flask import send_file
import sqlite3
from datetime import datetime
from flask import Flask, render_template, Response, jsonify
import cv2
from ultralytics import YOLO
import threading
import time

app = Flask(__name__)

# ======================================
# LOAD MODEL
# ======================================
model = YOLO("yolov8n.pt")
DB_NAME = "visitors.db"

def init_db():

    conn = sqlite3.connect(DB_NAME)

    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS visitors(

        tracker_id TEXT PRIMARY KEY,
        entries INTEGER,
        exits INTEGER,
        inside INTEGER,
        first_seen TEXT,
        last_seen TEXT

    )
    """)

    conn.commit()
    conn.close()

init_db()

def update_visitor(pid, action):

    print(f"Updating DB: {pid} -> {action}")

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM visitors WHERE tracker_id=?",
        (str(pid),)
    )

    row = cur.fetchone()

    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    if row is None:

        entries = 1 if action == "entry" else 0
        exits = 1 if action == "exit" else 0

        cur.execute("""
        INSERT INTO visitors
        VALUES (?,?,?,?,?,?)
        """,
        (
            str(pid),
            entries,
            exits,
            1 if action == "entry" else 0,
            now,
            now
        ))

    else:

        if action == "entry":

            cur.execute("""
            UPDATE visitors
            SET entries = entries + 1,
                inside = 1,
                last_seen = ?
            WHERE tracker_id = ?
            """,
            (now, str(pid)))

        else:

            cur.execute("""
            UPDATE visitors
            SET exits = exits + 1,
                inside = 0,
                last_seen = ?
            WHERE tracker_id = ?
            """,
            (now, str(pid)))

    conn.commit()
    conn.close()

os.makedirs("static/visitors", exist_ok=True)
# ======================================
# CAMERA OPEN (FINAL FIX)
# ======================================
def start_camera():
    # Try camera indexes 0,1,2
    for idx in [0, 1, 2]:
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)

        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            print("Camera Started :", idx)
            return cap

    # fallback
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        return cap

    return None


cap = start_camera()

# ======================================
# GLOBAL DATA
# ======================================
live_people = 0
in_count = 0
out_count = 0
current_occupancy = 0
alerts = 0

ENTRY_LINE = 200
EXIT_LINE = 400

history = {}
person_state = {}

frame_data = None
lock = threading.Lock()

# ======================================
# DETECTION THREAD
# ======================================
def detect_people():
    global cap, frame_data
    global live_people
    global in_count
    global out_count
    global alerts
    global current_occupancy
    while True:

        if cap is None or not cap.isOpened():
            cap = start_camera()
            time.sleep(1)
            continue

        success, frame = cap.read()

        if not success:
            cap.release()
            cap = start_camera()
            time.sleep(1)
            continue

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (1000, 600))

        ENTRY_LINE = 200
        EXIT_LINE = 400

        try:
            results = model.track(
                frame,
                persist=True,
                tracker="botsort.yaml",
                classes=[0],
                conf=0.45,
                verbose=False
            )
        except:
            results = []

        live_people = 0

        if results and len(results) > 0:
            r = results[0]

            if r.boxes.id is not None:

                boxes = r.boxes.xyxy.cpu().numpy()
                ids = r.boxes.id.cpu().numpy().astype(int)

                live_people = len(ids)

                for box, pid in zip(boxes, ids):

                    x1, y1, x2, y2 = map(int, box)
                    image_path = f"static/visitors/{pid}.jpg"

                    if not os.path.exists(image_path):

                        crop = frame[
                          max(0, y1):min(frame.shape[0], y2),
                          max(0, x1):min(frame.shape[1], x2)
                        ]

                        if crop.size > 0:
                          cv2.imwrite(image_path, crop)

                    cx = (x1 + x2) // 2
                    cy = y2

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                    cv2.circle(frame, (cx, cy), 5, (0,0,255), -1)

                    cv2.putText(frame, f'ID {pid}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

                    # IN / OUT COUNT
                    if pid not in person_state:

                       person_state[pid] = {
                        "status": "outside"
                       }

                    if pid in history:

                        old_y = history[pid]

                        print(f"PID={pid}, old_y={old_y}, cy={cy}")

                        # ENTRY (Top -> Bottom)
                        if old_y < ENTRY_LINE and cy >= ENTRY_LINE:

                          if person_state[pid]["status"] == "outside":

                            print(f"ENTRY -> {pid}")

                            in_count += 1
                            current_occupancy += 1

                            update_visitor(pid, "entry")

                            person_state[pid]["status"] = "inside"

                            print(f"ENTRY -> {pid}")

                        # EXIT (Bottom -> Top)
                        elif old_y > EXIT_LINE and cy <= EXIT_LINE:
                          
                          if person_state[pid]["status"] == "inside":

                            print(f"EXIT -> {pid}")

                            out_count += 1
                            current_occupancy = max(
                                0,
                                current_occupancy - 1
                            )

                            update_visitor(pid, "exit")

                            person_state[pid]["status"] = "outside"

                            print(f"EXIT -> {pid}")
 
                    history[pid] = cy

        alerts = 1 if live_people >= 5 else 0
        
        cv2.line(frame, (0, ENTRY_LINE), (1000, ENTRY_LINE), (0,255,0), 3)
        cv2.putText(frame, "ENTRY", (20, ENTRY_LINE-10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

        cv2.line(frame, (0, EXIT_LINE), (1000, EXIT_LINE), (0,0,255), 3)
        cv2.putText(frame, "EXIT", (20, EXIT_LINE-10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        
        # DRAW HUD
        cv2.putText(frame, f'LIVE PEOPLE : {live_people}', (20,40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)

        cv2.putText(frame, f'IN : {in_count}', (20,80),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)

        cv2.putText(frame, f'OUT : {out_count}', (20,120),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)

        cv2.putText(frame, f'INSIDE : {current_occupancy}', (20,160),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,0), 2)
        with lock:
            frame_data = frame.copy()



# ======================================
# VIDEO STREAM (MAIN FIX)
# ======================================
def generate_frames():
    global frame_data

    while True:

        with lock:
            if frame_data is None:
                blank = 255 * 0 + 0
                img = cv2.imread("none.jpg")

                if img is None:
                    img = cv2.UMat(600, 1000, cv2.CV_8UC3).get()
                    img[:] = (0, 0, 0)

                cv2.putText(img, "Starting Camera...", (320, 300),
                            cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 255, 0), 2)

                ret, buffer = cv2.imencode(".jpg", img)
            else:
                ret, buffer = cv2.imencode(".jpg", frame_data)

        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   buffer.tobytes() + b'\r\n')

        time.sleep(0.03)

# ======================================
# ROUTES
# ======================================
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/camera')
def camera():
    return render_template("camera.html")

@app.route('/analytics')
def analytics():
    return render_template("analytics.html")

@app.route('/alerts')
def alerts_page():
    return render_template("alerts.html")

@app.route('/reports')
def reports():
    return render_template("reports.html")

@app.route('/settings')
def settings():
    return render_template("settings.html")

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/data')
def data():

    return jsonify({
    "total": live_people,
    "inside": max(0, current_occupancy),
    "in": in_count,
    "out": out_count,
    "alerts": alerts
})

@app.route("/visitors")
def visitors():

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    cur.execute("SELECT * FROM visitors")

    data = [dict(row) for row in cur.fetchall()]

    conn.close()

    return jsonify(data)

@app.route("/visitors_page")
def visitors_page():
    return render_template("visitors.html")

@app.route("/export")
def export():

    conn = sqlite3.connect(DB_NAME)

    cur = conn.cursor()

    cur.execute("SELECT * FROM visitors")

    rows = cur.fetchall()

    conn.close()

    with open(
        "visitor_report.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Tracker ID",
            "Entries",
            "Exits",
            "Inside",
            "First Seen",
            "Last Seen"
        ])

        writer.writerows(rows)

    return send_file(
        "visitor_report.csv",
        as_attachment=True
    )
# ======================================
# START
# ======================================
if __name__ == "__main__":
    t = threading.Thread(target=detect_people)
    t.daemon = True
    t.start()

    app.run(debug=True, threaded=True, use_reloader=False)