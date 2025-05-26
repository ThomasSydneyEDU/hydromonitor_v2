from flask import Flask, render_template, Response
import cv2

app = Flask(__name__)

# Simulated sensor data
sensor_data = {
    'Air Temp': '22.3°C',
    'Water Temp': '19.1°C',
    'pH': '6.4',
    'EC': '1.2 mS/cm',
    'Top Float': 'Low',
    'Bottom Float': 'OK'
}

# Modified frame generator to support multiple cameras
def generate_frames(camera_index):
    cap = cv2.VideoCapture(camera_index)
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
    return render_template('index.html', data=sensor_data)

@app.route('/video_feed1')
def video_feed1():
    return Response(generate_frames(0), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed2')
def video_feed2():
    return Response(generate_frames(1), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)