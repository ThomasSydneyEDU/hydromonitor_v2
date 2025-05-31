from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def index():
    image_path = '/static/snapshots/TopCamera.jpg'
    return render_template('index.html', image_path=image_path)

def start_server():
    app.run(host='0.0.0.0', port=5050, debug=True)

if __name__ == '__main__':
    start_server()