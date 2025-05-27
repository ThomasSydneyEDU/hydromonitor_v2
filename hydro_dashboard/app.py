from flask import Flask, render_template, Response
import cv2
import os
import json

app = Flask(__name__)

# Modified frame generator to support multiple cameras
def generate_frames(camera_source):
    cap = cv2.VideoCapture(camera_source)
    if not cap.isOpened():
        print(f"Failed to open {camera_source}")
        return
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        status_path = os.path.join(script_dir, 'status.json')
        with open(status_path) as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to load sensor data: {e}")
        data = {}
    return render_template('index.html', data=data)

@app.route('/video_feed1')
def video_feed1():
    return Response(generate_frames("/dev/video0"), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed2')
def video_feed2():
    return Response(generate_frames("/dev/video2"), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)