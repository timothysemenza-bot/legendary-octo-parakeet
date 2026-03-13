DEFAULT_TIMELINE_MILESTONES = [
    {
        "code": "INITIAL_REVIEW",
        "label": "Initial review",
        "offset_days": 21,
        "note": "Confirm scope, submission channel, and basic opportunity fit.",
    },
    {
        "code": "BID_NO_BID",
        "label": "Bid / no-bid review",
        "offset_days": 18,
        "note": "Decide whether to pursue based on fit, timing, and resource readiness.",
    },
    {
        "code": "CLARIFICATIONS",
        "label": "Clarification question deadline",
        "offset_days": 14,
        "note": "Draft and submit clarification questions before the buyer cutoff.",
    },
    {
        "code": "SITE_VISIT_PREP",
        "label": "Site visit / walkthrough prep",
        "offset_days": 12,
        "note": "Prepare site-specific questions, staffing assumptions, and coverage notes.",
    },
    {
        "code": "PRICING_KICKOFF",
        "label": "Pricing kickoff",
        "offset_days": 10,
        "note": "Lock pricing assumptions, labor inputs, and required commercial approvals.",
    },
    {
        "code": "OPS_REVIEW",
        "label": "Operations review",
        "offset_days": 7,
        "note": "Validate staffing model, transition feasibility, and geography coverage.",
    },
    {
        "code": "DRAFT_REVIEW",
        "label": "Draft review",
        "offset_days": 5,
        "note": "Review the response package, required forms, and compliance mapping.",
    },
    {
        "code": "FINAL_REVIEW",
        "label": "Final review",
        "offset_days": 2,
        "note": "Confirm executive approval, packaging, and final submission readiness.",
    },
    {
        "code": "PRODUCTION_SUBMISSION",
        "label": "Production / submission",
        "offset_days": 0,
        "note": "Submit the package using the required channel and naming rules.",
    },
]

DEFAULT_STAKEHOLDERS = [
    {
        "role_code": "sales_lead",
        "role_label": "Sales lead",
        "purpose": "Own customer contact, bid decision framing, and executive alignment.",
    },
    {
        "role_code": "proposal_lead",
        "role_label": "Proposal lead",
        "purpose": "Own schedule, artifact assembly, and compliance coordination.",
    },
    {
        "role_code": "operations_lead",
        "role_label": "Operations lead",
        "purpose": "Validate staffing, mobilization, geography coverage, and delivery feasibility.",
    },
    {
        "role_code": "pricing_finance",
        "role_label": "Pricing / finance",
        "purpose": "Own pricing inputs, assumptions, approvals, and margin discipline.",
    },
    {
        "role_code": "local_leadership",
        "role_label": "Local / regional leadership",
        "purpose": "Provide site knowledge, local delivery context, and leadership sign-off.",
    },
    {
        "role_code": "sme_contributors",
        "role_label": "SME contributors",
        "purpose": "Contribute specialized input such as safety, transition, HR, or compliance forms.",
    },
]

DEFAULT_OPERATOR_PROMPTS = [
    "Confirm references and relevant past performance examples for similar facilities scope.",
    "Gather local office details, maps, and site-specific images if the response package uses them.",
    "Validate staffing assumptions, shift coverage, supervision ratios, and transition timing.",
    "Collect pricing inputs, wage assumptions, and any customer-required pricing forms.",
    "Confirm org chart, resumes, certifications, and insurance certificates needed for submission.",
]

DEFAULT_COORDINATION_CHECKLIST = [
    {
        "category": "Assessment",
        "label": "Confirm opportunity summary, dates, and go / no-go posture.",
        "owner_role": "sales_lead",
    },
    {
        "category": "Compliance",
        "label": "Review required forms, attachments, and compliance owners.",
        "owner_role": "proposal_lead",
    },
    {
        "category": "Operations",
        "label": "Validate scope assumptions, site coverage, and operational feasibility.",
        "owner_role": "operations_lead",
    },
    {
        "category": "Pricing",
        "label": "Kick off pricing inputs and assumptions.",
        "owner_role": "pricing_finance",
    },
    {
        "category": "Leadership",
        "label": "Confirm review cadence and required leadership checkpoints.",
        "owner_role": "local_leadership",
    },
]
