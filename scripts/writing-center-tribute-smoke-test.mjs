import { spawn } from "node:child_process";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");
const port = 33117;
const baseUrl = `http://127.0.0.1:${port}`;
const adminToken = "writing-center-smoke-test-token";
const intakePageUrl = `${baseUrl}/boss-key-website/writing-center-alumni-tribute.html`;
const composePageUrl = `${baseUrl}/boss-key-website/writing-center-alumni-tribute-compose.html`;
const displayPageUrl = `${baseUrl}/boss-key-website/writing-center-alumni-tribute-display.html`;

const filesToRestore = [
  path.join(repoRoot, "projects/shared/data/writing-center-tributes/submissions.json"),
  path.join(repoRoot, "projects/shared/data/writing-center-tributes/submissions.csv"),
  path.join(repoRoot, "boss-key-website/data/writing-center-tribute-display.json"),
];

const backups = new Map();

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function snapshotFiles() {
  for (const filePath of filesToRestore) {
    if (fs.existsSync(filePath)) {
      backups.set(filePath, await readFile(filePath, "utf8"));
    } else {
      backups.set(filePath, null);
    }
  }
}

async function restoreFiles() {
  for (const [filePath, content] of backups.entries()) {
    if (content === null) {
      if (fs.existsSync(filePath)) {
        await rm(filePath, { force: true });
      }
      continue;
    }
    await mkdir(path.dirname(filePath), { recursive: true });
    await writeFile(filePath, content, "utf8");
  }
}

async function requestJson(url, options = {}) {
  const headers = { ...(options.headers || {}) };
  let body = options.body;
  if (body && typeof body !== "string" && !(body instanceof Uint8Array)) {
    headers["content-type"] = headers["content-type"] || "application/json";
    body = JSON.stringify(body);
  }
  const response = await fetch(url, {
    ...options,
    headers,
    body,
  });
  const raw = await response.text();
  let data = null;
  if (raw) {
    try {
      data = JSON.parse(raw);
    } catch (error) {
      throw new Error(`Expected JSON from ${url}, received: ${raw.slice(0, 180)}`);
    }
  }
  return { response, data };
}

async function requestText(url, options = {}) {
  const response = await fetch(url, options);
  return { response, text: await response.text() };
}

async function waitForServer() {
  let lastError = null;
  for (let attempt = 0; attempt < 40; attempt += 1) {
    try {
      const { response } = await requestJson(`${baseUrl}/api/writing-center-tributes/published`);
      if (response.ok) {
        return;
      }
      lastError = new Error(`Server responded with ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    await wait(250);
  }
  throw lastError || new Error("Server did not start in time");
}

async function main() {
  console.log("Snapshotting Writing Center data files...");
  await snapshotFiles();

  const server = spawn(process.execPath, ["server.js"], {
    cwd: repoRoot,
    env: {
      ...process.env,
      PORT: String(port),
      WRITING_CENTER_ADMIN_TOKEN: adminToken,
    },
    stdio: ["ignore", "pipe", "pipe"],
  });

  let stdout = "";
  let stderr = "";
  server.stdout.on("data", (chunk) => {
    stdout += chunk.toString();
  });
  server.stderr.on("data", (chunk) => {
    stderr += chunk.toString();
  });

  try {
    await waitForServer();

    const intakeLogoPath = path.join(
      repoRoot,
      "boss-key-website/assets/logos/brand/uconn-writing-center-logo-transparent.png"
    );
    assert(fs.existsSync(intakeLogoPath), "The real Writing Center logo file is missing.");

    const { response: intakePageResponse, text: intakePage } = await requestText(
      intakePageUrl
    );
    assert(intakePageResponse.ok, "The public intake page did not load.");
    assert(
      intakePage.includes("not a fundraising or donation form"),
      "The intake page no longer states that it is not for fundraising or donations."
    );
    assert(
      intakePage.includes("uconn-writing-center-logo-transparent.png"),
      "The intake page is not referencing the real Writing Center logo."
    );

    const uniqueTag = `smoke-${Date.now()}`;
    const interestPayload = {
      full_name: "Smoke Test Alum",
      email: `${uniqueTag}@example.org`,
      graduation_year: "2014",
      current_role_org: "Editor, Example Org",
      linkedin_url: "https://www.linkedin.com/in/smoke-test-alum",
      best_contact_method: "email",
      connection_path: "Tom",
      verification_context:
        "I tutored in the UConn Writing Center, worked with Margie in the front office, and completed ENGL 296 before graduating.",
      network_interest: "Happy to stay in touch for alumni connection and future updates.",
      future_contact_ok: "yes",
      source_page: "/boss-key-website/writing-center-alumni-tribute.html",
    };

    console.log("Submitting interest intake...");
    const { response: intakeResponse, data: intakeResult } = await requestJson(
      `${baseUrl}/api/writing-center-interest`,
      { method: "POST", body: interestPayload }
    );
    assert(intakeResponse.status === 201, `Interest intake failed with ${intakeResponse.status}.`);
    assert(intakeResult?.submission_id, "Interest intake did not return a submission id.");

    console.log("Loading review queue...");
    const { response: reviewResponse, data: reviewQueue } = await requestJson(
      `${baseUrl}/api/writing-center-tributes/review`,
      {
        headers: {
          "x-admin-token": adminToken,
        },
      }
    );
    assert(reviewResponse.ok, "The review queue did not load.");
    const reviewItem = (reviewQueue?.items || []).find(
      (item) => item.submission_id === intakeResult.submission_id
    );
    assert(reviewItem, "The new interest record was not found in the review queue.");
    assert(
      Number.isFinite(Number(reviewItem.vetting_score)),
      "The review queue did not include a vetting score."
    );
    assert(reviewItem.vetting_summary, "The review queue did not include a vetting summary.");

    console.log("Approving the interest record...");
    const { response: approvalResponse, data: approvalResult } = await requestJson(
      `${baseUrl}/api/writing-center-tributes/${intakeResult.submission_id}`,
      {
        method: "PUT",
        headers: {
          "x-admin-token": adminToken,
        },
        body: {
          interest_status: "approved",
          invite_status: "generated",
          review_status: "not_submitted",
          interest_review_notes: "Smoke test approval.",
          vetting_review_notes: "Smoke test confirms the workflow can be reviewed locally.",
        },
      }
    );
    assert(approvalResponse.ok, "Approving the interest record failed.");
    const inviteToken = approvalResult?.item?.invite_token;
    assert(inviteToken, "Approving the interest record did not generate an invite token.");

    const { response: composePageResponse, text: composePage } = await requestText(
      composePageUrl
    );
    assert(composePageResponse.ok, "The invite-only compose page did not load.");
    assert(
      composePage.includes("not a fundraising or donation page"),
      "The invite-only page is missing the non-fundraising clarification."
    );
    assert(
      composePage.includes("uconn-writing-center-logo-transparent.png"),
      "The invite-only page is not referencing the real Writing Center logo."
    );

    console.log("Loading invite details...");
    const { response: inviteResponse, data: inviteRecord } = await requestJson(
      `${baseUrl}/api/writing-center-invites/${inviteToken}`
    );
    assert(inviteResponse.ok, "The generated invite token did not resolve.");
    assert(inviteRecord?.full_name === "Smoke Test Alum", "Invite payload did not match the saved alum.");

    console.log("Submitting tribute content...");
    const { response: tributeResponse } = await requestJson(
      `${baseUrl}/api/writing-center-invites/${inviteToken}/tribute`,
      {
        method: "POST",
        body: {
          preferred_display_name: "Smoke Test Alum",
          current_role_org: "Editor, Example Org",
          share_permission: "yes",
          display_permission: "yes",
          written_note:
            "Margie made the Writing Center feel organized, warm, and steady for everyone who walked through it.",
        },
      }
    );
    assert(tributeResponse.status === 201, "Submitting the tribute content failed.");

    console.log("Approving the tribute for display...");
    const { response: publishResponse } = await requestJson(
      `${baseUrl}/api/writing-center-tributes/${intakeResult.submission_id}`,
      {
        method: "PUT",
        headers: {
          "x-admin-token": adminToken,
        },
        body: {
          interest_status: "approved",
          invite_status: "tribute_submitted",
          review_status: "approved",
          publish_to_screen: "yes",
          published_display_name: "Smoke Test Alum",
          published_role_org: "Editor, Example Org",
          published_note:
            "Margie made the Writing Center feel organized, warm, and steady for everyone who walked through it.",
          review_notes: "Smoke test approval for display.",
        },
      }
    );
    assert(publishResponse.ok, "Approving the tribute for display failed.");

    console.log("Checking published display feed...");
    const { response: feedResponse, data: feed } = await requestJson(
      `${baseUrl}/api/writing-center-tributes/published`
    );
    assert(feedResponse.ok, "The published display feed did not load.");
    const feedItem = (feed?.items || []).find((item) => item.id === intakeResult.submission_id);
    assert(feedItem, "The approved tribute did not reach the published display feed.");

    const { response: displayPageResponse, text: displayPage } = await requestText(
      displayPageUrl
    );
    assert(displayPageResponse.ok, "The reception display page did not load.");
    assert(
      displayPage.includes("uconn-writing-center-logo-transparent.png"),
      "The display page is not referencing the real Writing Center logo."
    );

    console.log("Writing Center smoke test passed.");
  } finally {
    server.kill();
    await wait(300);
    await restoreFiles();
    if (stderr.trim()) {
      console.log("Server stderr:");
      console.log(stderr.trim());
    }
    if (server.exitCode && server.exitCode !== 0) {
      console.log("Server stdout:");
      console.log(stdout.trim());
      throw new Error(`Smoke test server exited with code ${server.exitCode}.`);
    }
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
