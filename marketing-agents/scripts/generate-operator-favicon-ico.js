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
    for (let xx = x; xx < x + w; xx += 1) {
      setPixel(xx, yy, r, g, b, a);
    }
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

function roundedBg() {
  fillRect(0, 0, size, size, 11, 15, 23, 255);
  const cut = 5;
  for (let y = 0; y < cut; y += 1) {
    for (let x = 0; x < cut; x += 1) {
      const d = Math.hypot(cut - x, cut - y);
      if (d > cut) {
        setPixel(x, y, 11, 15, 23, 0);
        setPixel(size - 1 - x, y, 11, 15, 23, 0);
        setPixel(x, size - 1 - y, 11, 15, 23, 0);
        setPixel(size - 1 - x, size - 1 - y, 11, 15, 23, 0);
      }
    }
  }
}

function drawGlyph() {
  // White "B-like" form
  fillRect(8, 7, 4, 19, 245, 247, 251, 255);
  fillRect(12, 7, 8, 4, 245, 247, 251, 255);
  fillRect(12, 14, 8, 4, 245, 247, 251, 255);
  fillRect(12, 22, 8, 4, 245, 247, 251, 255);
  fillRect(19, 10, 2, 4, 11, 15, 23, 255);
  fillRect(19, 18, 2, 4, 11, 15, 23, 255);

  // Blue accent stroke + dot
  drawLine(18, 18, 26, 26, 2.8, 62, 166, 255, 255);
  fillCircle(26, 26, 2.6, 62, 166, 255, 255);
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
  bi.writeInt32LE(0, 24);
  bi.writeInt32LE(0, 28);
  bi.writeUInt32LE(0, 32);
  bi.writeUInt32LE(0, 36);

  const xor = Buffer.alloc(xorSize);
  for (let y = 0; y < height; y += 1) {
    const srcRow = y;
    const dstRow = height - 1 - y; // BMP bottom-up
    bgra.copy(xor, dstRow * width * 4, srcRow * width * 4, srcRow * width * 4 + width * 4);
  }

  const andMask = Buffer.alloc(andSize, 0);
  const imageData = Buffer.concat([bi, xor, andMask]);

  const iconDir = Buffer.alloc(6);
  iconDir.writeUInt16LE(0, 0);
  iconDir.writeUInt16LE(1, 2);
  iconDir.writeUInt16LE(1, 4);

  const entry = Buffer.alloc(16);
  entry.writeUInt8(width === 256 ? 0 : width, 0);
  entry.writeUInt8(height === 256 ? 0 : height, 1);
  entry.writeUInt8(0, 2);
  entry.writeUInt8(0, 3);
  entry.writeUInt16LE(1, 4);
  entry.writeUInt16LE(32, 6);
  entry.writeUInt32LE(imageData.length, 8);
  entry.writeUInt32LE(6 + 16, 12);

  return Buffer.concat([iconDir, entry, imageData]);
}

roundedBg();
drawGlyph();

const ico = buildIcoFromBmp32(pixels, size, size);
const outPath = path.join(process.cwd(), "marketing-agents", "app", "favicon.ico");
fs.writeFileSync(outPath, ico);
console.log(`Wrote ${outPath}`);
