from flask import Flask, render_template, Response, jsonify
import cv2
from ultralytics import YOLO
import threading
import time
from collections import defaultdict

app = Flask(__name__)

# ======================================
# LOAD MODEL
# ======================================
model = YOLO("yolov8n.pt")

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

total_entries = 0
total_exits = 0
current_occupancy = 0

alerts = 0

ENTRY_LINE = 220
EXIT_LINE = 380

history = {}
person_state = defaultdict(dict)

frame_data = None
lock = threading.Lock()

# ======================================
# DETECTION THREAD
# ======================================
def detect_people():
    global live_people
    global total_entries
    global total_exits
    global current_occupancy
    global alerts 
    global cap, frame_data
    

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

        try:
            results = model.track(
            frame,
            persist=True,
            tracker="botsort.yaml",
            classes=[0],
            conf=0.50,
            iou=0.50,
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

                    w = x2 - x1
                    h = y2 - y1

                    if w < 40 or h < 80:
                     continue

                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                    cv2.circle(frame, (cx, cy), 5, (0,0,255), -1)

                    cv2.putText(frame, f'ID {pid}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

                    # IN / OUT COUNT
                    if pid not in person_state:

                        person_state[pid] = {
                          "status": "unknown"
                        }

                    if pid in history:

                      old_y = history[pid]

                      # ENTRY
                      if old_y < ENTRY_LINE and cy >= ENTRY_LINE:

                        if person_state[pid]["status"] != "inside":

                          total_entries += 1
                          current_occupancy += 1

                        person_state[pid]["status"] = "inside"

                      # EXIT
                      elif old_y > EXIT_LINE and cy <= EXIT_LINE:

                        if person_state[pid]["status"] != "outside":

                          total_exits += 1

                          if current_occupancy > 0:
                               current_occupancy -= 1

                          person_state[pid]["status"] = "outside"

                    history[pid] = cy 

        if current_occupancy >= 20:
          alerts = 1
        else:
          alerts = 0

        # DRAW HUD
        cv2.line(
          frame,
         (0, ENTRY_LINE),
         (1000, ENTRY_LINE),
         (0,255,0),
          3
        )

        cv2.line(
         frame,
         (0, EXIT_LINE),
         (1000, EXIT_LINE),
         (0,0,255),
         3
        )
        cv2.putText(
         frame,
         f'LIVE : {live_people}',
         (20,40),
         cv2.FONT_HERSHEY_SIMPLEX,
         0.8,
         (0,255,255),
         2
        )

        cv2.putText(
         frame,
         f'ENTRY : {total_entries}',
         (20,80),
         cv2.FONT_HERSHEY_SIMPLEX,
         0.8,
         (0,255,0),
          2
        )

        cv2.putText(
         frame,
         f'EXIT : {total_exits}',
         (20,120),
         cv2.FONT_HERSHEY_SIMPLEX,
         0.8,
         (0,0,255),
         2
        )

        cv2.putText(
         frame,
         f'INSIDE : {current_occupancy}',
          (20,160),
         cv2.FONT_HERSHEY_SIMPLEX,
         0.8,
         (255,255,0),
         2
        )

        cv2.putText(
         frame,
         f'ALERT : {alerts}',
         (20,200),
         cv2.FONT_HERSHEY_SIMPLEX,
         0.8,
         (0,165,255),
         2
        )

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

        "inside": current_occupancy,

        "in": total_entries,

        "out": total_exits,

        "alerts": alerts
    })

# ======================================
# START
# ======================================
if __name__ == "__main__":
    t = threading.Thread(target=detect_people)
    t.daemon = True
    t.start()

    app.run(debug=True, threaded=True, use_reloader=False)