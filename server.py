from flask import Flask, render_template, Response
from main import generate_frames

app = Flask(__name__)

# ---------------- HOME ----------------
@app.route('/')
def index():
    return render_template('index.html')

# ---------------- VIDEO STREAM ----------------
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True, threaded=True)

from flask import Flask, render_template, Response, jsonify
from main import generate_frames, count_in, count_out

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# 🔥 NEW ROUTE (IMPORTANT)
@app.route('/data')
def data():
    return jsonify({
        "in": count_in,
        "out": count_out,
        "total": count_in - count_out
    })

if __name__ == "__main__":
    app.run(debug=True, threaded=True)

