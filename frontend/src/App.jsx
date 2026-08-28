import { useEffect, useState } from "react";
import { io } from "socket.io-client";
import PixelCanvas from "./PixelCanvas";

const SIZE = 64;
const socket = io();

console.log('check 1', socket.connected);
socket.on('connect', function() {
  console.log('check 2', socket.connected);
});

function createBlankCanvas() {
  return Array.from({ length: SIZE }, () =>
    Array.from({ length: SIZE }, () => "transparent")
  );
}

//export default: the only function that returns
export default function App() {
  const [pixels, setPixels] = useState(createBlankCanvas);
  const [color, setColor] = useState("#ff0000");
  const [canvases, setCanvases] = useState([]);
  const [selectedCanvasId, setSelectedCanvasId] = useState("");

  useEffect(() => {
    loadCanvasList();
    fetch("/api/canvas")
      .then((res) => res.json())
      .then((data) => {
        if (data.pixels) {
          setPixels(data.pixels);
        }
      })
      .catch((error) => {
        console.error("Failed to load canvas:", error);
      });

    socket.on("canvas_init", (serverPixels) => {
      setPixels(serverPixels);
    });

    socket.on("pixel_update", ({ x, y, color }) => {
      setPixels((current) => {
        const next = current.map((row) => [...row]);
        next[y][x] = color;
        return next;
      });
    });

    socket.on("clear_response", ({ ok, reason }) => {
      if (ok) {
        alert("Canvas cleared.");
      } else if (reason === "wrong_password") {
        alert("Wrong password.");
      } else {
        alert("Clear failed.");
      }
    });

    return () => {
      socket.off("canvas_init");
      socket.off("pixel_update");
      socket.off("clear_response");
    };
  }, []);

  async function saveCanvas() {
    const name = window.prompt("Canvas name:");
    if (!name) return;

    const response = await fetch("/api/canvases/save", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name }),
    });

    const data = await response.json();

    if (!data.ok) {
      alert("Save failed.");
      return;
    }

    alert("Canvas saved.");
    await loadCanvasList();
  }

  async function loadCanvasList() {
    try {
      const response = await fetch("/api/canvases");
      const data = await response.json();

      if (data.ok) {
        setCanvases(data.canvases);
      }
    } catch (error) {
      console.error("Failed to load saved canvases:", error);
    }
  }

  async function loadSelectedCanvas() {
    if (!selectedCanvasId) return;

    const response = await fetch(`/api/canvases/${selectedCanvasId}/load`, {
      method: "POST",
    });

    const data = await response.json();

    if (!data.ok) {
      alert("Load failed.");
      return;
    }

    setPixels(data.pixels);
  }

  function paintPixel(x, y) {
    setPixels((current) => {
      const next = current.map((row) => [...row]);
      next[y][x] = color;
      return next;
    });

    socket.emit("pixel_update", { x, y, color });
  }

  function clearCanvas() {
    const password = window.prompt("Enter admin password:");
    if (!password) return;

    socket.emit("clear_canvas_request", { password });
  }

  return (
    <main>
      <PixelCanvas pixels={pixels} onPaint={paintPixel} />

      <div className="toolbar">
        <input
          type="color"
          value={color}
          onChange={(event) => setColor(event.target.value)}
        />

        <button onClick={clearCanvas}>Clear</button>
        <button onClick={saveCanvas}>Save</button>

        <select
          value={selectedCanvasId}
          onChange={(event) => setSelectedCanvasId(event.target.value)}
        >
          <option value="">Select saved canvas</option>
          {canvases.map((canvas) => (
            <option key={canvas.id} value={canvas.id}>
              {canvas.name}
            </option>
          ))}
        </select>

        <button onClick={loadSelectedCanvas} disabled={!selectedCanvasId}>
          Load
        </button>
      </div>
    </main>
  );
}
