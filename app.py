from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import threading
import time
from rgbmatrix import RGBMatrix, RGBMatrixOptions
from multiprocessing import Process,Queue,Pipe
from simplesquare import led_process
from werkzeug.security import check_password_hash

SIZE = 64
PASSWORD_HASH = "scrypt:32768:8:1$pojiw4Dscz7rzJyW$c3a3be5ba670fec064de97de5c15af3b01a68e6bb925fd9554e2f0dfb5ecdd8418ac42e4325a0e6ec7f01feab5aacefce733b0e92b9f574b7e3fe9ebfda3d440"

# Master canvas: 2D array initialized with transparent pixels
pixels = [["transparent" for _ in range(SIZE)] for _ in range(SIZE)]
matrixPixels = [[(0,0,0) for _ in range(SIZE)] for _ in range(SIZE)]

parent, child = Pipe()
print("began process")

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # allow all for testing

@app.route("/")
def index():
    return render_template("index.html")

# When a client connects
@socketio.on("connect")
def handle_connect():
    print("New client connected")
    emit("canvas_init", pixels)

# When a client paints a pixel
@socketio.on("pixel_update")
def handle_pixel_update(data):
    global pixels
    x = data["x"]
    y = data["y"]
    color = data["color"]
    pixels[y][x] = color
    
    parent.send((x,y,tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))))
    
    # Send update to all other clients
    emit("pixel_update", data, broadcast=True, include_self=False)

@socketio.on("clear_canvas_request")
def handle_clear_canvas_request(data):
    sid = request.sid
    provided = (data or {}).get("password", "")

    if check_password_hash(PASSWORD_HASH, provided):
        global pixels
        pixels = [["transparent" for _ in range(SIZE)] for _ in range(SIZE)]
        socketio.emit("canvas_init", pixels)  # broadcast to all new canvas
        emit("clear_response", {"ok": True})
        
        #send info to the matrix process that we are clearing
        parent.send((-1,0,(0,0,0)))
        
        print(f"[{sid}] cleared the canvas (password correct).")
    else:
        emit("clear_response", {"ok": False, "reason": "wrong_password"})
        print(f"[{sid}] wrong password attempt to clear.")

#broadcast full canvas every 1 second so everything is accurate on people's screens
def broadcast_full_canvas():
    while True:
        socketio.emit("canvas_init", pixels)
        time.sleep(1)  # every 1 second

#background thread for regular broadcasts (daemon so it stops with the server)
threading.Thread(target=broadcast_full_canvas, daemon=True).start()


if __name__ == "__main__":
    #begin LED Matrix control process.
    p = Process(target=led_process, args=(child,))
    p.start()
    #run flask
    socketio.run(app, host="0.0.0.0", port=5000)
