import { getDocument } from "pdfjs-dist/legacy/build/pdf.mjs";
import mammoth from "mammoth";
import type { File as FormidableFile } from "formidable";
import fs from "node:fs/promises";
import path from "node:path";
import type { ServerConfig } from "./config";

export interface ExtractedSourceDocument {
  name: string;
  text: string;
  characterCount: number;
}

export interface SourcePacket {
  documents: ExtractedSourceDocument[];
  combinedText: string;
  warnings: string[];
}

const TEXT_EXTENSION_PATTERN = /\.(txt|md|markdown|csv|json)$/i;
const DOCX_EXTENSION_PATTERN = /\.docx$/i;

function normalizeWhitespace(value: string): string {
  return value
    .replace(/\r/g, "\n")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/[ \t]{2,}/g, " ")
    .trim();
}

function clipText(value: string, maxCharacters: number): string {
  if (value.length <= maxCharacters) {
    return value;
  }

  return `${value.slice(0, maxCharacters).trim()}\n\n[Truncated for import]`;
}

function isPdfFile(file: FormidableFile): boolean {
  return (
    file.mimetype === "application/pdf" || PDF_EXTENSION_PATTERN.test(file.originalFilename || "")
  );
}

function isDocxFile(file: FormidableFile): boolean {
  return DOCX_EXTENSION_PATTERN.test(file.originalFilename || "");
}

function isTextFile(file: FormidableFile): boolean {
  return (
    file.mimetype?.startsWith("text/") === true ||
    TEXT_EXTENSION_PATTERN.test(file.originalFilename || "")
  );
}

const PDF_EXTENSION_PATTERN = /\.pdf$/i;

async function extractPdfText(filePath: string): Promise<string> {
  const data = new Uint8Array(await fs.readFile(filePath));
  const pdf = await getDocument({ data }).promise;
  const pageChunks: string[] = [];

  for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
    const page = await pdf.getPage(pageNumber);
    const textContent = await page.getTextContent();
    const pageText = textContent.items
      .map((item) => ("str" in item ? item.str : ""))
      .join(" ");

    pageChunks.push(pageText);
  }

  return normalizeWhitespace(pageChunks.join("\n\n"));
}

async function extractDocxText(filePath: string): Promise<string> {
  const result = await mammoth.extractRawText({ path: filePath });
  return normalizeWhitespace(result.value);
}

async function extractTextFile(filePath: string): Promise<string> {
  return normalizeWhitespace(await fs.readFile(filePath, "utf8"));
}

async function extractSingleFileText(
  file: FormidableFile,
  config: ServerConfig,
): Promise<ExtractedSourceDocument> {
  const originalName =
    file.originalFilename?.trim() || path.basename(file.filepath || "uploaded-file");
  let extractedText = "";

  if (isPdfFile(file)) {
    extractedText = await extractPdfText(file.filepath);
  } else if (isDocxFile(file)) {
    extractedText = await extractDocxText(file.filepath);
  } else if (isTextFile(file)) {
    extractedText = await extractTextFile(file.filepath);
  } else {
    throw new Error(
      `Unsupported source file type for ${originalName}. Upload PDF, DOCX, TXT, MD, CSV, or JSON files.`,
    );
  }

  const clippedText = clipText(extractedText, config.maxTotalCharacters);

  return {
    name: originalName,
    text: clippedText,
    characterCount: clippedText.length,
  };
}

export async function extractSourcePacket(
  files: FormidableFile[],
  config: ServerConfig,
): Promise<SourcePacket> {
  const documents = await Promise.all(
    files.map((file) => extractSingleFileText(file, config)),
  );
  const combinedChunks: string[] = [];
  const warnings: string[] = [];
  let totalCharacters = 0;

  for (const document of documents) {
    const chunk = `Source file: ${document.name}\n${document.text}`;
    if (totalCharacters + chunk.length > config.maxTotalCharacters) {
      const remaining = Math.max(config.maxTotalCharacters - totalCharacters, 0);
      if (remaining > 0) {
        combinedChunks.push(clipText(chunk, remaining));
      }
      warnings.push(
        "Source text was truncated to fit the model import budget. Review key assumptions before kickoff.",
      );
      break;
    }

    combinedChunks.push(chunk);
    totalCharacters += chunk.length;
  }

  return {
    documents,
    combinedText: combinedChunks.join("\n\n"),
    warnings,
  };
}
