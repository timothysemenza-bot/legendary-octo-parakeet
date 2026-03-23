import demoWorkspaceStateJson from "../inputs/demo-workspace-state.json";
import eastBayOpportunityJson from "../inputs/east-bay-library-opportunity.json";
import { describe, expect, it } from "vitest";
import {
  buildOpportunityFromSourceText,
  importStructuredJson,
} from "../src/services/opportunityImport";

const eastBaySourceText = `
REQUEST FOR PROPOSAL
Traverse Area District Library
SUBJECT: Request for Proposal - Custodial Services at East Bay Branch

Traverse Area District Library is accepting sealed bids for contractual custodial services
for the facility located at 1989 Three Mile Road in Traverse City, MI 49686.

1st Pre-Bid Conference: March 6, 2026
2nd Pre-Bid Conference: March 12, 2026
Bids Due: March 31, 2026
Anticipated Award Date: April 30, 2026

Project Overview
Services must be performed Monday and Thursday.
Services must be performed while the library is closed.

The successful bidder is responsible for:
- Providing trained and supervised employees
- Providing verification that emergency response / management availability is available on a 24/7 basis

Criteria for a Successful Bid Will Include:
- A thirty day out clause in the contract
- 3 to 5 References
- Proof of insurance
- Attendance at the pre-bid conference
- Competitive fees

Building Address and estimated square footage:
Traverse Area District Library
East Bay Branch Library
1989 Three Mile Rd
Traverse City, MI 49686
estimated square footage: 1,200

We certify that this proposal is for routine custodial services and will include:
- Vacuum all carpets and mats
- Clean bathroom and sanitize fixtures
- Take out all trash and recycling
- Clean sink and microwave in employee break area
- Wipe down and sanitize public tables, computers, and circulation desk
- Clean glass on entry door as needed

The staffing provided with this proposal and bid includes weekly inspection and contact with the Library Facilities Manager.
Emergency cleanup will include response time and bodily fluid cleanup training.

We certify that this bid includes all chemicals and that all chemicals meet green seal standards.
We will provide all hand soap, hand sanitizer, paper products, and trash liners and maintain enough stock to ensure no interruption in cleaning procedures.

2026 Cost basis for general cleaning: $_____ per year
2027 Cost basis for general cleaning: $_____ per year
2028 Cost basis for general cleaning: $_____ per year
`;

describe("opportunity import", () => {
  it("loads a structured opportunity JSON file", () => {
    const result = importStructuredJson(
      JSON.stringify(eastBayOpportunityJson),
      "east-bay-library-opportunity.json",
    );

    expect(result.kind).toBe("opportunity");
    if (result.kind !== "opportunity") {
      throw new Error("Expected an opportunity payload.");
    }

    expect(result.opportunity.buyerName).toBe("Traverse Area District Library");
    expect(result.opportunity.opportunityName).toContain("East Bay");
  });

  it("loads a workspace-state JSON file", () => {
    const result = importStructuredJson(
      JSON.stringify(demoWorkspaceStateJson),
      "demo-workspace-state.json",
    );

    expect(result.kind).toBe("workspace");
    if (result.kind !== "workspace") {
      throw new Error("Expected a workspace payload.");
    }

    expect(result.workspaceState.activeDraft.opportunity.buyerName).toBe(
      "Los Angeles County Sheriff's Department",
    );
  });

  it("builds a structured opportunity draft from janitorial RFP text", () => {
    const opportunity = buildOpportunityFromSourceText(
      eastBaySourceText,
      "Cleaning Services East Bay RFP 2026.pdf",
    );

    expect(opportunity.id).toContain("east-bay");
    expect(opportunity.buyerName).toBe("Traverse Area District Library");
    expect(opportunity.opportunityName).toContain("East Bay Branch");
    expect(opportunity.geography.city).toBe("Traverse City");
    expect(opportunity.geography.state).toBe("MI");
    expect(opportunity.siteProfile.siteCount).toBe(1);
    expect(opportunity.siteProfile.totalSquareFeet).toBe(1200);
    expect(opportunity.siteProfile.occupiedHours).toContain("Monday and Thursday");
    expect(opportunity.siteProfile.weekendCoverageRequired).toBe(false);
    expect(opportunity.contract.annualValueEstimate).toBe(25000);
    expect(opportunity.contract.termMonths).toBe(36);
    expect(opportunity.contract.transitionDays).toBe(14);
    expect(opportunity.requirements.requiredServices).toEqual(
      expect.arrayContaining([
        "nightly-cleaning",
        "floor-care",
        "consumables-management",
        "window-touchpoint",
      ]),
    );
    expect(opportunity.requirements.sustainabilityExpectation).toBe(true);
    expect(opportunity.requirements.referencesRequired).toBe(3);
    expect(opportunity.pursuitContext.pricingPressure).toBe("high");
    expect(opportunity.pursuitContext.strategicFit).toBe("low");
    expect(opportunity.pursuitContext.proofPriority).toEqual(
      expect.arrayContaining([
        "emergency response discipline",
        "supply continuity",
      ]),
    );
    expect(opportunity.pursuitContext.notes).toEqual(
      expect.arrayContaining([
        expect.stringContaining("March 31, 2026"),
        expect.stringContaining("Mandatory pre-bid attendance"),
      ]),
    );
  });
});
