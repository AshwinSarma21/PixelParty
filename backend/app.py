from flask import Flask, request
from flask_socketio import SocketIO, emit
import threading
import time
#from rgbmatrix import RGBMatrix, RGBMatrixOptions
#from multiprocessing import Process,Queue,Pipe
#from simplesquare import led_process
from werkzeug.security import check_password_hash
from db import init_db, get_db, load_latest_canvas_snapshot
import json


SIZE = 64
PASSWORD_HASH = "scrypt:32768:8:1$pojiw4Dscz7rzJyW$c3a3be5ba670fec064de97de5c15af3b01a68e6bb925fd9554e2f0dfb5ecdd8418ac42e4325a0e6ec7f01feab5aacefce733b0e92b9f574b7e3fe9ebfda3d440"

# Master canvas: 2D array initialized with transparent pixels
pixels = [["transparent" for _ in range(SIZE)] for _ in range(SIZE)]
matrixPixels = [[(0,0,0) for _ in range(SIZE)] for _ in range(SIZE)]

#parent, child = Pipe()
#print("began process")

init_db()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # allow all for testing


def get_or_create_default_canvas():
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM canvases WHERE name = ?",
            ("Default Canvas",),
        ).fetchone()

        if row:
            return row["id"]

        cursor = conn.execute(
            "INSERT INTO canvases (name, size) VALUES (?, ?)",
            ("Default Canvas", SIZE),
        )

        return cursor.lastrowid

DEFAULT_CANVAS_ID = get_or_create_default_canvas()
saved_pixels = load_latest_canvas_snapshot(DEFAULT_CANVAS_ID)
if saved_pixels:
    pixels = saved_pixels
else:
    pixels = [["transparent" for _ in range(SIZE)] for _ in range(SIZE)]

# save canvas to db
def save_canvas_snapshot():
    with get_db() as conn:
        conn.execute(
            "INSERT INTO canvas_snapshots (canvas_id, pixels_json) VALUES (?, ?)",
            (DEFAULT_CANVAS_ID, json.dumps(pixels)),
        )

@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "pixel-party",
        "canvas_size": SIZE,
    }
    
@app.get("/api/canvas")
def get_canvas():
    return {
        "size": SIZE,
        "pixels": pixels,
    }

@app.post("/api/pixels")
def update_pixel():
    data = request.get_json() or {}

    x = data.get("x")
    y = data.get("y")
    color = data.get("color")

    if not isinstance(x, int) or not isinstance(y, int):
        return {"ok": False, "error": "x and y must be integers"}, 400

    if x < 0 or x >= SIZE or y < 0 or y >= SIZE:
        return {"ok": False, "error": "pixel out of bounds"}, 400

    if not isinstance(color, str) or not color.startswith("#") or len(color) != 7:
        return {"ok": False, "error": "color must be a hex string like #ff0000"}, 400

    pixels[y][x] = color

    rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    #parent.send((x, y, rgb))

    socketio.emit("pixel_update", {"x": x, "y": y, "color": color})

    return {
        "ok": True,
        "pixel": {
            "x": x,
            "y": y,
            "color": color,
        },
    }

@app.post("/api/canvas/clear")
def clear_canvas():
    data = request.get_json() or {}
    provided = data.get("password", "")

    if not check_password_hash(PASSWORD_HASH, provided):
        return {"ok": False, "error": "wrong_password"}, 401

    global pixels
    pixels = [["transparent" for _ in range(SIZE)] for _ in range(SIZE)]

    #parent.send((-1, 0, (0, 0, 0)))
    socketio.emit("canvas_init", pixels)

    return {"ok": True}


@app.post("/api/canvases/save")
def save_canvas():
    data = request.get_json() or {}
    name = data.get("name", "Untitled Canvas")

    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO canvases (name, size) VALUES (?, ?)",
            (name, SIZE),
        )
        canvas_id = cursor.lastrowid

        conn.execute(
            "INSERT INTO canvas_snapshots (canvas_id, pixels_json) VALUES (?, ?)",
            (canvas_id, json.dumps(pixels)),
        )

    return {
        "ok": True,
        "canvas_id": canvas_id,
        "name": name,
    }


@app.get("/api/canvases")
def list_canvases():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT id, name, size, created_at, updated_at
            FROM canvases
            ORDER BY created_at DESC
        """).fetchall()

    return {
        "ok": True,
        "canvases": [dict(row) for row in rows],
    }


@app.post("/api/canvases/<int:canvas_id>/load")
def load_canvas(canvas_id):
    global pixels

    loaded_pixels = load_latest_canvas_snapshot(canvas_id)
    if loaded_pixels is None:
        return {"ok": False, "error": "canvas_not_found"}, 404

    if len(loaded_pixels) != SIZE or any(len(row) != SIZE for row in loaded_pixels):
        return {"ok": False, "error": "invalid_canvas_size"}, 400

    pixels = loaded_pixels
    socketio.emit("canvas_init", pixels)

    return {
        "ok": True,
        "canvas_id": canvas_id,
        "pixels": pixels,
    }




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
    
    #parent.send((x,y,tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))))
    
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
        #parent.send((-1,0,(0,0,0)))
        
        print(f"[{sid}] cleared the canvas (password correct).")
    else:
        emit("clear_response", {"ok": False, "reason": "wrong_password"})
        print(f"[{sid}] wrong password attempt to clear.")

#broadcast full canvas every 1 second so everything is accurate on people's screens
def broadcast_full_canvas():
    while True:
        socketio.emit("canvas_init", pixels)
        time.sleep(1)  # every 1 second
        
#autosave canvas to db
def autosave_canvas():
    while True:
        save_canvas_snapshot()
        time.sleep(10)

#background thread for regular broadcasts (daemon so it stops with the server)
threading.Thread(target=broadcast_full_canvas, daemon=True).start()


if __name__ == "__main__":
    #run flask
    socketio.run(app, host="0.0.0.0", port=5000)
