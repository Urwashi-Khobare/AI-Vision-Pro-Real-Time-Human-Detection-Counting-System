from database import insert_count
import time
import cv2
from ultralytics import YOLO

# ---------------- CAMERA ----------------
def start_camera():
    print("🔄 Starting camera...")

    cap = cv2.VideoCapture(0, cv2.CAP_MSMF)

    if not cap.isOpened():
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        raise RuntimeError("❌ Camera not working")

    # Stability fix
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("✅ Camera started")
    return cap


cap = start_camera()

# ---------------- MODEL ----------------
print("🔄 Loading YOLO model...")
model = YOLO("yolov8n.pt")
print("✅ Model loaded")

# ---------------- LOGIC ----------------
line_y = 250
count_in = 0
count_out = 0

previous_positions = {}
counted_ids = set()

last_save = time.time()

# ---------------- STREAM FUNCTION ----------------
def generate_frames():
    global count_in, count_out, previous_positions, counted_ids, last_save

    while True:
        ret, frame = cap.read()

        if not ret or frame is None:
            continue

        if frame.shape[0] == 0 or frame.shape[1] == 0:
            continue

        frame = cv2.resize(frame, (640, 480))

        # 🔥 Stable tracking
        results = model.track(frame, persist=True, conf=0.5)[0]

        if results.boxes is not None and results.boxes.id is not None:
            current_positions = {}

            for box, track_id in zip(results.boxes.data, results.boxes.id):
                x1, y1, x2, y2, conf, cls = box[:6]

                if int(cls) != 0 or conf < 0.5:
                    continue

                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
                track_id = int(track_id)

                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2

                current_positions[track_id] = cy

                # Draw box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.circle(frame, (cx, cy), 5, (255,0,0), -1)

                # Counting logic
                if track_id in previous_positions and track_id not in counted_ids:
                    prev_cy = previous_positions[track_id]

                    if prev_cy < line_y and cy >= line_y:
                        count_out += 1
                        counted_ids.add(track_id)

                    elif prev_cy > line_y and cy <= line_y:
                        count_in += 1
                        counted_ids.add(track_id)

            previous_positions = current_positions

        # Save to DB
        if time.time() - last_save > 2:
            insert_count(count_in, count_out)
            print("Saved:", count_in, count_out)
            last_save = time.time()

        # UI overlay
        cv2.line(frame, (0, line_y), (640, line_y), (0,0,255), 2)

        cv2.putText(frame, f"IN: {count_in}", (10,40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        cv2.putText(frame, f"OUT: {count_out}", (10,80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

        # 🔥 Convert to JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        # 🔥 Yield stream
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')