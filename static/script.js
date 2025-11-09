const SIZE = 64;
const CELL_SIZE = 10;
const canvas = document.getElementById("board");
const ctx = canvas.getContext("2d");
const colorPicker = document.getElementById("colorPicker");

canvas.width = SIZE * CELL_SIZE;
canvas.height = SIZE * CELL_SIZE;

// Master pixels array (starting black)
let pixels = Array.from({ length: SIZE }, () =>
  Array.from({ length: SIZE }, () => "black")
);

let isDrawing = false;
let lastX = null;
let lastY = null;

// Connect to Flask-SocketIO backend
const socket = io();

// Receive full canvas when connecting
socket.on("canvas_init", (masterPixels) => {
  pixels = masterPixels;
});

// Receive updates from other clients
socket.on("pixel_update", ({ x, y, color }) => {
  pixels[y][x] = color;
});

function draw() {
  // Clear the canvas first
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  // Flicker effect - random brightness for each frame
  const flicker = 0.9 + Math.random() * 0.1; // 0.9 to 1.1 brightness
  
  // First draw all the pixels
  for (let y = 0; y < SIZE; y++) {
    for (let x = 0; x < SIZE; x++) {
      const color = pixels[y][x];
      
      // Skip black pixels
      if (color === "black" || color === "#000000") continue;
      
      // Apply flicker to color
      const flickeredColor = applyFlicker(color, flicker);
      
      // Add glow effect
      ctx.shadowColor = flickeredColor;
      ctx.shadowBlur = 8;
      ctx.shadowOffsetX = 0;
      ctx.shadowOffsetY = 0;
      
      // Draw the pixel
      ctx.fillStyle = flickeredColor;
      ctx.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE);
      
      // Reset shadow for next pixel
      ctx.shadowBlur = 0;
    }
  }
  
  // THEN draw scanlines on top of everything
  drawScanlines();
  
  requestAnimationFrame(draw);
}

// Helper function to apply flicker effect to colors
function applyFlicker(color, flicker) {
  if (color.startsWith('#')) {
    // Hex color
    const r = parseInt(color.substr(1, 2), 16);
    const g = parseInt(color.substr(3, 2), 16);
    const b = parseInt(color.substr(5, 2), 16);
    
    const newR = Math.min(255, Math.floor(r * flicker));
    const newG = Math.min(255, Math.floor(g * flicker));
    const newB = Math.min(255, Math.floor(b * flicker));
    
    return `rgb(${newR}, ${newG}, ${newB})`;
  } else if (color.startsWith('rgb')) {
    // RGB color - simple brightness adjustment
    return color.replace(/rgb\((\d+), (\d+), (\d+)\)/, (match, r, g, b) => {
      const newR = Math.min(255, Math.floor(r * flicker));
      const newG = Math.min(255, Math.floor(g * flicker));
      const newB = Math.min(255, Math.floor(b * flicker));
      return `rgb(${newR}, ${newG}, ${newB})`;
    });
  }
  
  return color; // Fallback for named colors
}

// CRT scanlines effect
function drawScanlines() {
  // Use 'source-over' to draw on top of existing content
  ctx.globalCompositeOperation = 'source-over';
  
  // Draw horizontal scanlines
  ctx.fillStyle = 'rgba(0, 0, 0, 0.15)'; // Slightly darker for better visibility
  for (let y = 0; y < canvas.height; y += 4) {
    ctx.fillRect(0, y, canvas.width, 1); // Thinner lines
  }
  

  
  // Reset composite operation
  ctx.globalCompositeOperation = 'source-over';
}
draw();

// === Mouse Events ===
canvas.addEventListener("mousedown", (e) => {
  isDrawing = true;
  paintPixel(e.clientX, e.clientY);
});

canvas.addEventListener("mousemove", (e) => {
  if (isDrawing) paintPixel(e.clientX, e.clientY);
});

canvas.addEventListener("mouseup", () => stopDrawing());
canvas.addEventListener("mouseleave", () => stopDrawing());

// === Touch Events ===
canvas.addEventListener("touchstart", (e) => {
  e.preventDefault(); // Prevent scrolling
  isDrawing = true;
  const touch = e.touches[0];
  paintPixel(touch.clientX, touch.clientY);
});

canvas.addEventListener("touchmove", (e) => {
  e.preventDefault();
  if (!isDrawing) return;
  const touch = e.touches[0];
  paintPixel(touch.clientX, touch.clientY);
});

canvas.addEventListener("touchend", stopDrawing);
canvas.addEventListener("touchcancel", stopDrawing);

// === Stop drawing ===
function stopDrawing() {
  isDrawing = false;
  lastX = null;
  lastY = null;
}

// === Paint pixel function with smoothing ===
function paintPixel(clientX, clientY) {
  const rect = canvas.getBoundingClientRect();
  const x = Math.floor((clientX - rect.left) / (rect.width / SIZE));
  const y = Math.floor((clientY - rect.top) / (rect.height / SIZE));
  const color = colorPicker.value;

  if (lastX !== null && lastY !== null) {
    const dx = x - lastX;
    const dy = y - lastY;
    const steps = Math.max(Math.abs(dx), Math.abs(dy));
    for (let i = 0; i <= steps; i++) {
      const ix = Math.round(lastX + (dx * i) / steps);
      const iy = Math.round(lastY + (dy * i) / steps);
      if (ix >= 0 && ix < SIZE && iy >= 0 && iy < SIZE) {
        pixels[iy][ix] = color;
        socket.emit("pixel_update", { x: ix, y: iy, color });
      }
    }
  } else {
    pixels[y][x] = color;
    socket.emit("pixel_update", { x, y, color });
  }

  lastX = x;
  lastY = y;
}

const clearBtn = document.createElement("button");
clearBtn.textContent = "Clear Canvas";
clearBtn.style.marginLeft = "10px";
document.body.appendChild(clearBtn);

clearBtn.addEventListener("click", () => {
  const pwd = prompt("Enter admin password to clear the canvas:");
  if (pwd === null) return;
  socket.emit("clear_canvas_request", { password: pwd });
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