import type { ChangeEvent } from "react";
import type { Opportunity } from "../../domain/opportunity";
import { OpportunityFieldsForm } from "./OpportunityFieldsForm";

interface OpportunityWorkbenchProps {
  opportunity: Opportunity;
  uploadError: string | null;
  uploadNotice: string | null;
  onOpportunityChange: (nextOpportunity: Opportunity) => void;
  onLoadDemo: () => void;
  onImportFiles: (files: File[]) => Promise<void>;
}

export function OpportunityWorkbench({
  opportunity,
  uploadError,
  uploadNotice,
  onOpportunityChange,
  onLoadDemo,
  onImportFiles,
}: OpportunityWorkbenchProps) {
  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    if (files.length === 0) {
      return;
    }

    await onImportFiles(files);
    event.target.value = "";
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">Pursuit Intake</p>
          <h2>Opportunity Workbench</h2>
        </div>
        <button type="button" className="secondary-button" onClick={onLoadDemo}>
          Add Demo Opportunity
        </button>
      </div>

      <p className="panel-copy">
        Edit the active opportunity directly or import a structured JSON file,
        a saved workspace-state JSON, or one or more PDF/DOCX/TXT/MD source files. Boss Key
        now routes imported opportunity drafts through a review step before
        creating a new record in the local opportunity library.
      </p>

      <label className="upload-field">
        <span>Import JSON or source files</span>
        <input
          type="file"
          accept=".json,.pdf,.docx,.txt,.md,application/json,application/pdf,text/plain,text/markdown,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          multiple
          onChange={handleFileChange}
        />
      </label>

      <p className="helper-text">
        Use a single JSON file for a clean schema import, or upload source
        documents to draft a new opportunity from the RFP text.
      </p>

      {uploadNotice ? <p className="success-text">{uploadNotice}</p> : null}
      {uploadError ? <p className="error-text">{uploadError}</p> : null}

      <OpportunityFieldsForm
        opportunity={opportunity}
        onOpportunityChange={onOpportunityChange}
      />
    </section>
  );
}
