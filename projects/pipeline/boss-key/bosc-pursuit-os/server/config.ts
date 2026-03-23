import { config as loadEnv } from "dotenv";
import { fileURLToPath } from "node:url";
import path from "node:path";

const PROJECT_ROOT = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);

loadEnv({ path: path.join(PROJECT_ROOT, ".env"), quiet: true });
loadEnv({
  path: path.join(PROJECT_ROOT, ".env.local"),
  override: true,
  quiet: true,
});

function readNumberEnv(name: string, fallback: number): number {
  const raw = process.env[name];
  if (!raw) {
    return fallback;
  }

  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function readBooleanEnv(name: string, fallback: boolean): boolean {
  const raw = process.env[name];
  if (!raw) {
    return fallback;
  }

  return !["0", "false", "False", "FALSE"].includes(raw);
}

function readCorsOrigins(): string[] {
  return (process.env.BOSSKEY_IMPORT_CORS_ORIGINS || "*")
    .split(",")
    .map((origin) => origin.trim())
    .filter(Boolean);
}

export const serverConfig = {
  projectRoot: PROJECT_ROOT,
  port: readNumberEnv("BOSSKEY_IMPORT_PORT", 4174),
  corsOrigins: readCorsOrigins(),
  openAiApiKey: process.env.OPENAI_API_KEY?.trim() || "",
  openAiModel: process.env.BOSSKEY_OPENAI_MODEL?.trim() || "gpt-5.4-mini",
  openAiTimeoutMs:
    readNumberEnv("BOSSKEY_OPENAI_EXTRACT_TIMEOUT_SECONDS", 120) * 1000,
  openAiReasoningEffort:
    (process.env.BOSSKEY_OPENAI_REASONING_EFFORT?.trim() || "low") as
      | "minimal"
      | "low"
      | "medium"
      | "high",
  enableModelImport: readBooleanEnv("BOSSKEY_IMPORT_ENABLE_MODEL", true),
  allowHeuristicFallback: readBooleanEnv(
    "BOSSKEY_IMPORT_ALLOW_HEURISTIC_FALLBACK",
    true,
  ),
  maxFileBytes: readNumberEnv("BOSSKEY_IMPORT_MAX_FILE_BYTES", 20 * 1024 * 1024),
  maxTotalCharacters: readNumberEnv("BOSSKEY_IMPORT_MAX_TOTAL_CHARACTERS", 120000),
  maxFileCount: readNumberEnv("BOSSKEY_IMPORT_MAX_FILE_COUNT", 8),
};

export type ServerConfig = typeof serverConfig;
