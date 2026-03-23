import type { Opportunity } from "../domain/opportunity";
import type {
  ProofExample,
  SolutionModule,
  SolutionPlan,
  StaffingPlan,
  TransitionMilestone,
} from "../domain/solution";
import { buildHotButtons } from "./hotButtonModel";

interface ProofLibraryEntry extends ProofExample {
  noteKeywords: string[];
}

const proofLibrary: ProofLibraryEntry[] = [
  {
    id: "proof-corporate-campus-mobilization",
    title: "Corporate campus mobilization",
    metric: "97% staffing readiness by day 10",
    description:
      "Mobilized a four-building office portfolio with site leads, launch checklists, and buyer-visible readiness reporting.",
    tags: ["transition speed", "labor stability"],
    services: ["nightly-cleaning", "day-porter", "daytime-support"],
    buyerHotButtons: [
      "low-disruption-transition",
      "self-performed-accountability",
      "portfolio-consistency",
    ],
    evidenceType: "transition-playbook",
    bestUse: [
      "Executive summary opening proof",
      "Transition section",
      "Changeover objection counter",
    ],
    noteKeywords: ["transition", "changeover", "takeover", "staffing", "launch"],
  },
  {
    id: "proof-inspection-visibility-program",
    title: "Inspection visibility program",
    metric: "22% reduction in repeat inspection misses",
    description:
      "Deployed QR-coded inspections, supervisor sweeps, and issue closure reporting for a mixed commercial client.",
    tags: ["quality visibility"],
    services: ["floor-care", "nightly-cleaning", "daytime-support"],
    buyerHotButtons: [
      "floor-care-recovery",
      "visible-daytime-support",
      "portfolio-consistency",
    ],
    evidenceType: "operations-metric",
    bestUse: [
      "Quality win theme proof",
      "Buyer-facing quality section",
      "Executive summary support",
    ],
    noteKeywords: ["inspection", "quality", "misses", "appearance", "floor"],
  },
  {
    id: "proof-consumables-reliability-playbook",
    title: "Consumables reliability playbook",
    metric: "99.1% stocked restroom compliance",
    description:
      "Standardized day porter restocking triggers and monthly replenishment forecasting for multi-site operations.",
    tags: ["quality visibility", "labor stability"],
    services: ["consumables-management", "day-porter", "daytime-support"],
    buyerHotButtons: [
      "consumables-reliability",
      "visible-daytime-support",
      "portfolio-consistency",
    ],
    evidenceType: "operations-metric",
    bestUse: [
      "Day porter proof",
      "Consumables reliability messaging",
      "Occupied-hours support section",
    ],
    noteKeywords: ["consumable", "restocking", "restroom", "stocked", "supply"],
  },
  {
    id: "proof-sustainability-support-layer",
    title: "Sustainability support layer",
    metric: "18% reduction in disposable supply variance",
    description:
      "Aligned green cleaning products, dilution control, and operating dashboards with buyer sustainability expectations.",
    tags: ["quality visibility"],
    services: ["nightly-cleaning", "consumables-management"],
    buyerHotButtons: [
      "sustainability-without-instability",
      "consumables-reliability",
    ],
    evidenceType: "operations-metric",
    bestUse: [
      "Sustainability differentiator",
      "Consumables control proof",
    ],
    noteKeywords: ["sustainability", "green", "chemistry", "supply"],
  },
  {
    id: "proof-executive-floor-response-program",
    title: "Executive-floor response program",
    metric: "95% same-shift closure on daytime service requests",
    description:
      "Deployed named day porters, lobby and executive-floor reset standards, and supervisor escalation for high-visibility occupied spaces.",
    tags: ["quality visibility", "labor stability"],
    services: ["day-porter", "daytime-support", "consumables-management"],
    buyerHotButtons: [
      "visible-daytime-support",
      "self-performed-accountability",
      "portfolio-consistency",
    ],
    evidenceType: "operations-metric",
    bestUse: [
      "Executive-floor theme proof",
      "Occupied-hours summary variant",
      "Visible-service objection counter",
    ],
    noteKeywords: ["executive", "daytime", "occupied", "lobby", "visible"],
  },
  {
    id: "proof-floor-care-recovery-sprint",
    title: "Floor care recovery sprint",
    metric: "31% reduction in appearance complaints within 45 days",
    description:
      "Reset floor-care production standards, specialty cadence, and buyer-visible recovery reporting across a four-site office portfolio.",
    tags: ["quality visibility", "transition speed"],
    services: ["floor-care", "nightly-cleaning"],
    buyerHotButtons: [
      "floor-care-recovery",
      "low-disruption-transition",
      "portfolio-consistency",
    ],
    evidenceType: "case-study",
    bestUse: [
      "Floor-care recovery theme",
      "Ghosting angle against inspection-light competitors",
      "Executive summary support",
    ],
    noteKeywords: ["floor", "appearance", "complaint", "recovery", "misses"],
  },
  {
    id: "proof-self-performed-staffing-continuity",
    title: "Self-performed staffing continuity",
    metric: "89% frontline retention through the first 90 days",
    description:
      "Used self-performed recruiting, floating relief coverage, and named site leads to stabilize a multi-site account takeover.",
    tags: ["labor stability", "transition speed"],
    services: ["nightly-cleaning", "day-porter", "daytime-support"],
    buyerHotButtons: [
      "self-performed-accountability",
      "low-disruption-transition",
      "operating-value-under-price-pressure",
    ],
    evidenceType: "case-study",
    bestUse: [
      "Self-performed accountability theme",
      "Changeover and staffing objection counter",
      "Executive summary support",
    ],
    noteKeywords: ["self-performed", "brokered", "labor", "staffing", "retention"],
  },
  {
    id: "proof-budget-rebaseline-without-visible-slippage",
    title: "Budget rebaseline without visible slippage",
    metric: "9% annual operating-cost reduction with no increase in service complaints",
    description:
      "Reworked route density, floor-care scheduling, and supervisory coverage to remove waste without exposing the client to visible service degradation.",
    tags: ["price discipline", "operational value", "route density"],
    services: ["nightly-cleaning", "floor-care", "daytime-support"],
    buyerHotButtons: [
      "operating-value-under-price-pressure",
      "floor-care-recovery",
      "portfolio-consistency",
    ],
    evidenceType: "case-study",
    bestUse: [
      "Executive summary value variant",
      "Price-pressure objection counter",
      "Ghosting angle against low-rate instability",
    ],
    noteKeywords: ["budget", "price", "value", "cost", "efficiency"],
  },
];

function roundToHalf(value: number): number {
  return Math.round(value * 2) / 2;
}

function buildStaffingPlan(opportunity: Opportunity): StaffingPlan {
  const nightlyCleanerFte = roundToHalf(
    opportunity.siteProfile.totalSquareFeet / 28000 +
      opportunity.siteProfile.siteCount * 0.2 +
      (opportunity.siteProfile.weekendCoverageRequired ? 0.5 : 0),
  );
  const dayPorterFte = opportunity.siteProfile.dayPorterRequired
    ? roundToHalf(Math.max(1, opportunity.siteProfile.siteCount * 0.5))
    : 0;
  const supervisorFte = roundToHalf(
    opportunity.siteProfile.siteCount >= 4 ? 1 : 0.5,
  );

  return {
    nightlyCleanerFte,
    dayPorterFte,
    supervisorFte,
    summary: `${nightlyCleanerFte.toFixed(1)} nightly cleaner FTE, ${dayPorterFte.toFixed(
      1,
    )} day porter FTE, and ${supervisorFte.toFixed(
      1,
    )} supervisor FTE to stabilize a ${opportunity.siteProfile.siteCount}-site portfolio.`,
  };
}

function buildTransitionMilestones(opportunity: Opportunity): TransitionMilestone[] {
  return [
    {
      phase: "Launch planning",
      timing: "Days 1-7",
      detail:
        "Confirm scope assumptions, site access, incumbent handoff items, and buyer communication cadence.",
    },
    {
      phase: "Staffing and site readiness",
      timing: "Days 8-14",
      detail:
        "Finalize staffing roster, shift assignments, equipment staging, and checklist-driven startup controls.",
    },
    {
      phase: "Go-live and stabilization",
      timing: `Days 15-${Math.max(opportunity.contract.transitionDays, 21)}`,
      detail:
        "Run launch huddles, supervisor sweeps, and issue closure tracking until the account is operating on a steady state rhythm.",
    },
  ];
}

function buildOpportunitySignals(opportunity: Opportunity): string {
  return [
    ...opportunity.pursuitContext.proofPriority,
    ...opportunity.pursuitContext.notes,
    opportunity.siteProfile.dayPorterRequired ? "visible daytime support" : "",
    opportunity.pursuitContext.incumbentPresent ? "incumbent replacement" : "",
    opportunity.requirements.selfPerformedPreference ? "self performed accountability" : "",
    opportunity.requirements.sustainabilityExpectation
      ? "sustainability without service drift"
      : "",
    opportunity.pursuitContext.pricingPressure !== "low"
      ? "budget control and best value"
      : "",
    opportunity.siteProfile.siteCount > 1 ? "portfolio consistency multisite service" : "",
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function scoreProofEntry(entry: ProofLibraryEntry, opportunity: Opportunity): number {
  const opportunitySignals = buildOpportunitySignals(opportunity);
  const hotButtonWeights = new Map(
    buildHotButtons(opportunity).map((button) => [button.key, button.weight]),
  );
  const matchedServices = entry.services.filter((service) =>
    opportunity.requirements.requiredServices.includes(service),
  ).length;

  let score = matchedServices * 3;

  score += opportunity.pursuitContext.proofPriority.reduce(
    (total, priority) => (entry.tags.includes(priority) ? total + 4 : total),
    0,
  );

  score += entry.tags.reduce(
    (total, tag) => (opportunitySignals.includes(tag.toLowerCase()) ? total + 2 : total),
    0,
  );

  score += entry.buyerHotButtons.reduce(
    (total, button) => total + (hotButtonWeights.get(button) ?? 0),
    0,
  );

  score += entry.noteKeywords.reduce(
    (total, keyword) => (opportunitySignals.includes(keyword) ? total + 2 : total),
    0,
  );

  if (
    opportunity.pursuitContext.incumbentPresent &&
    entry.buyerHotButtons.includes("low-disruption-transition")
  ) {
    score += 3;
  }

  if (
    opportunity.siteProfile.dayPorterRequired &&
    entry.buyerHotButtons.includes("visible-daytime-support")
  ) {
    score += 3;
  }

  if (
    opportunity.requirements.selfPerformedPreference &&
    entry.buyerHotButtons.includes("self-performed-accountability")
  ) {
    score += 3;
  }

  if (
    opportunity.requirements.requiredServices.includes("floor-care") &&
    entry.buyerHotButtons.includes("floor-care-recovery")
  ) {
    score += 3;
  }

  if (
    opportunity.requirements.requiredServices.includes("consumables-management") &&
    entry.buyerHotButtons.includes("consumables-reliability")
  ) {
    score += 3;
  }

  if (
    opportunity.pursuitContext.pricingPressure !== "low" &&
    entry.buyerHotButtons.includes("operating-value-under-price-pressure")
  ) {
    score += 2;
  }

  if (
    opportunity.pursuitContext.pricingPressure !== "low" &&
    entry.noteKeywords.some((keyword) =>
      ["budget", "price", "value", "cost"].includes(keyword),
    )
  ) {
    score += 10;
  }

  return score;
}

function buildProofExamples(opportunity: Opportunity): ProofExample[] {
  return [...proofLibrary]
    .map((entry) => ({
      entry,
      score: scoreProofEntry(entry, opportunity),
    }))
    .sort((left, right) => {
      if (right.score !== left.score) {
        return right.score - left.score;
      }

      return left.entry.title.localeCompare(right.entry.title);
    })
    .slice(0, 6)
    .map(({ entry }) => ({
      id: entry.id,
      title: entry.title,
      metric: entry.metric,
      description: entry.description,
      tags: [...entry.tags],
      services: [...entry.services],
      buyerHotButtons: [...entry.buyerHotButtons],
      evidenceType: entry.evidenceType,
      bestUse: [...entry.bestUse],
    }));
}

function createModule(
  module: Omit<SolutionModule, "assumptions"> & { assumptions?: string[] },
): SolutionModule {
  return {
    ...module,
    assumptions: module.assumptions ?? [],
  };
}

export function assembleSolution(opportunity: Opportunity): SolutionPlan {
  const modules: SolutionModule[] = [
    createModule({
      id: "core-recurring-service",
      name: "Core recurring janitorial program",
      category: "core",
      summary:
        "Self-performed nightly cleaning anchored by scope maps, quality standards, and account-level supervision.",
      rationale:
        "Recurring janitorial service is the base operating layer for the opportunity and gives Boss Key control over consistency.",
      differentiator:
        "Positions Boss Key as an operator with service controls rather than a broker of labor.",
      servicesCovered: ["nightly-cleaning"],
      assumptions: [
        "Scope maps and room frequencies are validated during launch planning.",
      ],
    }),
    createModule({
      id: "mobilization-cell",
      name: "Mobilization and transition cell",
      category: "operations",
      summary:
        "A short-term launch cell handles staffing readiness, site setup, and buyer-visible transition reporting.",
      rationale:
        "Transition confidence matters in private-sector service bids and reduces the buyer's perceived switching risk.",
      differentiator:
        "Makes the proposal feel like an operating plan, not just a staffing promise.",
      servicesCovered: ["nightly-cleaning"],
    }),
    createModule({
      id: "qa-reporting",
      name: "Quality assurance and reporting layer",
      category: "experience",
      summary:
        "Supervisor sweeps, issue closure tracking, and monthly KPI reviews give the buyer a clear service control loop.",
      rationale:
        "Reporting cadence is explicitly requested in the opportunity and helps support a buyer-facing digital experience.",
      differentiator:
        "Turns quality visibility into a concrete operating feature, not a generic promise.",
      servicesCovered: ["nightly-cleaning", "daytime-support"],
    }),
  ];

  if (
    opportunity.siteProfile.dayPorterRequired ||
    opportunity.requirements.requiredServices.includes("day-porter")
  ) {
    modules.push(
      createModule({
        id: "day-porter-coverage",
        name: "Day porter coverage",
        category: "core",
        summary:
          "Daytime support covers restocking, touchpoint response, and lobby or executive-area reset needs during occupied hours.",
        rationale:
          "Visible daytime labor matches the site's occupancy pattern and buyer request for responsive support.",
        differentiator:
          "Creates a more premium, buyer-visible service posture during business hours.",
        servicesCovered: ["day-porter", "daytime-support", "consumables-management"],
      }),
    );
  }

  if (opportunity.requirements.requiredServices.includes("floor-care")) {
    modules.push(
      createModule({
        id: "floor-specialty",
        name: "Floor care and appearance recovery",
        category: "operations",
        summary:
          "Floor care is scheduled as a controlled specialty cadence instead of being buried inside recurring labor assumptions.",
        rationale:
          "The buyer has experienced quality misses on appearance-related work and needs a visible remediation plan.",
        differentiator:
          "Protects perceived service quality on high-visibility surfaces where incumbents often drift.",
        servicesCovered: ["floor-care"],
      }),
    );
  }

  if (
    opportunity.requirements.requiredServices.includes("consumables-management")
  ) {
    modules.push(
      createModule({
        id: "consumables-control",
        name: "Consumables control program",
        category: "experience",
        summary:
          "Restroom and breakroom consumables are tracked with restocking triggers and buyer-ready compliance reporting.",
        rationale:
          "Consumables reliability is one of the visible pain points surfaced in the opportunity notes.",
        differentiator:
          "Binds soft-service execution to measurable buyer confidence metrics.",
        servicesCovered: ["consumables-management", "day-porter"],
      }),
    );
  }

  if (opportunity.requirements.sustainabilityExpectation) {
    modules.push(
      createModule({
        id: "sustainability-ops",
        name: "Sustainability-aligned cleaning operations",
        category: "proof",
        summary:
          "Green chemistry, dilution controls, and supply discipline are included where they support buyer expectations.",
        rationale:
          "Sustainability is an explicit requirement and can reinforce a modern, disciplined operating story.",
        differentiator:
          "Shows operational maturity without turning the proposal into generic ESG language.",
        servicesCovered: ["nightly-cleaning", "consumables-management"],
      }),
    );
  }

  return {
    modules,
    staffing: buildStaffingPlan(opportunity),
    transitionMilestones: buildTransitionMilestones(opportunity),
    proofExamples: buildProofExamples(opportunity),
    assumptions: [
      "Staffing model is directional and intended for qualification-stage sizing, not final pricing approval.",
      "Transition plan assumes timely site access, incumbent asset data, and buyer-side decision availability.",
    ],
  };
}
