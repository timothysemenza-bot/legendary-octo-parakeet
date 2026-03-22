const { spawnSync } = require("child_process");
const path = require("path");

const MARKETING_AGENTS_ROOT = path.join(__dirname, "..");
const REPO_ROOT = path.join(MARKETING_AGENTS_ROOT, "..");
const TOOL_PATH = path.join(REPO_ROOT, "proposal-ops", "tools", "sync_company_os.py");

function resolvePythonCommand() {
  const candidates = process.platform === "win32"
    ? [
        { command: "py", prefix: ["-3"] },
        { command: "python", prefix: [] },
      ]
    : [
        { command: "python3", prefix: [] },
        { command: "python", prefix: [] },
      ];

  for (const candidate of candidates) {
    const probe = spawnSync(candidate.command, [...candidate.prefix, "--version"], {
      cwd: REPO_ROOT,
      stdio: "ignore",
    });
    if (probe.status === 0) {
      return candidate;
    }
  }

  throw new Error("Python was not found on PATH.");
}

function main() {
  const python = resolvePythonCommand();
  const args = [...python.prefix, TOOL_PATH, "--mode", "run"];

  if (process.env.COMPANY_OS_SOURCE_CONFIG) {
    args.push("--source-config-path", process.env.COMPANY_OS_SOURCE_CONFIG);
  }
  if (process.env.COMPANY_OS_MARKETING_AGENTS_ROOT) {
    args.push("--marketing-agents-root", process.env.COMPANY_OS_MARKETING_AGENTS_ROOT);
  }
  if (process.env.COMPANY_OS_OWNER) {
    args.push("--owner", process.env.COMPANY_OS_OWNER);
  }

  const result = spawnSync(python.command, args, {
    cwd: REPO_ROOT,
    stdio: "inherit",
  });

  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    process.exitCode = result.status || 1;
  }
}

try {
  main();
} catch (error) {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 1;
}
