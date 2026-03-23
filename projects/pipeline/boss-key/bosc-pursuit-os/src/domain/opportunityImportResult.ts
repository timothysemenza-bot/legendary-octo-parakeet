import { z } from "zod";
import { opportunitySchema } from "./opportunity";

export const opportunityImportEvidenceSchema = z.object({
  field: z.string().min(1),
  sourceFile: z.string().min(1),
  snippet: z.string().min(1),
});

export const opportunityImportResultSchema = z.object({
  opportunity: opportunitySchema,
  extractionMethod: z.enum(["model", "heuristic", "structured-json"]),
  summary: z.string().min(1),
  warnings: z.array(z.string().min(1)),
  assumptions: z.array(z.string().min(1)),
  evidence: z.array(opportunityImportEvidenceSchema),
});

export type OpportunityImportEvidence = z.infer<
  typeof opportunityImportEvidenceSchema
>;
export type OpportunityImportResult = z.infer<typeof opportunityImportResultSchema>;

export function parseOpportunityImportResult(
  input: unknown,
): OpportunityImportResult {
  return opportunityImportResultSchema.parse(input);
}
