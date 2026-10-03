AI Vision Pro -- Real-Time Human Detection & Counting System

A real-time AI-powered human detection and tracking system built with
YOLOv8, BoT-SORT, OpenCV, Flask, and SQLite. The system detects
people through a live camera, assigns tracking IDs, counts IN/OUT
movements, monitors current occupancy, stores visitor records, and
provides a web-based monitoring dashboard.

🚀 Features

Real-time human detection using YOLOv8

Multi-person tracking using BoT-SORT

Entry and exit counting using virtual lines

Live people count and current occupancy

Persistent visitor records using SQLite

Automatic visitor image capture

Live camera streaming through Flask

Web dashboard with:

Camera monitoring

Analytics

Alerts

Reports

Settings

Visitor records

CSV visitor report export

Automatic camera reconnection

Real-time detection statistics through a JSON API

🛠️ Technologies Used

Technology            Purpose

Python                Core application
YOLOv8                Human detection
BoT-SORT              Object tracking
OpenCV                Camera processing and image handling
Flask                 Web server and dashboard
SQLite                Visitor data storage
HTML/CSS/JavaScript   Frontend dashboard
CSV                   Visitor report export

📂 Project Structure

Human-Detection-and-Counting-System/
│
├── app.py
├── yolov8n.pt
├── visitors.db
├── visitor_report.csv
│
├── templates/
│   ├── index.html
│   ├── camera.html
│   ├── analytics.html
│   ├── alerts.html
│   ├── reports.html
│   ├── settings.html
│   └── visitors.html
│
├── static/
│   └── visitors/
│       └── visitor images
│
└── README.md

⚙️ Installation

1. Clone the repository

git clone https://github.com/Urwashi-Khobare/AI-Vision-Pro-Real-Time-Human-Detection-Counting-System.git
cd AI-Vision-Pro-Real-Time-Human-Detection-Counting-System

2. Create a virtual environment

python -m venv venv

Activate it on Windows:

venv\Scripts\activate

3. Install dependencies

pip install flask opencv-python ultralytics numpy

If your project contains a requirements.txt, you can instead run:

pip install -r requirements.txt

4. Add the YOLO model

Place the YOLOv8 model file in the project root:

yolov8n.pt

The application loads this model for human detection.

▶️ Run the Project

Start the Flask application:

python app.py

Open your browser and visit:

http://127.0.0.1:5000/

📊 Dashboard Routes

Route              Purpose

/                Main dashboard
/camera          Live camera page
/analytics       Analytics page
/alerts          Alerts page
/reports         Reports page
/settings        Settings page
/visitors_page   Visitor records
/video_feed      Live MJPEG video stream
/data            Live detection statistics
/visitors        Visitor data API
/export          Download visitor CSV report

🧠 How It Works

The application initializes the SQLite visitor database.

OpenCV connects to the available camera.

YOLOv8 detects people in each frame.

BoT-SORT assigns and maintains tracking IDs.

The system tracks the movement of each person.

Crossing the entry line records an IN event.

Crossing the exit line records an OUT event.

Visitor information is stored in SQLite.

Detection results and statistics are displayed on the Flask
dashboard.

Visitor records can be exported as a CSV report.

🗄️ Database

The project uses SQLite with a visitors table containing:

tracker_id
entries
exits
inside
first_seen
last_seen

Example:

Tracker ID     Entries   Exits   Inside First Seen            Last Seen

1                    2       1        1 03-10-2026 10:20:15   03-10-2026 11:05:32

📈 Live Statistics

The /data API provides:

{
  "total": 0,
  "inside": 0,
  "in": 0,
  "out": 0,
  "alerts": 0
}

These values can be used by the frontend dashboard for real-time
monitoring.

📷 Camera Configuration

The application attempts multiple camera indexes:

0
1
2

It also configures the camera resolution and buffer settings and
attempts to reconnect if the camera becomes unavailable.

📄 CSV Reports

The /export endpoint generates a visitor report containing:

Tracker ID
Entries
Exits
Inside
First Seen
Last Seen

The generated report can be downloaded from the browser.

🔒 Project Purpose

This system can be used as a foundation for:

Smart building monitoring

Visitor management

Crowd monitoring

Office occupancy monitoring

Retail analytics

Campus monitoring

Event management

Security and surveillance analytics

⚠️ Notes

A compatible webcam/camera is required.

Detection accuracy depends on camera quality, lighting, camera
position, and model confidence.

The current implementation uses virtual entry and exit lines
configured in the video frame.

The project is intended as an AI/computer-vision project and should
be adapted appropriately for real-world privacy and security
requirements.

🔮 Future Enhancements

Face recognition with privacy-aware access controls

User authentication and role-based access

Cloud database integration

Email/SMS alerts

Advanced occupancy analytics

Daily/weekly/monthly reports

PDF report generation

Multiple camera support

Improved re-identification across camera views

Deployment using Docker or a cloud platform

👩‍💻 Author

Urwashi Khobare
B.Tech -- Computer Science & Engineering
Priyadarshini College of Engineering, Nagpur

⭐ Project Highlights

AI Detection • Object Tracking • IN/OUT Counting • Live Occupancy •
Flask Dashboard • SQLite Logging • CSV Reporting

If you find this project useful, consider giving the repository a ⭐ on
GitHub.
