import {
  formatOpportunityValidationError,
  parseOpportunity,
  type Opportunity,
  type ServiceType,
} from "../domain/opportunity";
import {
  operatorWorkspaceStateSchema,
  type OperatorWorkspaceState,
} from "../domain/operatorWorkspace";
import type { OpportunityImportResult } from "../domain/opportunityImportResult";

const ENTITY_NAME_PATTERN =
  /(?:Library|Department|District|County|City|Authority|University|College|Agency|School(?:s)?|Sheriff(?:'s)? Department)/i;
const MONTH_NAME_PATTERN =
  "(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\\.?\\s+\\d{1,2},\\s+20\\d{2}";
const JSON_FILE_PATTERN = /\.json$/i;
const PDF_FILE_PATTERN = /\.pdf$/i;
const TEXT_FILE_PATTERN = /\.(txt|md|markdown)$/i;
const WEEKDAY_NAMES = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
] as const;
const STATE_NAME_TO_CODE: Record<string, string> = {
  alabama: "AL",
  alaska: "AK",
  arizona: "AZ",
  arkansas: "AR",
  california: "CA",
  colorado: "CO",
  connecticut: "CT",
  delaware: "DE",
  florida: "FL",
  georgia: "GA",
  hawaii: "HI",
  idaho: "ID",
  illinois: "IL",
  indiana: "IN",
  iowa: "IA",
  kansas: "KS",
  kentucky: "KY",
  louisiana: "LA",
  maine: "ME",
  maryland: "MD",
  massachusetts: "MA",
  michigan: "MI",
  minnesota: "MN",
  mississippi: "MS",
  missouri: "MO",
  montana: "MT",
  nebraska: "NE",
  nevada: "NV",
  "new hampshire": "NH",
  "new jersey": "NJ",
  "new mexico": "NM",
  "new york": "NY",
  "north carolina": "NC",
  "north dakota": "ND",
  ohio: "OH",
  oklahoma: "OK",
  oregon: "OR",
  pennsylvania: "PA",
  "rhode island": "RI",
  "south carolina": "SC",
  "south dakota": "SD",
  tennessee: "TN",
  texas: "TX",
  utah: "UT",
  vermont: "VT",
  virginia: "VA",
  washington: "WA",
  "west virginia": "WV",
  wisconsin: "WI",
  wyoming: "WY",
  "district of columbia": "DC",
};
const STATE_CODE_TO_REGION: Record<string, string> = {
  AL: "Alabama",
  AK: "Alaska",
  AZ: "Arizona",
  AR: "Arkansas",
  CA: "California",
  CO: "Colorado",
  CT: "Connecticut",
  DE: "Delaware",
  FL: "Florida",
  GA: "Georgia",
  HI: "Hawaii",
  ID: "Idaho",
  IL: "Illinois",
  IN: "Indiana",
  IA: "Iowa",
  KS: "Kansas",
  KY: "Kentucky",
  LA: "Louisiana",
  ME: "Maine",
  MD: "Maryland",
  MA: "Massachusetts",
  MI: "Michigan",
  MN: "Minnesota",
  MS: "Mississippi",
  MO: "Missouri",
  MT: "Montana",
  NE: "Nebraska",
  NV: "Nevada",
  NH: "New Hampshire",
  NJ: "New Jersey",
  NM: "New Mexico",
  NY: "New York",
  NC: "North Carolina",
  ND: "North Dakota",
  OH: "Ohio",
  OK: "Oklahoma",
  OR: "Oregon",
  PA: "Pennsylvania",
  RI: "Rhode Island",
  SC: "South Carolina",
  SD: "South Dakota",
  TN: "Tennessee",
  TX: "Texas",
  UT: "Utah",
  VT: "Vermont",
  VA: "Virginia",
  WA: "Washington",
  WV: "West Virginia",
  WI: "Wisconsin",
  WY: "Wyoming",
  DC: "District of Columbia",
};
let pdfJsModulePromise: Promise<typeof import("pdfjs-dist/legacy/build/pdf.mjs")> | null =
  null;

export type ImportedPayload =
  | {
      kind: "opportunity";
      opportunity: Opportunity;
      message: string;
      importResult: OpportunityImportResult;
    }
  | {
      kind: "workspace";
      workspaceState: OperatorWorkspaceState;
      message: string;
    };

function formatSchemaIssues(input: unknown): string | null {
  const result = operatorWorkspaceStateSchema.safeParse(input);
  if (result.success) {
    return null;
  }

  return result.error.issues
    .map((issue) => `${issue.path.join(".") || "root"}: ${issue.message}`)
    .join("; ");
}

function sanitizeNamePart(value: string): string {
  return value
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function uniqueValues<T>(values: Array<T | null | undefined>): T[] {
  return [...new Set(values.filter((value): value is T => value != null))];
}

function normalizeWhitespace(value: string): string {
  return value
    .replace(/\r/g, "\n")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/[ \t]{2,}/g, " ")
    .trim();
}

function normalizeLine(value: string): string {
  return value.replace(/\s+/g, " ").replace(/\s+([,.;:])/g, "$1").trim();
}

function splitLines(value: string): string[] {
  return normalizeWhitespace(value)
    .split("\n")
    .map((line) => normalizeLine(line))
    .filter(Boolean);
}

async function loadPdfJsModule(): Promise<typeof import("pdfjs-dist/legacy/build/pdf.mjs")> {
  if (!pdfJsModulePromise) {
    pdfJsModulePromise = Promise.all([
      import("pdfjs-dist/legacy/build/pdf.mjs"),
      import("pdfjs-dist/legacy/build/pdf.worker.min.mjs?url"),
    ]).then(([pdfModule, workerModule]) => {
      if (typeof window !== "undefined" && !pdfModule.GlobalWorkerOptions.workerSrc) {
        pdfModule.GlobalWorkerOptions.workerSrc = workerModule.default;
      }

      return pdfModule;
    });
  }

  return pdfJsModulePromise;
}

function isJsonFile(file: File): boolean {
  return file.type === "application/json" || JSON_FILE_PATTERN.test(file.name);
}

function isPdfFile(file: File): boolean {
  return file.type === "application/pdf" || PDF_FILE_PATTERN.test(file.name);
}

function isTextSourceFile(file: File): boolean {
  return file.type.startsWith("text/") || TEXT_FILE_PATTERN.test(file.name);
}

function describeImportSource(files: File[]): string {
  if (files.length === 1) {
    return files[0].name;
  }

  return `${files.length} source files`;
}

function buildImportResult(
  opportunity: Opportunity,
  extractionMethod: OpportunityImportResult["extractionMethod"],
  summary: string,
  warnings: string[] = [],
  assumptions: string[] = [],
): OpportunityImportResult {
  return {
    opportunity,
    extractionMethod,
    summary,
    warnings,
    assumptions,
    evidence: [],
  };
}

function cleanEntityName(value: string): string {
  return value
    .replace(/\s+/g, " ")
    .replace(/\b(?:issued by|point of contact|facilities manager)\b.*$/i, "")
    .replace(/\s+-\s+.*$/i, "")
    .trim();
}

function cleanOpportunityName(value: string, buyerName: string): string {
  return value
    .replace(/\s+/g, " ")
    .replace(/^request for (?:proposal|bid)\s*-\s*/i, "")
    .replace(/^project:\s*/i, "")
    .replace(/^subject:\s*/i, "")
    .replace(
      new RegExp(`\\b${buyerName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "ig"),
      "",
    )
    .replace(/\s{2,}/g, " ")
    .replace(/\s+-\s+$/, "")
    .trim();
}

function extractBuyerName(lines: string[], flatText: string): string {
  const lineMatch = lines.find((line) => {
    return (
      ENTITY_NAME_PATTERN.test(line) &&
      !/request for|instructions to bidders|cover letter|project bid form|attachments|point of contact/i.test(
        line,
      )
    );
  });

  if (lineMatch) {
    return cleanEntityName(lineMatch);
  }

  const acceptingMatch = flatText.match(
    /([A-Z][A-Za-z0-9'&.,\- ]+?(?:Library|Department|District|County|City|Authority|University|College|Agency|School(?:s)?|Sheriff(?:'s)? Department))\s+is accepting/i,
  );
  if (acceptingMatch) {
    return cleanEntityName(acceptingMatch[1]);
  }

  return "Imported Public Sector Opportunity";
}

function extractOpportunityName(
  lines: string[],
  flatText: string,
  buyerName: string,
): string {
  const subjectLine = lines.find((line) => /^subject:/i.test(line));
  if (subjectLine) {
    return cleanOpportunityName(subjectLine, buyerName);
  }

  const projectLine = lines.find((line) =>
    /(?:custodial|cleaning|janitorial).*(?:services|service)/i.test(line),
  );
  if (projectLine) {
    return cleanOpportunityName(projectLine, buyerName);
  }

  const inlineMatch = flatText.match(
    /(?:subject|project)\s*:?\s*(.+?(?:custodial|cleaning|janitorial).+?)(?:\.\s| bids due| anticipated award| services must be performed|$)/i,
  );
  if (inlineMatch) {
    return cleanOpportunityName(inlineMatch[1], buyerName);
  }

  return `${buyerName} Custodial Services`;
}

function extractDateAfterLabel(flatText: string, label: string): string | null {
  const expression = new RegExp(`${label}\\s*:?[\\s]+(${MONTH_NAME_PATTERN})`, "i");
  const match = flatText.match(expression);
  return match?.[1] ?? null;
}

function resolveStateCode(value: string): string | null {
  const cleaned = value.trim().toLowerCase().replace(/\.$/, "");
  if (cleaned.length === 2) {
    return cleaned.toUpperCase();
  }

  return STATE_NAME_TO_CODE[cleaned] ?? null;
}

function normalizeCityCandidate(value: string): string {
  const cleaned = value.trim();

  if (
    /\b(?:road|rd|avenue|ave|street|st|drive|dr|lane|ln|boulevard|blvd|highway|hwy)\b/i.test(
      cleaned,
    ) &&
    /\bin\b/i.test(cleaned)
  ) {
    return cleaned.split(/\bin\b/i).at(-1)?.trim() ?? cleaned;
  }

  return cleaned;
}

function extractCityState(lines: string[], flatText: string): { city: string; state: string } {
  const addressPattern =
    /\b([A-Z][A-Za-z.'\- ]+),\s*([A-Z]{2}|[A-Za-z][A-Za-z ]+)\s+\d{5}(?:-\d{4})?\b/;

  for (const line of lines) {
    const match = line.match(addressPattern);
    if (!match) {
      continue;
    }

    const stateCode = resolveStateCode(match[2]);
    if (!stateCode) {
      continue;
    }

    return {
      city: normalizeCityCandidate(match[1]),
      state: stateCode,
    };
  }

  const inlineMatch = flatText.match(addressPattern);
  if (inlineMatch) {
    const stateCode = resolveStateCode(inlineMatch[2]);
    if (stateCode) {
      return {
        city: normalizeCityCandidate(inlineMatch[1]),
        state: stateCode,
      };
    }
  }

  return {
    city: "Unknown City",
    state: "CA",
  };
}

function extractSquareFeet(lines: string[], flatText: string): number {
  const squareFootPatterns = [
    /estimated square footage[: ]+([0-9,]+)/i,
    /square footage[: ]+([0-9,]+)/i,
    /([0-9,]+)\s*(?:square feet|sq\.?\s*ft\.?)/i,
  ];

  for (const line of lines) {
    for (const pattern of squareFootPatterns) {
      const match = line.match(pattern);
      if (!match) {
        continue;
      }

      return Number(match[1].replace(/,/g, ""));
    }
  }

  for (const pattern of squareFootPatterns) {
    const match = flatText.match(pattern);
    if (match) {
      return Number(match[1].replace(/,/g, ""));
    }
  }

  return 25000;
}

function extractSiteCount(flatText: string): number {
  const match = flatText.match(
    /\b([0-9]+)\s+(?:sites|stations|substations|facilities|locations|buildings|campuses)\b/i,
  );

  if (match) {
    return Number(match[1]);
  }

  return 1;
}

function extractServiceDays(flatText: string): string[] {
  const scheduleMatch = flatText.match(
    /(?:services must be performed|service will be on)\s+(.+?)(?:\.| the successful bidder|$)/i,
  );
  const scheduleWindow = scheduleMatch?.[1] ?? "";

  return WEEKDAY_NAMES.filter((day) =>
    new RegExp(`\\b${day}\\b`, "i").test(scheduleWindow),
  );
}

function buildOccupiedHours(flatText: string, serviceDays: string[]): string {
  const scheduleLabel =
    serviceDays.length > 0
      ? `${serviceDays.join(" and ")} service window`
      : "Routine cleaning window";
  const afterHours = /while (?:the )?(?:library|building|facility) is closed|after[- ]hours|overnight/i.test(
    flatText,
  );
  const emergencyCoverage = /24\/7|call-in service|emergency response/i.test(flatText);

  if (afterHours && emergencyCoverage) {
    return `${scheduleLabel} while the facility is closed, plus 24/7 emergency response`;
  }

  if (afterHours) {
    return `${scheduleLabel} while the facility is closed`;
  }

  if (emergencyCoverage) {
    return `${scheduleLabel} with 24/7 emergency response availability`;
  }

  return scheduleLabel;
}

function extractRequiredServices(flatText: string): ServiceType[] {
  const services = new Set<ServiceType>(["nightly-cleaning"]);

  if (/paper products|trash liners|soap|sanitizer|consumables|dispensers|maintain enough stock/i.test(flatText)) {
    services.add("consumables-management");
  }

  if (
    /carpet cleaning|carpets? and mats|stripping and waxing|waxing|floor care|mop floors/i.test(
      flatText,
    )
  ) {
    services.add("floor-care");
  }

  if (/window cleaning|clean glass|entry door/i.test(flatText)) {
    services.add("window-touchpoint");
  }

  if (/day porter|daytime support|occupied hours/i.test(flatText)) {
    services.add("day-porter");
    services.add("daytime-support");
  }

  return [...services];
}

function extractReferencesRequired(flatText: string): number {
  const rangeMatch = flatText.match(/(\d+)\s*(?:to|-)\s*(\d+)\s*references/i);
  if (rangeMatch) {
    return Number(rangeMatch[1]);
  }

  const exactMatch = flatText.match(/(\d+)\s+references/i);
  if (exactMatch) {
    return Number(exactMatch[1]);
  }

  return 3;
}

function extractTermMonths(flatText: string): number {
  const years = uniqueValues(
    Array.from(flatText.matchAll(/\b(20\d{2})\s+cost basis\b/gi)).map((match) =>
      Number(match[1]),
    ),
  );
  if (years.length >= 2) {
    return years.length * 12;
  }

  const explicitYearMatch = flatText.match(/(\d+)\s*year\s+(?:contract|term)/i);
  if (explicitYearMatch) {
    return Number(explicitYearMatch[1]) * 12;
  }

  const explicitMonthMatch = flatText.match(/(\d+)\s*month\s+(?:contract|term)/i);
  if (explicitMonthMatch) {
    return Number(explicitMonthMatch[1]);
  }

  return 12;
}

function roundToNearest(value: number, step: number): number {
  return Math.max(step, Math.round(value / step) * step);
}

function estimateAnnualValueEstimate(params: {
  siteCount: number;
  totalSquareFeet: number;
  weekendCoverageRequired: boolean;
  dayPorterRequired: boolean;
  consumablesIncluded: boolean;
}): number {
  const {
    siteCount,
    totalSquareFeet,
    weekendCoverageRequired,
    dayPorterRequired,
    consumablesIncluded,
  } = params;

  let estimate =
    totalSquareFeet <= 5000
      ? 18000
      : totalSquareFeet <= 50000
        ? totalSquareFeet * 6
        : totalSquareFeet <= 200000
          ? totalSquareFeet * 3.5
          : totalSquareFeet * 2.2;

  estimate += Math.max(0, siteCount - 1) * 12000 + 4000;

  if (dayPorterRequired) {
    estimate += Math.max(20000, totalSquareFeet * 0.35);
  }

  if (weekendCoverageRequired) {
    estimate += Math.max(8000, totalSquareFeet * 0.12);
  }

  if (consumablesIncluded) {
    estimate += Math.max(3000, totalSquareFeet * 0.08);
  }

  return roundToNearest(estimate, 1000);
}

function inferSector(flatText: string): Opportunity["sector"] {
  if (/hospital|clinic|medical/i.test(flatText)) {
    return "Medical Office";
  }

  if (/warehouse|industrial|plant|manufacturing|sheriff|detention|airport|transit/i.test(flatText)) {
    return "Industrial Support";
  }

  if (/office|headquarters|administration building/i.test(flatText)) {
    return "Class A Office";
  }

  return "Mixed Commercial";
}

function inferRegion(city: string, state: string): string {
  if (/traverse city/i.test(city)) {
    return "Northern Michigan";
  }

  return STATE_CODE_TO_REGION[state] ?? `${city} region`;
}

function inferStrategicFit(params: {
  siteCount: number;
  totalSquareFeet: number;
  dayPorterRequired: boolean;
  weekendCoverageRequired: boolean;
}): Opportunity["pursuitContext"]["strategicFit"] {
  const { siteCount, totalSquareFeet, dayPorterRequired, weekendCoverageRequired } = params;

  if (siteCount === 1 && totalSquareFeet <= 5000 && !dayPorterRequired && !weekendCoverageRequired) {
    return "low";
  }

  if (siteCount >= 5 || totalSquareFeet >= 100000 || dayPorterRequired || weekendCoverageRequired) {
    return "medium";
  }

  return "medium";
}

function inferPricingPressure(flatText: string): Opportunity["pursuitContext"]["pricingPressure"] {
  if (/competitive fees|price and other factors|lowest|cost/i.test(flatText)) {
    return "high";
  }

  return "medium";
}

function buildProofPriority(flatText: string, params: {
  totalSquareFeet: number;
  dayPorterRequired: boolean;
  suppliesIncluded: boolean;
}): string[] {
  const priorities = uniqueValues([
    /24\/7|call-in service|emergency clean-?up/i.test(flatText)
      ? "emergency response discipline"
      : null,
    params.suppliesIncluded ? "supply continuity" : null,
    /while (?:the )?(?:library|building|facility) is closed|after[- ]hours/i.test(flatText)
      ? "after-hours reliability"
      : null,
    params.dayPorterRequired ? "daytime visibility" : null,
    params.totalSquareFeet <= 5000 ? "small-site consistency" : null,
    /professionalism and presentation|proof of insurance|years in business/i.test(flatText)
      ? "credibility under scrutiny"
      : null,
    "rate credibility",
  ]);

  return priorities.slice(0, 3);
}

function buildNotes(params: {
  sourceName: string;
  flatText: string;
  dueDate: string | null;
  awardDate: string | null;
  requiredServices: ServiceType[];
}): string[] {
  const notes = uniqueValues([
    `Drafted locally from ${params.sourceName}; review commercial assumptions before using the import in a live pursuit.`,
    params.dueDate ? `Official due date in source: ${params.dueDate}.` : null,
    params.awardDate ? `Source lists ${params.awardDate} as the anticipated award date.` : null,
    /mandatory pre-bid|required to participate in a pre-bid conference|attendance at the pre-bid conference/i.test(
      params.flatText,
    )
      ? "Mandatory pre-bid attendance appears to be an eligibility gate."
      : null,
    /30 day out clause/i.test(params.flatText)
      ? "The buyer expects a thirty-day out clause in the contract."
      : null,
    /paper products|soap|sanitizer|trash liners|maintain enough stock/i.test(params.flatText)
      ? "Consumables, restroom stock, or paper products are inside the service story."
      : null,
    /24\/7|call-in service|emergency clean-?up/i.test(params.flatText)
      ? "Emergency response coverage is part of the requested operating model."
      : null,
    params.requiredServices.includes("window-touchpoint")
      ? "Visible public-touchpoint cleaning is specifically called out in the source scope."
      : null,
  ]);

  return notes.length > 0 ? notes : ["Imported from source documents; validate scope assumptions."];
}

function extractReportingCadence(flatText: string): string {
  if (/weekly inspection/i.test(flatText)) {
    return "Weekly inspection and Facilities Manager check-ins";
  }

  if (/monthly/i.test(flatText)) {
    return "Monthly performance reporting";
  }

  if (/report to Facilities Manager/i.test(flatText)) {
    return "Routine issue reporting to the Facilities Manager";
  }

  return "Routine supervisor inspections and buyer reporting";
}

function extractStartDate(flatText: string, awardDate: string | null): string {
  if (awardDate) {
    return `Anticipated award ${awardDate}`;
  }

  const workCouldBeginMatch = flatText.match(/work could begin on[: ]+(.+?)(?:\.|$)/i);
  if (workCouldBeginMatch) {
    return normalizeLine(workCouldBeginMatch[1]);
  }

  return "TBD after award";
}

function groupPdfItemsIntoLines(items: unknown[]): string[] {
  const lines: Array<{ y: number | null; parts: string[] }> = [];

  for (const item of items) {
    if (typeof item !== "object" || item === null) {
      continue;
    }

    const record = item as {
      str?: string;
      transform?: number[];
      hasEOL?: boolean;
    };
    const value = normalizeLine(record.str ?? "");
    if (!value) {
      continue;
    }

    const y =
      Array.isArray(record.transform) && typeof record.transform[5] === "number"
        ? Math.round(record.transform[5] * 10) / 10
        : null;
    const current = lines.at(-1);

    if (!current || (current.y !== null && y !== null && Math.abs(current.y - y) > 2)) {
      lines.push({ y, parts: [value] });
    } else {
      current.parts.push(value);
      current.y = y ?? current.y;
    }

    if (record.hasEOL) {
      lines.push({ y: null, parts: [] });
    }
  }

  return lines
    .map((line) => line.parts.join(" ").replace(/\s+/g, " ").trim())
    .filter(Boolean);
}

async function extractTextFromPdfFile(file: File): Promise<string> {
  const { getDocument } = await loadPdfJsModule();
  const data = new Uint8Array(await file.arrayBuffer());
  const pdf = await getDocument({ data }).promise;
  const pageTexts: string[] = [];

  for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
    const page = await pdf.getPage(pageNumber);
    const textContent = await page.getTextContent();
    pageTexts.push(groupPdfItemsIntoLines(textContent.items).join("\n"));
  }

  return pageTexts.join("\n\n");
}

async function readSourceFile(file: File): Promise<string> {
  if (isPdfFile(file)) {
    return extractTextFromPdfFile(file);
  }

  if (isTextSourceFile(file)) {
    return file.text();
  }

  throw new Error(
    `Unsupported file type for ${file.name}. Upload one JSON file or PDF/TXT/MD source files.`,
  );
}

export function importStructuredJson(
  rawText: string,
  sourceName = "uploaded JSON",
): ImportedPayload {
  let parsedJson: unknown;

  try {
    parsedJson = JSON.parse(rawText);
  } catch {
    throw new Error(`Unable to parse ${sourceName} as JSON.`);
  }

  const opportunityError = formatOpportunityValidationError(parsedJson);
  if (!opportunityError) {
    const opportunity = parseOpportunity(parsedJson);

    return {
      kind: "opportunity",
      opportunity,
      importResult: buildImportResult(
        opportunity,
        "structured-json",
        `Loaded structured opportunity from ${sourceName}.`,
        [
          "Review the imported fields before creating a new Boss Key opportunity record.",
        ],
      ),
      message: `Loaded structured opportunity from ${sourceName}.`,
    };
  }

  const workspaceResult = operatorWorkspaceStateSchema.safeParse(parsedJson);
  if (workspaceResult.success) {
    return {
      kind: "workspace",
      workspaceState: workspaceResult.data,
      message: `Loaded workspace state from ${sourceName}.`,
    };
  }

  const workspaceError = formatSchemaIssues(parsedJson);
  throw new Error(
    `JSON in ${sourceName} did not match the opportunity or workspace schema. Opportunity: ${opportunityError}. Workspace: ${workspaceError}.`,
  );
}

export function buildOpportunityFromSourceText(
  rawText: string,
  sourceName = "uploaded source file",
): Opportunity {
  const lines = splitLines(rawText);
  const flatText = lines.join(" ");
  const buyerName = extractBuyerName(lines, flatText);
  const opportunityName = extractOpportunityName(lines, flatText, buyerName);
  const { city, state } = extractCityState(lines, flatText);
  const totalSquareFeet = extractSquareFeet(lines, flatText);
  const siteCount = extractSiteCount(flatText);
  const serviceDays = extractServiceDays(flatText);
  const requiredServices = extractRequiredServices(flatText);
  const suppliesIncluded = requiredServices.includes("consumables-management");
  const weekendCoverageRequired = serviceDays.some(
    (day) => day === "Saturday" || day === "Sunday",
  );
  const dayPorterRequired = requiredServices.includes("day-porter");
  const awardDate = extractDateAfterLabel(flatText, "Anticipated Award Date");
  const dueDate =
    extractDateAfterLabel(flatText, "Bids Due") ??
    extractDateAfterLabel(flatText, "Response Date") ??
    extractDateAfterLabel(flatText, "Due Date");
  const pricingPressure = inferPricingPressure(flatText);
  const strategicFit = inferStrategicFit({
    siteCount,
    totalSquareFeet,
    dayPorterRequired,
    weekendCoverageRequired,
  });
  const annualValueEstimate = estimateAnnualValueEstimate({
    siteCount,
    totalSquareFeet,
    weekendCoverageRequired,
    dayPorterRequired,
    consumablesIncluded: suppliesIncluded,
  });
  const sourceYear =
    dueDate?.match(/20\d{2}/)?.[0] ??
    awardDate?.match(/20\d{2}/)?.[0] ??
    new Date().getUTCFullYear().toString();

  return parseOpportunity({
    id: `${sanitizeNamePart(opportunityName || buyerName)}-${sourceYear}`,
    opportunityName,
    buyerName,
    sector: inferSector(flatText),
    geography: {
      region: inferRegion(city, state),
      city,
      state,
      inPreferredRegion: false,
    },
    siteProfile: {
      siteCount,
      totalSquareFeet,
      occupiedHours: buildOccupiedHours(flatText, serviceDays),
      weekendCoverageRequired,
      dayPorterRequired,
      unionEnvironment: /union|collective bargaining|prevailing wage/i.test(flatText),
    },
    contract: {
      annualValueEstimate,
      termMonths: extractTermMonths(flatText),
      targetGrossMarginPercent: pricingPressure === "high" ? 15 : 18,
      transitionDays: siteCount === 1 && totalSquareFeet <= 5000 ? 14 : 30,
      startDate: extractStartDate(flatText, awardDate),
    },
    requirements: {
      requiredServices,
      reportingCadence: extractReportingCadence(flatText),
      sustainabilityExpectation: /green seal|recycled products|sustain/i.test(flatText),
      selfPerformedPreference: /trained and supervised employees|own employees|self-performed/i.test(
        flatText,
      ),
      referencesRequired: extractReferencesRequired(flatText),
    },
    pursuitContext: {
      incumbentPresent: true,
      relationshipStrength: "low",
      strategicFit,
      pricingPressure,
      proofPriority: buildProofPriority(flatText, {
        totalSquareFeet,
        dayPorterRequired,
        suppliesIncluded,
      }),
      notes: buildNotes({
        sourceName,
        flatText,
        dueDate,
        awardDate,
        requiredServices,
      }),
    },
  });
}

export async function importOpportunityFiles(files: File[]): Promise<ImportedPayload> {
  if (files.length === 0) {
    throw new Error("Choose a JSON file or one or more PDF/TXT/MD source files.");
  }

  if (files.length === 1 && isJsonFile(files[0])) {
    return importStructuredJson(await files[0].text(), files[0].name);
  }

  if (files.some((file) => isJsonFile(file))) {
    throw new Error(
      "Upload either one JSON file or one or more PDF/TXT/MD source files, not both together.",
    );
  }

  const extractedSource = await Promise.all(
    files.map(async (file) => {
      const text = await readSourceFile(file);

      return `Source file: ${file.name}\n${text}`;
    }),
  );

  const opportunity = buildOpportunityFromSourceText(
    extractedSource.join("\n\n"),
    describeImportSource(files),
  );
  const importResult = buildImportResult(
    opportunity,
    "heuristic",
    `Drafted an opportunity from ${describeImportSource(files)}.`,
    [
      "Review value, term, fit, and eligibility assumptions before using it in a live pursuit.",
    ],
    opportunity.pursuitContext.notes,
  );

  return {
    kind: "opportunity",
    opportunity,
    importResult,
    message: `${importResult.summary} ${importResult.warnings.join(" ")}`.trim(),
  };
}
