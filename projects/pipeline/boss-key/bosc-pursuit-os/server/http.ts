import type { ServerResponse } from "node:http";

function isOriginAllowed(origin: string, allowedOrigins: string[]): boolean {
  if (!origin) {
    return true;
  }

  return allowedOrigins.includes("*") || allowedOrigins.includes(origin);
}

export function resolveCorsOrigin(
  requestOrigin: string,
  allowedOrigins: string[],
): string {
  if (!requestOrigin || allowedOrigins.includes("*")) {
    return "*";
  }

  return isOriginAllowed(requestOrigin, allowedOrigins) ? requestOrigin : "";
}

export function sendJson(
  response: ServerResponse,
  payload: unknown,
  statusCode: number,
  requestOrigin: string,
  allowedOrigins: string[],
): void {
  const body = JSON.stringify(payload, null, 2);

  response.writeHead(statusCode, {
    "Access-Control-Allow-Origin": resolveCorsOrigin(requestOrigin, allowedOrigins),
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
  });
  response.end(body);
}

export function sendText(
  response: ServerResponse,
  body: string,
  statusCode: number,
  requestOrigin: string,
  allowedOrigins: string[],
): void {
  response.writeHead(statusCode, {
    "Access-Control-Allow-Origin": resolveCorsOrigin(requestOrigin, allowedOrigins),
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Content-Type": "text/plain; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
  });
  response.end(body);
}
