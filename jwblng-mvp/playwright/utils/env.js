const fs = require('fs');
const path = require('path');

function env(name, fallback = '') {
  return process.env[name] || fallback;
}

function requireEnv(name) {
  const value = env(name);
  if (!value) {
    throw new Error(`Missing required env var: ${name}`);
  }
  return value;
}

function writesAllowed() {
  return env('ALLOW_KAJABI_WRITES', '0') === '1';
}

function ensureArtifactsDir() {
  const dir = path.join(__dirname, '..', 'artifacts');
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  return dir;
}

function adminBaseUrl() {
  const scoped = env('KAJABI_ADMIN_BASE_URL', '').trim().replace(/\/+$/, '');
  if (scoped) return scoped;

  const base = requireEnv('KAJABI_BASE_URL').trim().replace(/\/+$/, '');
  return `${base}/admin`;
}

module.exports = {
  env,
  requireEnv,
  writesAllowed,
  ensureArtifactsDir,
  adminBaseUrl,
};
