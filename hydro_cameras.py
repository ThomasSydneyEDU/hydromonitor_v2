from flask import Flask, render_template, url_for

app = Flask(__name__)

@app.route('/')
def index():
    top_image_path = url_for('static', filename='snapshots/TopCamera.jpg')
    bottom_image_path = url_for('static', filename='snapshots/BottomCamera.jpg')
    return render_template('index.html', top_image_path=top_image_path, bottom_image_path=bottom_image_path)

def start_server():
    app.run(host='0.0.0.0', port=5050, debug=True)

if __name__ == '__main__':
    start_server()