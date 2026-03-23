import OpenAI from "openai";
import { zodTextFormat } from "openai/helpers/zod";
import {
  opportunitySchema,
  parseOpportunity,
  type Opportunity,
} from "../../src/domain/opportunity";
import type { ServerConfig } from "../config";
import type { SourcePacket } from "../extractSourceText";

const IMPORT_INSTRUCTIONS = `
You are extracting a Boss Key opportunity from janitorial, custodial, or facilities pursuit source files.

Return only the Boss Key Opportunity schema.

Rules:
- Use exact customer names, dates, locations, scope details, and gate requirements from the source text whenever they are available.
- If the source is public sector or institutional, do not force a commercial-property voice into the data.
- The allowed sector values are exactly: Class A Office, Medical Office, Mixed Commercial, Industrial Support.
- If the source does not provide annual value, transition days, margin target, or strategic fit explicitly, infer a conservative, plausible value and explain that inference in pursuitContext.notes.
- Put bid gates, mandatory meetings, ambiguous scope, missing pricing basis, and estimation caveats into pursuitContext.notes.
- Keep proofPriority short and practical for live pursuits.
- If multiple files disagree, choose the most conservative interpretation and mention the conflict in pursuitContext.notes.
`.trim();

let openAiClient: OpenAI | null = null;

function getOpenAiClient(config: ServerConfig): OpenAI {
  if (!config.openAiApiKey) {
    throw new Error("OPENAI_API_KEY is not configured.");
  }

  if (!openAiClient) {
    openAiClient = new OpenAI({
      apiKey: config.openAiApiKey,
      timeout: config.openAiTimeoutMs,
    });
  }

  return openAiClient;
}

function buildUserInput(sourcePacket: SourcePacket): string {
  return `
Source file count: ${sourcePacket.documents.length}

Extract one Boss Key opportunity from these source files.
If you estimate any field, explain it in pursuitContext.notes.
Preserve public-sector gates such as mandatory pre-bid attendance in pursuitContext.notes.

${sourcePacket.combinedText}
`.trim();
}

export async function importOpportunityWithModel(
  sourcePacket: SourcePacket,
  config: ServerConfig,
): Promise<Opportunity> {
  const client = getOpenAiClient(config);
  const response = await client.responses.parse({
    model: config.openAiModel,
    instructions: IMPORT_INSTRUCTIONS,
    input: buildUserInput(sourcePacket),
    reasoning: {
      effort: config.openAiReasoningEffort,
    },
    text: {
      verbosity: "low",
      format: zodTextFormat(opportunitySchema, "boss_key_opportunity"),
    },
  });

  if (!response.output_parsed) {
    throw new Error("The model response did not include a parsed opportunity.");
  }

  return parseOpportunity(response.output_parsed);
}
