import formidable, { type File as FormidableFile } from "formidable";
import http, {
  type IncomingMessage,
  type ServerResponse,
} from "node:http";
import { buildOpportunityImportResult } from "./buildOpportunityImportResult";
import { serverConfig } from "./config";
import { extractSourcePacket } from "./extractSourceText";
import { sendJson } from "./http";
import { importOpportunityWithModel } from "./openai/importOpportunityWithModel";
import { buildOpportunityFromSourceText } from "../src/services/opportunityImport";

function flattenUploadedFiles(
  uploadedFiles: Record<string, FormidableFile | FormidableFile[] | undefined>,
): FormidableFile[] {
  return Object.values(uploadedFiles).flatMap((value) =>
    !value ? [] : Array.isArray(value) ? value : [value],
  );
}

async function parseMultipartFiles(
  request: IncomingMessage,
): Promise<FormidableFile[]> {
  const form = formidable({
    multiples: true,
    maxFiles: serverConfig.maxFileCount,
    maxFileSize: serverConfig.maxFileBytes,
    allowEmptyFiles: false,
    keepExtensions: true,
  });
  const [, uploadedFiles] = await form.parse(request);

  return flattenUploadedFiles(uploadedFiles);
}

async function handleImportOpportunity(
  request: IncomingMessage,
  response: ServerResponse,
  requestOrigin: string,
): Promise<void> {
  try {
    const files = await parseMultipartFiles(request);

    if (files.length === 0) {
      sendJson(
        response,
        { error: "Upload at least one source file." },
        400,
        requestOrigin,
        serverConfig.corsOrigins,
      );
      return;
    }

    const sourcePacket = await extractSourcePacket(files, serverConfig);
    const fallbackWarnings = [...sourcePacket.warnings];

    if (serverConfig.enableModelImport && serverConfig.openAiApiKey) {
      try {
        const opportunity = await importOpportunityWithModel(
          sourcePacket,
          serverConfig,
        );
        const result = buildOpportunityImportResult({
          opportunity,
          extractionMethod: "model",
          documents: sourcePacket.documents,
          warnings: fallbackWarnings,
        });

        sendJson(
          response,
          result,
          200,
          requestOrigin,
          serverConfig.corsOrigins,
        );
        return;
      } catch (error) {
        if (!serverConfig.allowHeuristicFallback) {
          sendJson(
            response,
            {
              error:
                error instanceof Error
                  ? error.message
                  : "Model import failed.",
            },
            502,
            requestOrigin,
            serverConfig.corsOrigins,
          );
          return;
        }

        fallbackWarnings.push(
          error instanceof Error
            ? `Model import failed, so Boss Key returned a heuristic draft instead: ${error.message}`
            : "Model import failed, so Boss Key returned a heuristic draft instead.",
        );
      }
    } else {
      fallbackWarnings.push(
        "Model import is not configured on this server, so Boss Key returned a heuristic draft instead.",
      );
    }

    const opportunity = buildOpportunityFromSourceText(
      sourcePacket.combinedText,
      sourcePacket.documents.length === 1
        ? sourcePacket.documents[0].name
        : `${sourcePacket.documents.length} source files`,
    );
    const result = buildOpportunityImportResult({
      opportunity,
      extractionMethod: "heuristic",
      documents: sourcePacket.documents,
      warnings: fallbackWarnings,
    });

    sendJson(
      response,
      result,
      200,
      requestOrigin,
      serverConfig.corsOrigins,
    );
  } catch (error) {
    sendJson(
      response,
      {
        error:
          error instanceof Error ? error.message : "Import request failed.",
      },
      400,
      requestOrigin,
      serverConfig.corsOrigins,
    );
  }
}

function requestHandler(
  request: IncomingMessage,
  response: ServerResponse,
): void {
  const requestOrigin = request.headers.origin || "";
  const requestUrl = new URL(
    request.url || "/",
    `http://${request.headers.host || `localhost:${serverConfig.port}`}`,
  );
  const pathname =
    requestUrl.pathname.endsWith("/") && requestUrl.pathname.length > 1
      ? requestUrl.pathname.slice(0, -1)
      : requestUrl.pathname;

  if (request.method === "OPTIONS") {
    response.writeHead(204, {
      "Access-Control-Allow-Origin": requestOrigin || "*",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    });
    response.end();
    return;
  }

  if (pathname === "/api/health" && request.method === "GET") {
    sendJson(
      response,
      {
        ok: true,
        modelEnabled: serverConfig.enableModelImport && !!serverConfig.openAiApiKey,
        fallbackEnabled: serverConfig.allowHeuristicFallback,
        model: serverConfig.openAiModel,
      },
      200,
      requestOrigin,
      serverConfig.corsOrigins,
    );
    return;
  }

  if (pathname === "/api/import-opportunity" && request.method === "POST") {
    void handleImportOpportunity(request, response, requestOrigin);
    return;
  }

  sendJson(
    response,
    { error: "Not found" },
    404,
    requestOrigin,
    serverConfig.corsOrigins,
  );
}

const server = http.createServer(requestHandler);

server.listen(serverConfig.port, () => {
  console.log(
    `Boss Key import server running at http://localhost:${serverConfig.port}`,
  );
});
