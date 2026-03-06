# Data Contracts

## rfp_submission

- client_id: string
- opportunity_title: string
- source_docs[]: string[]
- due_date: YYYY-MM-DD
- industry: string
- priority_flags[]: string[]

## qualification_result

- gate_checks[]: object map by gate id
- weighted_score: number (0-100)
- recommendation: Go | Conditional | No-Go
- rationale[]: string[]
- missing_data[]: string[]

## proposal_draft_v1

- executive_summary: string
- compliance_matrix: string
- solution_outline: string
- assumptions: string
- risk_callouts: string
- brand_elements_applied: string[]

## sharepoint_asset_index

- brand_files[]: string[]
- past_performance_snippets[]: string[]
- approved_claims[]: string[]
- proposal_templates[]: string[]
- restrictions[]: string[]
