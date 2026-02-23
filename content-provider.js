const fs = require("fs");
const https = require("https");
const path = require("path");
const { URL } = require("url");

const REQUIRED_LIBRARY_KEYS = ["industryGraphics", "geography", "serviceLevel", "siteType", "risk", "coverage", "capabilities"];

function isPlainObject(value) {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function isIndustryGraphicsMap(value) {
  if (!isPlainObject(value)) return false;
  return Object.values(value).every((item) => Array.isArray(item));
}

function isValidLibraryPayload(payload) {
  if (!isPlainObject(payload)) return false;
  if (!isIndustryGraphicsMap(payload[REQUIRED_LIBRARY_KEYS[0]])) return false;
  for (const key of REQUIRED_LIBRARY_KEYS.slice(1)) {
    if (!isPlainObject(payload[key])) return false;
  }
  return true;
}

function normalizeString(value, fallback = "") {
  const text = String(value || "").trim();
  return text || fallback;
}

function sanitizeCapabilityList(capabilities = []) {
  if (!Array.isArray(capabilities)) return [];
  return capabilities.map((value) => String(value || "").trim()).filter(Boolean);
}

function getFirst(list, fallback = null) {
  return list && list.length ? list[0] : fallback;
}

function isReadablePath(value) {
  if (typeof value !== "string") return false;
  const text = value.trim();
  if (!text) return false;
  return (
    text.startsWith("http://") ||
    text.startsWith("https://") ||
    text.startsWith("content:") ||
    text.startsWith("file:") ||
    text.startsWith("/") ||
    text.startsWith("./") ||
    text.startsWith("../") ||
    /\.(txt|md|mdx|json|yaml|yml|html|htm)$/i.test(text)
  );
}

function stripSourcePrefix(value) {
  if (typeof value !== "string") return "";
  const text = value.trim();
  if (text.startsWith("content://")) return text.slice("content://".length);
  if (text.startsWith("file://")) return text.slice("file://".length);
  if (text.startsWith("content:")) return text.slice("content:".length);
  if (text.startsWith("file:")) return text.slice("file:".length);
  return text;
}

async function readTextFromFile(filePath) {
  const raw = await fs.promises.readFile(filePath, "utf8");
  return raw;
}

function detectFileExtension(value) {
  const candidate = String(value || "").trim().toLowerCase();
  const dot = candidate.lastIndexOf(".");
  return dot === -1 ? "" : candidate.slice(dot + 1);
}

function toText(value) {
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) return value.filter((line) => typeof line === "string" && line.trim()).join("\n");
  return typeof value === "string" ? value : String(value);
}

function toStringArray(value) {
  if (Array.isArray(value)) {
    return value.filter((line) => typeof line === "string").map((line) => line.trim()).filter(Boolean);
  }
  if (typeof value === "string") {
    return value
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);
  }
  return [];
}

async function fetchTextFromUrl(targetUrl, headers = {}) {
  return new Promise((resolve, reject) => {
    let parsed;
    try {
      parsed = new URL(targetUrl);
    } catch (error) {
      reject(error);
      return;
    }

    if (!/^https?:$/.test(parsed.protocol)) {
      reject(new Error(`Unsupported protocol: ${parsed.protocol}`));
      return;
    }

    const request = https.request(
      parsed,
      {
        method: "GET",
        headers: {
          Accept: "application/octet-stream",
          ...headers,
        },
      },
      (response) => {
        if (response.statusCode < 200 || response.statusCode >= 300) {
          const status = response.statusCode || "unknown";
          reject(new Error(`Request failed (${status}) for ${targetUrl}`));
          return;
        }
        response.setEncoding("utf8");
        let body = "";
        response.on("data", (chunk) => {
          body += chunk;
        });
        response.on("end", () => resolve(body));
      }
    );

    request.on("error", reject);
    request.end();
  });
}

function resolveGraphUrl(settings, targetPath) {
  const siteId = settings.siteId;
  const driveId = settings.driveId;
  if (!siteId || !driveId) {
    throw new Error("CONTENT_PROVIDER_SETTINGS missing siteId/driveId");
  }
  const basePath = stripSourcePrefix(targetPath || "").replace(/^\/+/, "");
  const graphBase = settings.graphBaseUrl || "https://graph.microsoft.com/v1.0";
  const encoded = encodeURIComponent(basePath).replace(/%2F/g, "/");
  return `${graphBase}/sites/${siteId}/drives/${driveId}/root:/${encoded}:/content`;
}

async function fetchContentForSharePoint(settings, targetPath) {
  const token = settings.accessToken || process.env.GRAPH_ACCESS_TOKEN;
  const normalizedPath = stripSourcePrefix(targetPath || "").trim();
  if (!normalizedPath) throw new Error("Empty content path");

  const headers = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  if (/^https?:\/\/\S+/i.test(normalizedPath)) {
    return fetchTextFromUrl(normalizedPath, headers);
  }

  const root = (settings.basePath || settings.contentPath || "").trim();
  const useGraph = !!(settings.siteId && settings.driveId);
  if (useGraph) {
    const sourcePath = root ? `${root.replace(/\/+$/, "")}/${normalizedPath}` : normalizedPath;
    const url = resolveGraphUrl(settings, sourcePath);
    return fetchTextFromUrl(url, headers);
  }

  const localPath = root ? path.join(root, normalizedPath) : normalizedPath;
  if (isReadablePath(localPath) && !path.isAbsolute(localPath)) {
    return readTextFromFile(path.resolve(process.cwd(), localPath));
  }
  return readTextFromFile(localPath);
}

async function resolveSourceValue(provider, value) {
  if (!isReadablePath(value)) return value;
  const source = stripSourcePrefix(String(value || ""));
  try {
    const raw = await fetchContentForSharePoint(provider.settings, source);
    const ext = detectFileExtension(source);
    if (ext === "json") {
      const parsed = JSON.parse(raw);
      return parsed;
    }
    return raw;
  } catch (_error) {
    return value;
  }
}

async function resolveLibrarySection(section, provider) {
  if (!isPlainObject(section)) return section;
  const next = { ...section };
  if ("summary" in next) {
    const resolved = await resolveSourceValue(provider, next.summary);
    next.summary = toText(resolved);
  }
  if ("description" in next) {
    const resolved = await resolveSourceValue(provider, next.description);
    next.description = toText(resolved);
  }
  if ("scopeBullets" in next) {
    const resolved = await resolveSourceValue(provider, next.scopeBullets);
    next.scopeBullets = toStringArray(resolved);
  }
  if ("timeline" in next) {
    const resolved = await resolveSourceValue(provider, next.timeline);
    next.timeline = toStringArray(resolved);
  }
  if ("exclusions" in next) {
    const resolved = await resolveSourceValue(provider, next.exclusions);
    next.exclusions = toStringArray(resolved);
  }
  if ("body" in next && next.body && isReadablePath(next.body)) {
    next.body = toText(await resolveSourceValue(provider, next.body));
  }
  return next;
}

async function resolveLibraryPayload(payload, provider) {
  if (!isPlainObject(payload)) return payload;
  const nextPayload = { ...payload };
  const mapKeys = ["geography", "serviceLevel", "siteType", "risk", "coverage", "capabilities"];
  for (const key of mapKeys) {
    const catalog = payload[key];
    if (!isPlainObject(catalog)) continue;
    const nextCatalog = {};
    for (const [name, section] of Object.entries(catalog)) {
      if (isPlainObject(section)) {
        nextCatalog[name] = await resolveLibrarySection(section, provider);
      } else {
        nextCatalog[name] = section;
      }
    }
    nextPayload[key] = nextCatalog;
  }

  if (isPlainObject(payload.industryGraphics)) {
    const nextIndustry = {};
    for (const [name, list] of Object.entries(payload.industryGraphics)) {
      if (!Array.isArray(list)) {
        nextIndustry[name] = [];
        continue;
      }
      const nextList = [];
      for (const option of list) {
        if (!isPlainObject(option)) {
          nextList.push(option);
          continue;
        }
        const resolvedOption = await resolveLibrarySection(option, provider);
        if ("body" in resolvedOption && resolvedOption.body && isReadablePath(resolvedOption.body)) {
          resolvedOption.body = toText(await resolveSourceValue(provider, resolvedOption.body));
        }
        nextList.push(resolvedOption);
      }
      nextIndustry[name] = nextList;
    }
    nextPayload.industryGraphics = nextIndustry;
  }

  return nextPayload;
}

function resolveIndustryOption(library, industry) {
  const options = isPlainObject(library.industryGraphics) ? library.industryGraphics[industry] : [];
  if (!Array.isArray(options) || !options.length) return null;
  return options[0];
}

function buildPackageSelections(intake, library) {
  const selections = [];
  const seen = new Set();
  const add = (id, title, reason) => {
    const key = String(id || "");
    if (!key || seen.has(key)) return;
    seen.add(key);
    selections.push({
      id: key,
      title: String(title || key),
      reason: reason || "auto-selected",
    });
  };

  const geography = library.geography?.[intake.geography] || library.geography?.Default || {};
  const service = library.serviceLevel?.[intake.serviceLevel] || library.serviceLevel?.Enhanced || {};
  const site = library.siteType?.[intake.siteType] || library.siteType?.["Corporate office"] || {};
  const risk = library.risk?.[intake.riskLevel] || library.risk?.Medium || {};
  const coverage = library.coverage?.[intake.coverageHours] || library.coverage?.["Business hours"] || {};

  add(`geography:${intake.geography || "Default"}`, geography.title || "Regional context", "Dropdown: geography");
  add(`service:${intake.serviceLevel || "Enhanced"}`, service.title || "Service package", "Dropdown: service level");
  add(`site:${intake.siteType || "Corporate office"}`, site.title || "Site package", "Dropdown: site type");
  add(`risk:${intake.riskLevel || "Medium"}`, risk.title || "Risk package", "Dropdown: risk level");
  add(`coverage:${intake.coverageHours || "Business hours"}`, coverage.title || "Coverage package", "Dropdown: coverage window");

  const industryOption = resolveIndustryOption(library, intake.industry || intake.siteType || "Corporate office");
  if (industryOption) {
    add(`industry:${industryOption.id || intake.siteType || "default"}`, industryOption.title || "Industry visual", "Derived from site type");
  }

  intake.capabilities.forEach((capability) => {
    const entry = library.capabilities?.[capability];
    add(`capability:${capability}`, entry?.title || capability, "Capability checkbox");
  });

  return selections;
}

function buildSection(title, paragraphs = [], bullets = [], graphic = null) {
  return {
    title: String(title || ""),
    paragraphs: paragraphs.filter((line) => typeof line === "string").map((line) => String(line)),
    bullets: bullets.filter((line) => typeof line === "string").map((line) => String(line)),
    graphic,
  };
}

function toInlineGraphic(option, sourceLabel = "industry visual") {
  if (!option || typeof option !== "object") return null;
  if (!option.source && !option.inline && !option.graphic && !option.wordImage) return null;
  return {
    label: option.label || sourceLabel,
    inline: option.inline || option.graphic || "",
    wordImage: option.source || option.image || option.imageUrl || option.src || option.wordImage || "",
    alt: option.description || option.title || sourceLabel,
  };
}

function buildSectionsFromLibrary(intake, library) {
  const geography = library.geography?.[intake.geography] || library.geography?.Default || {};
  const service = library.serviceLevel?.[intake.serviceLevel] || library.serviceLevel?.Enhanced || {};
  const site = library.siteType?.[intake.siteType] || library.siteType?.["Corporate office"] || {};
  const risk = library.risk?.[intake.riskLevel] || library.risk?.Medium || {};
  const coverage = library.coverage?.[intake.coverageHours] || library.coverage?.["Business hours"] || {};

  const selectedCapabilities = intake.capabilities
    .map((capability) => library.capabilities?.[capability] || null)
    .filter(Boolean);
  const industryOption = resolveIndustryOption(library, intake.industry || intake.siteType || "Corporate office");

  const sections = [];
  sections.push(
    buildSection(
      geography.title || `${intake.geography || "Selected"} geography context`,
      [`${geography.summary || "Regional context included for this proposal."}`],
      geography.scopeBullets || []
    )
  );
  sections.push(
    buildSection(
      service.title || "Service profile",
      [service.summary || "", intake.keyConcerns ? `Priority concern: ${intake.keyConcerns}` : "Priority concerns to confirm at kickoff."],
      service.scopeBullets || [],
      toInlineGraphic(service, "Service visual")
    )
  );
  sections.push(buildSection(site.title || "Site profile", ["Site profile is configured from the facility type selection."], site.scopeBullets || [], toInlineGraphic(site, "Site visual")));
  sections.push(buildSection(risk.title || "Risk profile", [`Risk profile: ${intake.riskLevel} at ${intake.startWindow}.`], risk.scopeBullets || []));
  if (industryOption) {
    sections.push(buildSection(industryOption.title || `${intake.industry || "Industry"} visual`, [industryOption.description || "Industry visual selected automatically."], [], toInlineGraphic(industryOption, "Industry visual")));
  }
  sections.push(buildSection(coverage.title || "Coverage profile", [`Coverage selected: ${intake.coverageHours}.`], coverage.scopeBullets || []));

  selectedCapabilities.forEach((capability) => {
    sections.push(
      buildSection(
        capability.title || "Capability",
        [`Selection pulled from capability library: ${capability.title || ""}.`],
        capability.scopeBullets || [],
        toInlineGraphic(capability, "Capability visual")
      )
    );
  });

  const timeline = [
    "Day 1-3: contract review and kickoff.",
    `Day 4-14: onboarding and access provisioning (${intake.startWindow}).`,
    "Week 3: pilot shifts and escalation drill.",
    "Week 4: first KPI review.",
    ...(service.timeline || []),
    ...(site.timeline || []),
    ...(risk.timeline || []),
    ...(coverage.timeline || []),
    ...(geography.timeline || []),
    ...selectedCapabilities.flatMap((capability) => capability.timeline || []),
  ];

  const exclusions = [
    "Permits and third-party certifications are billed separately.",
    "Overtime outside agreed coverage windows is billed separately.",
    "Long-term hardware refresh is not included in this base scope.",
    ...(service.exclusions || []),
    ...(site.exclusions || []),
    ...(risk.exclusions || []),
    ...(coverage.exclusions || []),
    ...(geography.exclusions || []),
    ...selectedCapabilities.flatMap((capability) => capability.exclusions || []),
  ];

  const scopeLines = [
    `Facility count: ${intake.facilities} site${intake.facilities === 1 ? "" : "s"}`,
    `Geography: ${intake.geography || "Default"}`,
    `Service level: ${intake.serviceLevel}`,
    `Contract length: ${intake.contractLength}`,
    `Selected capabilities: ${intake.capabilities.join(", ")}`,
  ];

  return {
    packageSelections: buildPackageSelections(intake, library),
    sections,
    timeline: [...new Set(timeline.filter(Boolean))],
    exclusions: [...new Set(exclusions.filter(Boolean))],
    scope: scopeLines,
  };
}

class JsonContentProvider {
  constructor(options = {}) {
    this.mode = "json";
    this.file = options.file ? path.resolve(options.file) : path.resolve(process.cwd(), "content-library.json");
    this.library = {};
  }

  async init() {
    await this.reload();
    return this;
  }

  getStatus() {
    return {
      provider: this.mode,
      file: this.file,
      loaded: isValidLibraryPayload(this.library),
      lastLoadUtc: this.lastLoadUtc || null,
    };
  }

  async reload() {
    try {
      const raw = fs.readFileSync(this.file, "utf8");
      const parsed = JSON.parse(raw);
      if (!isValidLibraryPayload(parsed)) {
        throw new Error("Invalid library payload");
      }
      this.library = parsed;
      this.lastLoadUtc = new Date().toISOString();
      return this.library;
    } catch {
      this.library = {};
      this.lastLoadUtc = new Date().toISOString();
      return this.library;
    }
  }

  async getLibrary() {
    if (!this.lastLoadUtc) {
      await this.reload();
    }
    return this.library;
  }

  async saveLibrary(payload) {
    if (!isValidLibraryPayload(payload)) {
      throw new Error("Invalid library payload");
    }
    this.library = payload;
    this.lastLoadUtc = new Date().toISOString();
    fs.writeFileSync(this.file, JSON.stringify(payload, null, 2), "utf8");
    return this.library;
  }

  async resolve(intake) {
    const library = await this.getLibrary();
    const normalized = this.normalizeIntake(intake);
    return buildSectionsFromLibrary(normalized, library);
  }

  normalizeIntake(value = {}) {
    return {
      companyName: normalizeString(value.companyName, ""),
      primaryContact: normalizeString(value.primaryContact, ""),
      contactEmail: normalizeString(value.contactEmail, ""),
      phone: normalizeString(value.phone, ""),
      location: normalizeString(value.location, ""),
      geography: normalizeString(value.geography, "US Northeast"),
      facilities: Number.isInteger(value.facilities) ? value.facilities : Number(value.facilities || 1),
      siteType: normalizeString(value.siteType, "Corporate office"),
      industry: normalizeString(value.industry, value.siteType || "Corporate office"),
      coverageHours: normalizeString(value.coverageHours, "Business hours"),
      riskLevel: normalizeString(value.riskLevel, "Medium"),
      startWindow: normalizeString(value.startWindow, "2-4 weeks"),
      keyConcerns: normalizeString(value.keyConcerns, ""),
      serviceLevel: normalizeString(value.serviceLevel, "Enhanced"),
      capabilities: sanitizeCapabilityList(value.capabilities || []),
      budgetBand: normalizeString(value.budgetBand, "Under $6,000"),
      contractLength: normalizeString(value.contractLength, "6 months"),
    };
  }
}

class SharePointContentProvider extends JsonContentProvider {
  constructor(options = {}) {
    super(options);
    this.mode = "sharepoint";
    this.settings = options.settings || {};
    this.rawLibrary = {};
  }

  async init() {
    await this.reload();
    return this;
  }

  resolveAuthHeaders() {
    const token = this.settings.accessToken || process.env.GRAPH_ACCESS_TOKEN;
    if (!token) return {};
    return {
      Authorization: `Bearer ${token}`,
    };
  }

  async loadManifest() {
    const manifestSource = this.settings.manifestFile || this.settings.manifestPath;
    if (!manifestSource) {
      if (this.settings.siteId && this.settings.driveId) {
        const manifestPath = this.settings.manifestPath || "content-manifest.json";
        return fetchContentForSharePoint(this.settings, manifestPath);
      }
      throw new Error("SharePoint provider requires manifestFile or siteId/driveId/manifestPath");
    }
    if (/^https?:\/\//i.test(manifestSource)) {
      return fetchTextFromUrl(manifestSource, this.resolveAuthHeaders());
    }
    const resolved = path.resolve(process.cwd(), stripSourcePrefix(manifestSource));
    return readTextFromFile(resolved);
  }

  getStatus() {
    return {
      ...super.getStatus(),
      provider: this.mode,
      message:
        "SharePoint provider is active. Use manifestFile or Graph settings to point to a structured content source.",
      configuredDrive: !!this.settings.driveId,
      configuredSite: !!this.settings.siteId,
      manifestConfigured: !!(this.settings.manifestFile || this.settings.manifestPath || this.settings.siteId),
    };
  }

  async reload() {
    const rawPayload = await this.loadManifest();
    const parsed = JSON.parse(rawPayload);
    if (!isValidLibraryPayload(parsed)) {
      throw new Error("Invalid library payload from SharePoint provider");
    }
    this.rawLibrary = parsed;
    const resolved = await resolveLibraryPayload(parsed, this);
    this.library = resolved;
    this.lastLoadUtc = new Date().toISOString();
    return this.library;
  }

  async getLibrary() {
    if (!this.lastLoadUtc) {
      await this.reload();
    }
    if (Object.keys(this.rawLibrary || {}).length) {
      this.library = await resolveLibraryPayload(this.rawLibrary, this);
    } else {
      this.library = this.rawLibrary;
    }
    return this.library;
  }

  async saveLibrary() {
    throw new Error("SharePoint provider is read-only in this mode.");
  }

  async resolve(intake) {
    if (!this.lastLoadUtc) {
      await this.reload();
    }
    const library = await this.getLibrary();
    const normalized = this.normalizeIntake(intake);
    return buildSectionsFromLibrary(normalized, library);
  }
}

function createContentProvider(options = {}) {
  const providerName = String(options.provider || "json").toLowerCase();
  if (providerName === "sharepoint") {
    return new SharePointContentProvider(options);
  }
  return new JsonContentProvider(options);
}

module.exports = {
  createContentProvider,
  isValidLibraryPayload,
  buildSectionsFromLibrary,
};
