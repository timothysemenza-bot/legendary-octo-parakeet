import type { Opportunity, ServiceType } from "../../domain/opportunity";
import { serviceTypeLabels } from "../../domain/opportunity";
import type {
  Brief90,
  DecisionFeedCard,
  ProposalNarrativeSections,
} from "../../domain/proposalExperience";
import type { QualificationResult } from "../../domain/qualification";
import type { ProofExample, SolutionPlan } from "../../domain/solution";
import type { NarrativeService } from "./NarrativeService";

function formatServiceLabel(service: ServiceType): string {
  return serviceTypeLabels[service];
}

function formatStatus(status: QualificationResult["status"]): string {
  if (status === "no-bid") {
    return "No-bid";
  }

  if (status === "pursue") {
    return "Pursue";
  }

  return "Review";
}

function formatProofReference(proof: ProofExample | undefined): string {
  if (!proof) {
    return "portfolio-ready operating proof";
  }

  return `${proof.metric} in ${proof.title}`;
}

function buildBuyerFraming(
  opportunity: Opportunity,
  solution: SolutionPlan,
): string {
  const occupiedSpacesLine = opportunity.siteProfile.dayPorterRequired
    ? "visible daytime support in occupied spaces"
    : "steady recurring control without management chase";
  const leadModule = solution.modules[0];

  return `${opportunity.buyerName} gets a cleaner, easier-to-manage portfolio through ${leadModule?.differentiator.toLowerCase() ?? "a self-performed operating model"}, ${occupiedSpacesLine}, and a transition that feels stable from day one.`;
}

function buildBrief90(
  opportunity: Opportunity,
  solution: SolutionPlan,
): Brief90 {
  const leadProof = solution.proofExamples[0];

  return {
    title: "90-second brief",
    summary: `${opportunity.buyerName} is not just buying cleaning hours. The real decision is whether the next provider can make ${opportunity.siteProfile.siteCount} sites easier to trust, easier to manage, and easier to transition without visible service noise.`,
    signalChips: [
      `${opportunity.siteProfile.siteCount} sites`,
      `${opportunity.siteProfile.totalSquareFeet.toLocaleString()} square feet`,
      `${opportunity.contract.transitionDays}-day transition`,
      `${opportunity.siteProfile.occupiedHours} occupancy`,
    ],
    decisionPoints: [
      "Will occupied spaces feel more controlled and inspection-ready every day?",
      "Can the provider switch in without a messy first month?",
      `Is there proof that the operating model holds up? ${formatProofReference(leadProof)}.`,
    ],
  };
}

function buildDecisionFeed(
  opportunity: Opportunity,
  qualification: QualificationResult,
  solution: SolutionPlan,
  services: string[],
): DecisionFeedCard[] {
  const leadProof = solution.proofExamples[0];
  const supportProof = solution.proofExamples[1];
  const leadModules = solution.modules.slice(0, 3);
  const firstMilestones = solution.transitionMilestones.slice(0, 3);
  const dayPorterSignal = opportunity.siteProfile.dayPorterRequired
    ? "Named daytime response is part of the operating model, not an afterthought."
    : "Nightly production stays controlled without creating extra management load during the day.";
  const weekendSignal = opportunity.siteProfile.weekendCoverageRequired
    ? "Weekend coverage is already built into the service rhythm."
    : "The service rhythm is designed for weekday consistency without unnecessary weekend overhead.";

  return [
    {
      id: "buyer-friction",
      label: "What this fixes",
      headline: `Reduce visible service noise across ${opportunity.siteProfile.siteCount} sites`,
      summary:
        "This pursuit is really about reducing the friction buyers feel when occupied spaces, restocking, and visible quality issues force management to keep chasing the janitorial partner.",
      bullets: [
        `${opportunity.siteProfile.occupiedHours} operating pattern means the service model has to work while people are in the building.`,
        `${services.slice(0, 3).join(", ")} are part of the visible buyer experience, not back-of-house details.`,
        `A ${opportunity.contract.transitionDays}-day transition window leaves little room for handoff confusion.`,
      ],
      tone: "signal",
    },
    {
      id: "operating-chain",
      label: "Why this feels lower-risk",
      headline: "One accountable operating chain beats a generic vendor promise",
      summary:
        "The offer should read as an operating system with visible control points, named ownership, and self-performed accountability instead of a commodity labor plan.",
      bullets: leadModules.map(
        (module) => `${module.name}: ${module.differentiator}`,
      ),
      tone: "confidence",
    },
    {
      id: "launch-sequence",
      label: "What changes first",
      headline: "The first 30 days are meant to feel structured, not dramatic",
      summary:
        "Decision-makers shaped by fast media still want one thing from a new provider: immediate clarity on what happens next and how fast they will feel the difference.",
      bullets: firstMilestones.map(
        (milestone) => `${milestone.phase}: ${milestone.detail}`,
      ),
      proof: `${opportunity.contract.transitionDays}-day launch window`,
      tone: "transition",
    },
    {
      id: "proof-stack",
      label: "Proof that travels",
      headline: "Short-form buyers still need receipts",
      summary:
        "Fast-scanning audiences decide quickly, but they still anchor on proof. The strongest proofs here are measurable, portable, and easy to repeat in conversation.",
      bullets: [leadProof, supportProof]
        .filter((proof): proof is ProofExample => Boolean(proof))
        .map((proof) => `${proof.title}: ${proof.metric}`),
      proof: formatProofReference(leadProof),
      tone: "proof",
    },
    {
      id: "daily-experience",
      label: "What their team will notice",
      headline: opportunity.siteProfile.dayPorterRequired
        ? "Occupied spaces should feel reset faster and easier to trust"
        : "Recurring cleaning should feel steadier and less distracting to manage",
      summary:
        qualification.status === "no-bid"
          ? "Even if the current pursuit is not yet worth advancing, the buyer-facing shape still needs to show how a cleaner operating model would feel in practice."
          : "The best buyer-facing story is not a long explanation. It is a few strong signals that make daily operations feel calmer, cleaner, and easier to oversee.",
      bullets: [
        dayPorterSignal,
        weekendSignal,
        `Core service mix: ${services.slice(0, 4).join(", ")}.`,
      ],
      tone: "signal",
    },
  ];
}

export class RuleBasedNarrativeService implements NarrativeService {
  compose(
    opportunity: Opportunity,
    qualification: QualificationResult,
    solution: SolutionPlan,
  ): ProposalNarrativeSections {
    const services = opportunity.requirements.requiredServices.map(formatServiceLabel);

    const statusLabel = formatStatus(qualification.status);
    const headline = `${opportunity.buyerName} operating plan for a ${opportunity.siteProfile.siteCount}-site ${opportunity.sector.toLowerCase()} portfolio`;
    const buyerFraming = buildBuyerFraming(opportunity, solution);
    const summary = `${opportunity.buyerName} needs a janitorial partner that can hold visible quality across ${opportunity.siteProfile.siteCount} sites without making the transition feel risky. Boss Key is positioned around self-performed service control, visible transition management, and buyer-facing quality reporting for ${services.slice(
      0,
      3,
    ).join(", ")}.`;

    return {
      overview: {
        headline,
        summary,
        buyerFraming,
        recommendation:
          qualification.status === "pursue"
            ? "Advance with a controlled pursuit plan and preserve differentiation around launch confidence and quality visibility."
            : qualification.status === "review"
              ? "Advance only after resolving the visible risk flags and confirming the commercial posture."
              : "Do not advance without changing the pursuit economics or operating assumptions.",
      },
      scopeSummary: {
        operatingModel: solution.staffing.summary,
        coveragePlan: `Coverage is shaped around ${opportunity.siteProfile.occupiedHours} occupancy with ${
          opportunity.siteProfile.weekendCoverageRequired
            ? "weekend support included"
            : "weekday-only support assumed"
        }.`,
        serviceLines: services,
        assumptions: [
          ...qualification.assumptions,
          ...solution.assumptions,
        ],
      },
      differentiators: [
        "Proposal experience is structured around service controls, not generic narrative pages.",
        "Transition is presented as a managed operating motion with milestones and visible buyer checkpoints.",
        "Proof points are attached to buyer priorities and required services instead of inserted as disconnected testimonials.",
        ...solution.modules.slice(0, 2).map((module) => module.differentiator),
      ],
      transitionApproach: {
        title: "Controlled transition with buyer-visible launch reporting",
        summary:
          "The transition plan creates a short-term launch cell, staged staffing readiness, and account stabilization checkpoints before the service is treated as steady state.",
        milestones: solution.transitionMilestones,
      },
      brief90: buildBrief90(opportunity, solution),
      decisionFeed: buildDecisionFeed(
        opportunity,
        qualification,
        solution,
        services,
      ),
      exportSummary: {
        sections: [
          {
            title: "Opportunity snapshot",
            items: [
              `Buyer: ${opportunity.buyerName}`,
              `Portfolio: ${opportunity.siteProfile.siteCount} sites / ${opportunity.siteProfile.totalSquareFeet.toLocaleString()} square feet`,
              `Annual value estimate: $${opportunity.contract.annualValueEstimate.toLocaleString()}`,
              `Start date: ${opportunity.contract.startDate}`,
            ],
          },
          {
            title: "Qualification",
            items: [
              `Recommendation: ${statusLabel}`,
              `Score: ${qualification.score}/100`,
              ...qualification.riskFlags.map(
                (flag) => `${flag.title}: ${flag.detail}`,
              ),
            ],
          },
          {
            title: "Solution modules",
            items: solution.modules.map(
              (module) => `${module.name}: ${module.summary}`,
            ),
          },
        ],
      },
    };
  }
}
