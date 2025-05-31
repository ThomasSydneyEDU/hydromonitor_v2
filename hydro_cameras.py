from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def index():
    top_image = '/static/snapshots/TopCamera.jpg'
    bottom_image = '/static/snapshots/BottomCamera.jpg'
    return render_template('index.html', top_image=top_image, bottom_image=bottom_image)

def start_server():
    app.run(host='0.0.0.0', port=5050,debug=True)

if __name__ == '__main__':
    start_server()