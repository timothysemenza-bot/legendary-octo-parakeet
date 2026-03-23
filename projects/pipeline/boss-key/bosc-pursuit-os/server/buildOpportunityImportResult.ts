import type {
  OpportunityImportEvidence,
  OpportunityImportResult,
} from "../src/domain/opportunityImportResult";
import type { Opportunity } from "../src/domain/opportunity";
import type { ExtractedSourceDocument } from "./extractSourceText";

interface BuildOpportunityImportResultParams {
  opportunity: Opportunity;
  extractionMethod: OpportunityImportResult["extractionMethod"];
  documents: ExtractedSourceDocument[];
  warnings?: string[];
  summary?: string;
}

function uniqueValues(values: Array<string | null | undefined>): string[] {
  return [...new Set(values.filter((value): value is string => !!value))];
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function extractSnippet(
  documents: ExtractedSourceDocument[],
  patterns: string[],
): { sourceFile: string; snippet: string } | null {
  for (const document of documents) {
    for (const pattern of patterns) {
      if (!pattern.trim()) {
        continue;
      }

      const match = document.text.match(
        new RegExp(`(.{0,90}${escapeRegExp(pattern)}.{0,120})`, "i"),
      );
      if (match?.[1]) {
        return {
          sourceFile: document.name,
          snippet: match[1].replace(/\s+/g, " ").trim(),
        };
      }
    }
  }

  return null;
}

function buildEvidence(
  opportunity: Opportunity,
  documents: ExtractedSourceDocument[],
): OpportunityImportEvidence[] {
  const evidenceRequests: Array<{ field: string; patterns: string[] }> = [
    {
      field: "buyerName",
      patterns: [opportunity.buyerName],
    },
    {
      field: "opportunityName",
      patterns: [opportunity.opportunityName],
    },
    {
      field: "geography.city",
      patterns: [opportunity.geography.city],
    },
    {
      field: "siteProfile.totalSquareFeet",
      patterns: [
        opportunity.siteProfile.totalSquareFeet.toLocaleString("en-US"),
        `${opportunity.siteProfile.totalSquareFeet}`,
      ],
    },
    {
      field: "siteProfile.occupiedHours",
      patterns: [
        opportunity.siteProfile.occupiedHours,
        "services must be performed",
        "while the library is closed",
        "24/7",
      ],
    },
  ];

  return evidenceRequests
    .map((request) => {
      const match = extractSnippet(documents, request.patterns);
      if (!match) {
        return null;
      }

      return {
        field: request.field,
        sourceFile: match.sourceFile,
        snippet: match.snippet,
      };
    })
    .filter((item): item is OpportunityImportEvidence => item !== null);
}

function extractAssumptionsFromNotes(opportunity: Opportunity): string[] {
  return uniqueValues(
    opportunity.pursuitContext.notes.filter((note) =>
      /assum|estimate|estimated|inferred|placeholder|tbd|pilot|review/i.test(note),
    ),
  );
}

function buildSummary(
  extractionMethod: OpportunityImportResult["extractionMethod"],
  documents: ExtractedSourceDocument[],
): string {
  const sourceCount = documents.length;
  const modeLabel =
    extractionMethod === "model"
      ? "Built a model-based opportunity draft"
      : "Built a heuristic opportunity draft";

  return `${modeLabel} from ${sourceCount} source file${
    sourceCount === 1 ? "" : "s"
  }.`;
}

export function buildOpportunityImportResult(
  params: BuildOpportunityImportResultParams,
): OpportunityImportResult {
  const assumptions = extractAssumptionsFromNotes(params.opportunity);

  return {
    opportunity: params.opportunity,
    extractionMethod: params.extractionMethod,
    summary:
      params.summary ??
      buildSummary(params.extractionMethod, params.documents),
    warnings: uniqueValues(params.warnings ?? []),
    assumptions,
    evidence: buildEvidence(params.opportunity, params.documents),
  };
}
