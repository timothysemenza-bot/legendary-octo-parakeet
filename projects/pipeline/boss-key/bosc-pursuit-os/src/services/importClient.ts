import {
  parseOpportunityImportResult,
  type OpportunityImportResult,
} from "../domain/opportunityImportResult";
import {
  importOpportunityFiles,
  importStructuredJson,
  type ImportedPayload,
} from "./opportunityImport";

const JSON_FILE_PATTERN = /\.json$/i;

class ImportApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ImportApiError";
  }
}

function isStructuredJsonFile(file: File): boolean {
  return file.type === "application/json" || JSON_FILE_PATTERN.test(file.name);
}

function composeImportMessage(result: OpportunityImportResult): string {
  return [result.summary, ...result.warnings.slice(0, 2)]
    .filter(Boolean)
    .join(" ");
}

function buildImportedPayloadFromApiResult(
  result: OpportunityImportResult,
): ImportedPayload {
  return {
    kind: "opportunity",
    opportunity: result.opportunity,
    importResult: result,
    message: composeImportMessage(result),
  };
}

async function requestModelImport(
  files: File[],
): Promise<OpportunityImportResult> {
  const formData = new FormData();

  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await fetch("/api/import-opportunity", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let message = `Import request failed with status ${response.status}.`;

    try {
      const errorPayload = (await response.json()) as { error?: string };
      if (errorPayload.error) {
        message = errorPayload.error;
      }
    } catch {
      // Keep the generic message when the server does not return JSON.
    }

    throw new ImportApiError(message, response.status);
  }

  return parseOpportunityImportResult(await response.json());
}

export async function importOpportunityForApp(
  files: File[],
): Promise<ImportedPayload> {
  if (files.length === 1 && isStructuredJsonFile(files[0])) {
    return importStructuredJson(await files[0].text(), files[0].name);
  }

  try {
    const modelResult = await requestModelImport(files);
    return buildImportedPayloadFromApiResult(modelResult);
  } catch (error) {
    if (
      error instanceof ImportApiError &&
      ![404, 405, 501, 502, 503].includes(error.status)
    ) {
      throw error;
    }

    const fallback = await importOpportunityFiles(files);
    if (fallback.kind === "opportunity") {
      return {
        ...fallback,
        message:
          `${fallback.message} ` +
          "The Boss Key import server was unavailable, so the app used the local heuristic importer instead.",
      };
    }

    return fallback;
  }
}

export { buildImportedPayloadFromApiResult, composeImportMessage };
