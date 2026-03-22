const fs = require('fs');
const path = require('path');

function env(name, fallback = '') {
  return process.env[name] || fallback;
}

function canonicalJoinUrl() {
  return env('JWBLNG_CANONICAL_JOIN_URL', '/#block-1772192187104_0').trim();
}

function canonicalJoinHref() {
  const joinUrl = canonicalJoinUrl();
  if (/^https?:\/\//i.test(joinUrl)) return joinUrl;

  const publicUrl = env('JWBLNG_PUBLIC_URL', '').trim().replace(/\/+$/, '');
  if (!publicUrl) return joinUrl;

  return `${publicUrl}${joinUrl.startsWith('/') ? joinUrl : `/${joinUrl}`}`;
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
  canonicalJoinHref,
  canonicalJoinUrl,
  env,
  requireEnv,
  writesAllowed,
  ensureArtifactsDir,
  adminBaseUrl,
};
