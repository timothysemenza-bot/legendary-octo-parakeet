const fs = require("fs");
const path = require("path");

const size = 32;
const pixels = Buffer.alloc(size * size * 4, 0);

function setPixel(x, y, r, g, b, a = 255) {
  if (x < 0 || y < 0 || x >= size || y >= size) return;
  const i = (y * size + x) * 4;
  pixels[i + 0] = b;
  pixels[i + 1] = g;
  pixels[i + 2] = r;
  pixels[i + 3] = a;
}

function fillRect(x, y, w, h, r, g, b, a = 255) {
  for (let yy = y; yy < y + h; yy += 1) {
    for (let xx = x; xx < x + w; xx += 1) setPixel(xx, yy, r, g, b, a);
  }
}

function fillCircle(cx, cy, radius, r, g, b, a = 255) {
  const rr = radius * radius;
  for (let yy = Math.floor(cy - radius); yy <= Math.ceil(cy + radius); yy += 1) {
    for (let xx = Math.floor(cx - radius); xx <= Math.ceil(cx + radius); xx += 1) {
      const dx = xx - cx;
      const dy = yy - cy;
      if (dx * dx + dy * dy <= rr) setPixel(xx, yy, r, g, b, a);
    }
  }
}

function drawLine(x1, y1, x2, y2, thickness, r, g, b, a = 255) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.max(Math.abs(dx), Math.abs(dy));
  for (let i = 0; i <= len; i += 1) {
    const t = len === 0 ? 0 : i / len;
    const x = x1 + dx * t;
    const y = y1 + dy * t;
    fillCircle(x, y, thickness / 2, r, g, b, a);
  }
}

function drawPolyline(points, thickness, r, g, b, close = false) {
  for (let i = 0; i < points.length - 1; i += 1) {
    drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1], thickness, r, g, b);
  }
  if (close && points.length > 2) {
    const p0 = points[0];
    const pN = points[points.length - 1];
    drawLine(pN[0], pN[1], p0[0], p0[1], thickness, r, g, b);
  }
}

function roundedCornersTransparent(radius) {
  for (let y = 0; y < radius; y += 1) {
    for (let x = 0; x < radius; x += 1) {
      const d = Math.hypot(radius - x, radius - y);
      if (d > radius) {
        setPixel(x, y, 0, 0, 0, 0);
        setPixel(size - 1 - x, y, 0, 0, 0, 0);
        setPixel(x, size - 1 - y, 0, 0, 0, 0);
        setPixel(size - 1 - x, size - 1 - y, 0, 0, 0, 0);
      }
    }
  }
}

function buildIcoFromBmp32(bgra, width, height) {
  const xorSize = width * height * 4;
  const andRowBytes = Math.ceil(width / 32) * 4;
  const andSize = andRowBytes * height;

  const bi = Buffer.alloc(40);
  bi.writeUInt32LE(40, 0);
  bi.writeInt32LE(width, 4);
  bi.writeInt32LE(height * 2, 8);
  bi.writeUInt16LE(1, 12);
  bi.writeUInt16LE(32, 14);
  bi.writeUInt32LE(0, 16);
  bi.writeUInt32LE(xorSize + andSize, 20);

  const xor = Buffer.alloc(xorSize);
  for (let y = 0; y < height; y += 1) {
    const srcRow = y;
    const dstRow = height - 1 - y;
    bgra.copy(xor, dstRow * width * 4, srcRow * width * 4, srcRow * width * 4 + width * 4);
  }
  const andMask = Buffer.alloc(andSize, 0);
  const imageData = Buffer.concat([bi, xor, andMask]);

  const iconDir = Buffer.alloc(6);
  iconDir.writeUInt16LE(0, 0);
  iconDir.writeUInt16LE(1, 2);
  iconDir.writeUInt16LE(1, 4);

  const entry = Buffer.alloc(16);
  entry.writeUInt8(width, 0);
  entry.writeUInt8(height, 1);
  entry.writeUInt16LE(1, 4);
  entry.writeUInt16LE(32, 6);
  entry.writeUInt32LE(imageData.length, 8);
  entry.writeUInt32LE(22, 12);

  return Buffer.concat([iconDir, entry, imageData]);
}

// Website favicon style colors
const bg = [245, 247, 251];
const stroke = [11, 16, 32];
const accent = [197, 22, 46];

fillRect(0, 0, size, size, bg[0], bg[1], bg[2], 255);
roundedCornersTransparent(5);

// Outer eight-sided frame (scaled from website favicon geometry)
const oct = [
  [7, 4], [25, 4], [28, 7], [28, 25], [25, 28], [7, 28], [4, 25], [4, 7],
];
drawPolyline(oct, 1.9, stroke[0], stroke[1], stroke[2], true);

// Inner diamond
const diamond = [[16, 10], [22, 16], [16, 22], [10, 16]];
drawPolyline(diamond, 1.9, stroke[0], stroke[1], stroke[2], true);

// Top vertical line
drawLine(16, 4, 16, 10, 1.9, stroke[0], stroke[1], stroke[2]);

// Red accent dot
fillCircle(20.5, 16, 1.4, accent[0], accent[1], accent[2], 255);

const ico = buildIcoFromBmp32(pixels, size, size);
const outPath = path.join(process.cwd(), "marketing-agents", "app", "company-favicon.ico");
fs.writeFileSync(outPath, ico);
console.log(`Wrote ${outPath}`);
