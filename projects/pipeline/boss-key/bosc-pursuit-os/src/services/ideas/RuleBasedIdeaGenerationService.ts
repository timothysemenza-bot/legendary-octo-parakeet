import {
  serviceTypeLabels,
  type Opportunity,
  type ServiceType,
} from "../../domain/opportunity";
import type {
  BuyerConcernResponse,
  CompetitorGhostAngle,
  DifferentiatorOption,
  ExecutiveSummaryVariant,
  HotButton,
  ProofMatch,
  PursuitIdeaContext,
  PursuitIdeaPack,
  TransitionAngle,
  WinTheme,
} from "../../domain/pursuitIdeaPack";
import type { QualificationResult } from "../../domain/qualification";
import type { ProofExample, SolutionModule, SolutionPlan } from "../../domain/solution";
import { buildHotButtons } from "../../engine/hotButtonModel";
import type { IdeaGenerationService } from "./IdeaGenerationService";

function formatServiceLabel(service: ServiceType): string {
  return serviceTypeLabels[service];
}

function formatProofReference(proof: ProofExample): string {
  return `${proof.metric} in ${proof.title}`;
}

function formatProofClause(proof: ProofExample): string {
  return `${proof.metric}, demonstrated in ${proof.title}`;
}

function includesAny(haystack: string, needles: string[]): boolean {
  return needles.some((needle) => haystack.includes(needle));
}

interface OpportunityStorySignals {
  notesText: string;
  visibleAreaLabel: string;
  serviceMissLabel: string;
  managementBurdenLabel: string;
  buyerTeamLabel: string;
  basicsLabel: string;
  launchWindowLabel: string;
  portfolioLabel: string;
  pricingStoryLabel: string;
}

function buildOpportunityStorySignals(
  opportunity: Opportunity,
): OpportunityStorySignals {
  const notesText = opportunity.pursuitContext.notes.join(" ").toLowerCase();
  const publicSectorLike = [
    opportunity.buyerName,
    opportunity.sector,
    ...opportunity.pursuitContext.notes,
  ]
    .join(" ")
    .toLowerCase();
  const hasPublicSectorSignals = includesAny(publicSectorLike, [
    "county",
    "city",
    "district",
    "department",
    "sheriff",
    "public",
    "station",
    "security",
    "background",
  ]);
  const visibleAreaLabel =
    includesAny(notesText, ["public lobby", "public-lobby", "public area", "public-facing"]) &&
    includesAny(notesText, ["restroom", "supply", "consumable"])
      ? "public lobbies, front counters, and restrooms"
      : includesAny(notesText, ["public lobby", "public-lobby", "public area", "public-facing"])
        ? "public lobbies and front counters"
        : 
    includesAny(notesText, ["executive", "lobby"]) &&
    includesAny(notesText, ["restroom", "supply", "consumable"])
      ? "executive floors, lobby touchpoints, and restrooms"
      : includesAny(notesText, ["executive", "lobby"])
        ? "executive floors and lobby touchpoints"
        : opportunity.siteProfile.dayPorterRequired
          ? "occupied spaces and front-of-house touchpoints"
          : "the most visible spaces in the building";
  const serviceMissLabel =
    includesAny(notesText, ["floor"]) &&
    includesAny(notesText, ["restock", "consumable", "restroom", "supply"])
      ? "floor-care misses and empty dispensers"
      : includesAny(notesText, ["floor"])
        ? "floor-care callbacks"
        : includesAny(notesText, ["restock", "consumable", "restroom", "supply"])
          ? "stocking misses"
          : "visible service misses";
  const managementBurdenLabel = includesAny(
    notesText,
    ["tenant email", "tenant emails", "tenant"],
  )
    ? "tenant emails and property-team chase"
    : "avoidable escalations and follow-up work";

  return {
    notesText,
    visibleAreaLabel,
    serviceMissLabel,
    managementBurdenLabel,
    buyerTeamLabel: hasPublicSectorSignals ? "buyer team" : "property team",
    basicsLabel: hasPublicSectorSignals
      ? "empty dispensers or public-area basics"
      : "empty dispensers or breakroom basics",
    launchWindowLabel:
      opportunity.contract.transitionDays <= 30
        ? `first ${opportunity.contract.transitionDays} days`
        : "first 30 days",
    portfolioLabel: `${opportunity.siteProfile.siteCount}-site ${opportunity.sector.toLowerCase()} portfolio`,
    pricingStoryLabel:
      opportunity.pursuitContext.pricingPressure === "high"
        ? "thin pricing that turns into more management work"
        : "rate pressure that cannot be solved by stripping out control",
  };
}

function pickModule(
  modules: SolutionModule[],
  patterns: RegExp[],
): SolutionModule {
  return (
    modules.find((module) =>
      patterns.some((pattern) => pattern.test(module.id) || pattern.test(module.name)),
    ) ?? modules[0]
  );
}

function scoreProof(proof: ProofExample, hotButtons: HotButton[]): number {
  const hotButtonWeights = new Map(
    hotButtons.map((hotButton) => [hotButton.key, hotButton.weight]),
  );

  let score = proof.buyerHotButtons.reduce(
    (total, key) => total + (hotButtonWeights.get(key) ?? 0),
    0,
  );

  score += proof.tags.reduce(
    (total, tag) =>
      total +
      hotButtons.filter((button) =>
        `${button.buyerSignal} ${button.winLeverage} ${button.proofFocus}`
          .toLowerCase()
          .includes(tag.toLowerCase()),
      ).length,
    0,
  );

  if (proof.bestUse.some((item) => /executive summary/i.test(item))) {
    score += 1;
  }

  return score;
}

function rankProofExamples(
  proofExamples: ProofExample[],
  hotButtons: HotButton[],
): ProofExample[] {
  return [...proofExamples].sort((left, right) => {
    const scoreDelta = scoreProof(right, hotButtons) - scoreProof(left, hotButtons);

    if (scoreDelta !== 0) {
      return scoreDelta;
    }

    return left.title.localeCompare(right.title);
  });
}

function pickProofForHotButton(
  proofExamples: ProofExample[],
  hotButtonKey: string,
  fallbackPattern: RegExp,
): ProofExample {
  return (
    proofExamples.find((proof) => proof.buyerHotButtons.includes(hotButtonKey)) ??
    proofExamples.find((proof) =>
      `${proof.title} ${proof.description}`.match(fallbackPattern),
    ) ??
    proofExamples[0]
  );
}

function buildUnifyingConcept(
  qualification: QualificationResult,
  hotButtons: HotButton[],
): string {
  const lead = hotButtons[0]?.key;

  switch (lead) {
    case "low-disruption-transition":
      return "Clean switch, tighter control";
    case "visible-daytime-support":
      return "Visible service control from day one";
    case "self-performed-accountability":
      return "One accountable chain on the floor";
    case "operating-value-under-price-pressure":
      return "Protect the building before defending the rate";
    case "floor-care-recovery":
      return "Visible recovery the buyer can feel";
    default:
      return qualification.status === "pursue"
        ? "Lower-risk janitorial control"
        : "Risk-aware service design";
  }
}

function createWinTheme(
  opportunity: Opportunity,
  hotButton: HotButton,
  proof: ProofExample,
  modules: SolutionModule[],
  signals: OpportunityStorySignals,
): WinTheme {
  switch (hotButton.key) {
    case "low-disruption-transition": {
      const module = pickModule(modules, [/mobilization/i, /transition/i]);

      return {
        id: "theme-low-disruption-transition",
        title: "Switch cleanly, improve quickly",
        customerIssue: hotButton.buyerSignal,
        differentiator: module.differentiator,
        proofPoint: formatProofReference(proof),
        themeStatement: `${opportunity.buyerName} should not spend the ${signals.launchWindowLabel} babysitting a janitorial changeover. Boss Key locks the roster, clears access and equipment before day one, and runs buyer-visible launch huddles, backed by ${formatProofClause(proof)}.`,
      };
    }
    case "visible-daytime-support": {
      const module = pickModule(modules, [/day-porter/i, /day porter/i, /quality/i]);

      return {
        id: "theme-visible-daytime-support",
        title: "Keep occupied spaces inspection-ready",
        customerIssue: hotButton.buyerSignal,
        differentiator: module.differentiator,
        proofPoint: formatProofReference(proof),
        themeStatement: `${signals.visibleAreaLabel} should look reset, stocked, and inspection-ready in the middle of the day, not after an email. Boss Key puts named day-porter zones, response standards, and supervisor escalation behind that promise, backed by ${formatProofClause(proof)}.`,
      };
    }
    case "floor-care-recovery": {
      const module = pickModule(modules, [/floor/i, /quality/i]);

      return {
        id: "theme-floor-care-recovery",
        title: "Recover visible floor quality",
        customerIssue: hotButton.buyerSignal,
        differentiator: module.differentiator,
        proofPoint: formatProofReference(proof),
        themeStatement: `${opportunity.buyerName} needs visible floor recovery, not another promise that things will improve once the account settles in. Boss Key gives floor care its own production cadence, inspections, and callback discipline, backed by ${formatProofClause(proof)}.`,
      };
    }
    case "consumables-reliability": {
      const module = pickModule(modules, [/consumables/i, /day-porter/i]);

      return {
        id: "theme-consumables-reliability",
        title: "Keep basics stocked without chasing",
        customerIssue: hotButton.buyerSignal,
        differentiator: module.differentiator,
        proofPoint: formatProofReference(proof),
        themeStatement: `${opportunity.buyerName} should not have to chase ${signals.basicsLabel}. Boss Key turns restocking into a route, trigger, and verification rhythm, backed by ${formatProofClause(proof)}.`,
      };
    }
    case "self-performed-accountability": {
      const module = pickModule(modules, [/core/i, /nightly/i]);

      return {
        id: "theme-self-performed-accountability",
        title: "Keep accountability in one chain",
        customerIssue: hotButton.buyerSignal,
        differentiator: module.differentiator,
        proofPoint: formatProofReference(proof),
        themeStatement: `When coverage slips or a complaint hits, ${opportunity.buyerName} should know exactly who owns the fix. Boss Key keeps recruiting, day-to-day supervision, and service recovery inside one operating chain, backed by ${formatProofClause(proof)}.`,
      };
    }
    case "sustainability-without-instability": {
      const module = pickModule(modules, [/sustainability/i, /consumables/i]);

      return {
        id: "theme-sustainability-without-instability",
        title: "Meet green expectations without drift",
        customerIssue: hotButton.buyerSignal,
        differentiator: module.differentiator,
        proofPoint: formatProofReference(proof),
        themeStatement: `${opportunity.buyerName} can meet the green-cleaning requirement without inviting chemistry drift or supply noise because approved products, dilution control, and replenishment checks stay inside the operating routine, backed by ${formatProofClause(proof)}.`,
      };
    }
    case "operating-value-under-price-pressure": {
      const module = pickModule(modules, [/core/i, /quality/i]);

      return {
        id: "theme-operating-value-under-price-pressure",
        title: "Protect value before talking rate",
        customerIssue: hotButton.buyerSignal,
        differentiator: module.differentiator,
        proofPoint: formatProofReference(proof),
        themeStatement: `If ${opportunity.buyerName} presses on rate, Boss Key can defend the number in operating terms: fewer daytime misses, a cleaner launch, and less ${signals.managementBurdenLabel}. That value story is backed by ${formatProofClause(proof)}.`,
      };
    }
    default: {
      const module = modules[0];

      return {
        id: `theme-${hotButton.key}`,
        title: hotButton.title,
        customerIssue: hotButton.buyerSignal,
        differentiator: module.differentiator,
        proofPoint: formatProofReference(proof),
        themeStatement: `${opportunity.buyerName} gets a more reliable janitorial operating model because Boss Key ties ${hotButton.title.toLowerCase()} to controlled execution, backed by ${formatProofClause(proof)}.`,
      };
    }
  }
}

function pickThemeProof(
  proofExamples: ProofExample[],
  hotButtonKey: string,
): ProofExample {
  switch (hotButtonKey) {
    case "low-disruption-transition":
      return (
        proofExamples.find(
          (proof) =>
            proof.evidenceType === "transition-playbook" ||
            /mobilization|launch|transition|staffing readiness/i.test(
              `${proof.title} ${proof.description}`,
            ),
        ) ??
        pickProofForHotButton(
          proofExamples,
          hotButtonKey,
          /transition|launch|mobilization|staffing/i,
        )
      );
    case "visible-daytime-support":
      return pickProofForHotButton(
        proofExamples,
        hotButtonKey,
        /executive|daytime|occupied|same-shift/i,
      );
    case "floor-care-recovery":
      return pickProofForHotButton(
        proofExamples,
        hotButtonKey,
        /floor|appearance|inspection|complaint/i,
      );
    case "consumables-reliability":
      return pickProofForHotButton(
        proofExamples,
        hotButtonKey,
        /consumable|restroom|stock|supply/i,
      );
    case "self-performed-accountability":
      return pickProofForHotButton(
        proofExamples,
        hotButtonKey,
        /self-performed|staffing|retention|labor/i,
      );
    case "sustainability-without-instability":
      return pickProofForHotButton(
        proofExamples,
        hotButtonKey,
        /sustainability|green|chemistry|dilution/i,
      );
    case "operating-value-under-price-pressure":
      return (
        proofExamples.find((proof) =>
          /budget|value|cost|slippage/i.test(`${proof.title} ${proof.description}`),
        ) ??
        pickProofForHotButton(
          proofExamples,
          hotButtonKey,
          /budget|value|cost|slippage/i,
        )
      );
    default:
      return pickProofForHotButton(
        proofExamples,
        hotButtonKey,
        /quality|transition|service/i,
      );
  }
}

function buildWinThemes(
  opportunity: Opportunity,
  hotButtons: HotButton[],
  solution: SolutionPlan,
  proofExamples: ProofExample[],
): WinTheme[] {
  const signals = buildOpportunityStorySignals(opportunity);

  return hotButtons.slice(0, 5).map((hotButton) =>
    createWinTheme(
      opportunity,
      hotButton,
      pickThemeProof(proofExamples, hotButton.key),
      solution.modules,
      signals,
    ),
  );
}

function buildDifferentiatorOptions(
  modules: SolutionModule[],
): DifferentiatorOption[] {
  return modules.slice(0, 4).map((module) => ({
    id: module.id,
    title: module.name,
    feature: module.summary,
    benefit: module.differentiator,
    whyItWins: module.rationale,
  }));
}

function pushConcern(
  concerns: BuyerConcernResponse[],
  concern: BuyerConcernResponse,
) {
  if (!concerns.some((item) => item.concern === concern.concern)) {
    concerns.push(concern);
  }
}

function buildBuyerConcerns(
  opportunity: Opportunity,
  qualification: QualificationResult,
  hotButtons: HotButton[],
  proofExamples: ProofExample[],
): BuyerConcernResponse[] {
  const concerns: BuyerConcernResponse[] = [];
  const signals = buildOpportunityStorySignals(opportunity);

  if (opportunity.pursuitContext.pricingPressure !== "low") {
    const proof = pickThemeProof(proofExamples, "operating-value-under-price-pressure");

    pushConcern(concerns, {
      concern: "If your price is not the lowest, what am I really buying?",
      whyItMatters:
        `${signals.buyerTeamLabel.charAt(0).toUpperCase()}${signals.buyerTeamLabel.slice(1)} will pay to avoid callbacks, rework, and visible service noise, but only if the value bridge feels concrete.`,
      responseAngle: "Bridge rate to fewer escalations and less management chase.",
      counterMessage:
        `Show the buyer where the labor and supervision sit: staffed daytime response, floor-care recovery, and a launch plan that does not dump work back on the ${signals.buyerTeamLabel}. Tie the number to less ${signals.managementBurdenLabel}.`,
      proofToUse: formatProofReference(proof),
    });
  }

  hotButtons.forEach((hotButton) => {
    const proof = pickThemeProof(proofExamples, hotButton.key);

    switch (hotButton.key) {
      case "low-disruption-transition":
        pushConcern(concerns, {
          concern: "How do I know the first month will not get messy?",
          whyItMatters:
            "A dissatisfied buyer can still stay with the incumbent if the replacement story feels like badge chaos, call-outs, and tenant noise.",
          responseAngle: "Sell the first 30 days like an operating plan.",
          counterMessage:
            "Walk through the locked roster, access checks, equipment staging, and weekly launch huddles so the buyer can see who owns day one through day 30.",
          proofToUse: formatProofReference(proof),
        });
        break;
      case "visible-daytime-support":
        pushConcern(concerns, {
          concern: "What keeps the day porter from disappearing once the building gets busy?",
          whyItMatters:
            "High-visibility occupied spaces create fast reputational damage when response is inconsistent or informal.",
          responseAngle: "Present daytime coverage as a managed response layer with named zones and escalation.",
          counterMessage:
            `Tie the role to named zones, midday resets across ${signals.visibleAreaLabel}, and a supervisor response clock rather than vague "as needed" coverage.`,
          proofToUse: formatProofReference(proof),
        });
        break;
      case "floor-care-recovery":
        pushConcern(concerns, {
          concern: "How do I know floor work will not get buried behind nightly scope?",
          whyItMatters:
            "If visible appearance issues persist, the buyer will question the whole service model no matter what the scorecard says.",
          responseAngle: "Separate appearance recovery from generic recurring labor.",
          counterMessage:
            "Show the specialty cadence, appearance checkpoints, and callback discipline that keep floor-care quality visible and measurable.",
          proofToUse: formatProofReference(proof),
        });
        break;
      case "consumables-reliability":
        pushConcern(concerns, {
          concern: "What prevents supply misses from becoming another management chore?",
          whyItMatters:
            "Buyers experience empty dispensers and missing basics as avoidable sloppiness.",
          responseAngle: "Tie consumables to triggers and compliance checks.",
          counterMessage:
            "Show restocking triggers, route checks, and supervisor verification that keep basic supplies from turning into buyer emails.",
          proofToUse: formatProofReference(proof),
        });
        break;
      case "self-performed-accountability":
        pushConcern(concerns, {
          concern: "Who actually owns staffing if someone calls out or the launch gets thin?",
          whyItMatters:
            "If the buyer suspects labor brokering or a loose bench, accountability becomes harder to trust.",
          responseAngle: "Lead with one operating chain and named supervision.",
          counterMessage:
            "Make the bench, relief plan, and named site supervision explicit so the buyer never pictures a subcontractor scramble.",
          proofToUse: formatProofReference(proof),
        });
        break;
      default:
        break;
    }
  });

  if (
    opportunity.requirements.sustainabilityExpectation &&
    !concerns.some((item) => item.concern.includes("green"))
  ) {
    const proof = pickProofForHotButton(
      proofExamples,
      "sustainability-without-instability",
      /sustainability|green/i,
    );

    pushConcern(concerns, {
      concern: "Green-cleaning requirements could weaken service reliability.",
      whyItMatters:
        "Buyers will reject sustainability language that is not grounded in operating discipline.",
      responseAngle: "Show green operations as controlled chemistry and supply discipline.",
      counterMessage:
        "Link sustainability to dilution control, approved products, and supply variance checks so the requirement reads as operational rigor.",
      proofToUse: formatProofReference(proof),
    });
  }

  return concerns.slice(0, 5);
}

function pushGhostAngle(
  angles: CompetitorGhostAngle[],
  angle: CompetitorGhostAngle,
) {
  if (!angles.some((item) => item.title === angle.title)) {
    angles.push(angle);
  }
}

function buildCompetitorGhostAngles(
  opportunity: Opportunity,
  hotButtons: HotButton[],
  proofExamples: ProofExample[],
): CompetitorGhostAngle[] {
  if (!opportunity.pursuitContext.incumbentPresent) {
    return [];
  }

  const angles: CompetitorGhostAngle[] = [];
  const signals = buildOpportunityStorySignals(opportunity);

  hotButtons.forEach((hotButton) => {
    const proof = pickThemeProof(proofExamples, hotButton.key);

    switch (hotButton.key) {
      case "low-disruption-transition":
        pushGhostAngle(angles, {
          id: "ghost-low-disruption-transition",
          title: "Ghost the seamless-start claim",
          buyerRisk:
            "Competitors often promise an easy handoff without showing who owns launch readiness.",
          ghostStatement:
            `Most janitorial offers say "seamless transition" and stop there. Boss Key shows who locks the roster, clears site access, and closes issues during the ${signals.launchWindowLabel}.`,
          bossKeyCounter:
            "Make launch ownership, staffing lock, and buyer-visible reporting concrete enough that the buyer can picture the first month.",
          proofToUse: formatProofReference(proof),
        });
        break;
      case "visible-daytime-support":
        pushGhostAngle(angles, {
          id: "ghost-visible-daytime-support",
          title: "Ghost generic daytime coverage",
          buyerRisk:
            "Many janitorial offers hide daytime support inside a staffing table instead of showing how occupied-hours response works.",
          ghostStatement:
            `Most bids list day porter hours and call it coverage. Boss Key shows how ${signals.visibleAreaLabel} get reset, stocked, and escalated before the buyer asks twice.`,
          bossKeyCounter:
            "Treat day porter coverage as a customer-facing response layer with named zones and visible standards, not a spare labor bucket.",
          proofToUse: formatProofReference(proof),
        });
        break;
      case "floor-care-recovery":
        pushGhostAngle(angles, {
          id: "ghost-floor-care-recovery",
          title: "Ghost inspection-light quality claims",
          buyerRisk:
            "Competitors often promise quality but never show how visible floor-care misses are found and corrected.",
          ghostStatement:
            "Plenty of providers promise quality while floor work stays buried inside the nightly block. Boss Key separates the floor-care cadence, inspection rhythm, and callback control.",
          bossKeyCounter:
            "Position Boss Key as the operator that can show how visible appearance recovery will actually be managed.",
          proofToUse: formatProofReference(proof),
        });
        break;
      case "self-performed-accountability":
        pushGhostAngle(angles, {
          id: "ghost-self-performed-accountability",
          title: "Ghost brokered-labor distance",
          buyerRisk:
            "A competitor may offer coverage but still separate recruiting, supervision, and accountability.",
          ghostStatement:
            "Without naming anyone, contrast one accountable operating chain against models where the buyer ends up chasing multiple parties for coverage, call-outs, and correction.",
          bossKeyCounter:
            "Make self-performed staffing, named supervision, and relief coverage part of the reason Boss Key is easier to trust.",
          proofToUse: formatProofReference(proof),
        });
        break;
      case "operating-value-under-price-pressure":
        pushGhostAngle(angles, {
          id: "ghost-operating-value-under-price-pressure",
          title: "Ghost low-rate instability",
          buyerRisk:
            "Lower-priced offers often understate the labor and supervision needed to hold service quality.",
          ghostStatement:
            `A thin rate is not a savings story if it creates more ${signals.managementBurdenLabel}, service noise, and launch friction.`,
          bossKeyCounter:
            "Explain how Boss Key protects value by removing avoidable service noise and management overhead before defending the rate.",
          proofToUse: formatProofReference(proof),
        });
        break;
      default:
        break;
    }
  });

  return angles.slice(0, 4);
}

function buildTransitionAngles(
  opportunity: Opportunity,
  hotButtons: HotButton[],
  solution: SolutionPlan,
): TransitionAngle[] {
  const angles: TransitionAngle[] = [
    {
      id: "transition-launch-control-sprint",
      title: "Launch control sprint",
      bestFit: "Best when the buyer needs a clean switch from the incumbent with visible first-month control.",
      moves: solution.transitionMilestones.map(
        (milestone) => `${milestone.phase}: ${milestone.detail}`,
      ),
    },
  ];

  if (hotButtons.some((item) => item.key === "visible-daytime-support")) {
    angles.push({
      id: "transition-occupied-hours-assurance",
      title: "Occupied-hours assurance",
      bestFit:
        "Best when executive floors, lobbies, and high-traffic spaces matter as much as after-hours production.",
      moves: [
        "Stand up named day porter coverage before steady-state routines begin.",
        "Use launch huddles to review visible misses and same-day corrective action.",
        "Give the buyer a simple occupied-hours issue-closure cadence during the first month.",
      ],
    });
  }

  if (hotButtons.some((item) => item.key === "floor-care-recovery")) {
    angles.push({
      id: "transition-appearance-recovery-burst",
      title: "Appearance recovery burst",
      bestFit: "Best when the buyer is reacting to recurring floor-care misses or visible appearance complaints.",
      moves: [
        "Validate specialty scope and appearance standards before go-live.",
        "Sequence recovery work so the most visible surfaces improve first.",
        "Show the buyer a first-45-day recovery rhythm with inspection checkpoints.",
      ],
    });
  }

  if (
    opportunity.requirements.requiredServices.includes("consumables-management") ||
    opportunity.requirements.sustainabilityExpectation
  ) {
    angles.push({
      id: "transition-supply-discipline-startup",
      title: "Supply discipline startup",
      bestFit: "Best when restocking reliability and green-cleaning control are part of the buying decision.",
      moves: [
        "Lock approved consumables and chemistry before go-live.",
        "Set launch-period restocking triggers by site traffic profile.",
        "Review first-month supply variance and buyer concerns in the weekly launch huddle.",
      ],
    });
  }

  return angles.slice(0, 3);
}

function describeProofStrength(proof: ProofExample): string {
  switch (proof.evidenceType) {
    case "transition-playbook":
      return "Best when you need to reduce switching risk fast.";
    case "case-study":
      return "Best when the buyer needs a credible before-and-after operating example.";
    default:
      return "Best when you need a quantified operations proof point.";
  }
}

function buildProofMatches(
  proofExamples: ProofExample[],
  hotButtons: HotButton[],
): ProofMatch[] {
  const hotButtonTitles = new Map(
    hotButtons.map((hotButton) => [hotButton.key, hotButton.title]),
  );

  return proofExamples.slice(0, 6).map((proof) => {
    const matchedButtons = proof.buyerHotButtons
      .map((key) => hotButtonTitles.get(key))
      .filter((value): value is string => Boolean(value));

    return {
      id: proof.id,
      title: proof.title,
      metric: proof.metric,
      hotButton: matchedButtons[0] ?? "General buyer confidence",
      whyItFits:
        matchedButtons.length > 0
          ? `It directly supports ${matchedButtons.join(" and ")}.`
          : proof.description,
      strength: describeProofStrength(proof),
      whereToUse: proof.bestUse[0] ?? "Executive summary and proof callouts.",
    };
  });
}

function buildExecutiveSummaryVariants(
  opportunity: Opportunity,
  hotButtons: HotButton[],
  proofExamples: ProofExample[],
): ExecutiveSummaryVariant[] {
  const signals = buildOpportunityStorySignals(opportunity);
  const siteDriver = `${opportunity.siteProfile.siteCount}-site portfolio`;
  const occupancyDriver = `${opportunity.siteProfile.occupiedHours} occupied-hours pattern`;
  const transitionDriver = `${opportunity.contract.transitionDays}-day transition window`;
  const daytimeDriver = includesAny(signals.notesText, ["executive", "lobby"])
    ? "Executive floors and lobby touchpoints set the tone"
    : "Visible daytime spaces set the tone";
  const supplyDriver = includesAny(
    signals.notesText,
    ["restroom", "supply", "consumable"],
  )
    ? "Restocking misses trigger emails fast"
    : "Visible misses trigger follow-up fast";
  const transitionProof = pickThemeProof(proofExamples, "low-disruption-transition");
  const daytimeProof = pickThemeProof(proofExamples, "visible-daytime-support");
  const qualityProof = pickThemeProof(proofExamples, "floor-care-recovery");
  const staffingProof = pickThemeProof(proofExamples, "self-performed-accountability");
  const valueProof = pickThemeProof(
    proofExamples,
    "operating-value-under-price-pressure",
  );

  return [
    {
      id: "summary-switch-cleanly-then-stabilize",
      title: "Switch cleanly, then stabilize",
      openingLine: `${opportunity.buyerName} can change janitorial providers without burning the ${signals.launchWindowLabel} on coverage gaps, callbacks, and follow-up work.`,
      customerDrivers: [
        siteDriver,
        transitionDriver,
        `Incumbent pain: ${signals.serviceMissLabel}`,
      ],
      solutionFrame:
        "Lead with the locked launch roster, named site leads, access readiness, and a first-30-day dashboard before talking about steady state.",
      proofThread: `Prove it with ${formatProofReference(transitionProof)} and ${formatProofReference(qualityProof)}.`,
      close:
        "This variant sells risk removal before it sells polish or rate.",
      useWhen:
        "Use when the buyer is fed up with the incumbent but still nervous about a messy changeover.",
    },
    {
      id: "summary-make-the-building-easier-to-manage",
      title: "Make the building easier to manage",
      openingLine: `${opportunity.buyerName} should feel less janitorial drag during the day: ${signals.visibleAreaLabel} stay reset, supplies stay stocked, and the ${signals.buyerTeamLabel} stops chasing basics.`,
      customerDrivers: [
        siteDriver,
        occupancyDriver,
        daytimeDriver,
        supplyDriver,
      ],
      solutionFrame:
        "Lead with named day-porter zones, midday reset standards, restroom checks, and same-day supervisor escalation.",
      proofThread: `Prove it with ${formatProofReference(daytimeProof)} and ${formatProofReference(pickThemeProof(proofExamples, "consumables-reliability"))}.`,
      close:
        "This variant makes daytime control and management relief the buying reason.",
      useWhen:
        "Use when executive floors, lobbies, restrooms, and same-day response dominate the conversation.",
    },
    {
      id: "summary-one-accountable-operating-chain",
      title: "One accountable operating chain",
      openingLine: `${opportunity.buyerName} gets an easier provider to trust when staffing, supervision, and service recovery sit inside one accountable chain instead of being brokered across multiple hands.`,
      customerDrivers: [
        siteDriver,
        transitionDriver,
        hotButtons.some((item) => item.key === "self-performed-accountability")
          ? "Named supervision stays visible"
          : "Operating ownership stays visible",
        hotButtons.some((item) => item.key === "operating-value-under-price-pressure")
          ? "Rate defense tied to fewer callbacks"
          : "Portfolio control",
        opportunity.requirements.sustainabilityExpectation
          ? "Sustainability without instability"
          : "Service stability under pressure",
      ],
      solutionFrame:
        "Lead with direct staffing ownership, named site supervision, and the relief plan that keeps service from wobbling under pressure.",
      proofThread: `Prove it with ${formatProofReference(staffingProof)} and ${formatProofReference(valueProof)}.`,
      close:
        "This variant sells trust in the operating chain, not just trust in the promise.",
      useWhen:
        "Use when the buyer is comparing labor models, worrying about value, or reacting against brokered accountability.",
    },
  ];
}

function buildValidationQuestions(
  qualification: QualificationResult,
  context: PursuitIdeaContext,
  hotButtons: HotButton[],
): string[] {
  const questions = [
    ...qualification.recommendedActions,
    ...context.openActionTitles.slice(0, 2),
    ...hotButtons.slice(0, 2).map(
      (hotButton) =>
        `What independent proof best supports "${hotButton.title}" without sounding generic?`,
    ),
    ...context.assumptions.slice(0, 1).map(
      (assumption) => `What evidence will confirm or retire this assumption: ${assumption}?`,
    ),
    "Which ghost angle is strongest, and what proof makes it credible?",
    `What has to be true before ${context.nextCheckpointTitle} is genuinely ready?`,
  ];

  return questions.slice(0, 6);
}

export class RuleBasedIdeaGenerationService implements IdeaGenerationService {
  compose(
    opportunity: Opportunity,
    qualification: QualificationResult,
    solution: SolutionPlan,
    context: PursuitIdeaContext,
  ): PursuitIdeaPack {
    const hotButtons = buildHotButtons(opportunity);
    const proofExamples = rankProofExamples(solution.proofExamples, hotButtons);
    const unifyingConcept = buildUnifyingConcept(qualification, hotButtons);
    const storySignals = buildOpportunityStorySignals(opportunity);
    const services = opportunity.requirements.requiredServices
      .map(formatServiceLabel)
      .slice(0, 4)
      .join(", ");
    const leadProof = proofExamples[0];
    const leadHotButton = hotButtons[0];

    return {
      strategyMemo: {
        headline: `${opportunity.buyerName} pursuit ideas for ${opportunity.opportunityName}`,
        pursuitCall: qualification.status,
        unifyingConcept,
        elevatorPitch: `${opportunity.buyerName} should see Boss Key as the operator that can keep ${storySignals.visibleAreaLabel} under control, switch the ${storySignals.portfolioLabel} without a messy first month, and defend its rate through less ${storySignals.managementBurdenLabel}, backed by ${leadProof ? formatProofClause(leadProof) : `credible proof across ${services}`}.`,
        priorities: [
          leadHotButton
            ? `Lead with ${leadHotButton.winLeverage}.`
            : "Lead with the strongest customer-facing risk reduction story.",
          `Turn the first two hot buttons into quantified theme statements before ${context.nextCheckpointTitle}.`,
          leadProof
            ? `Use ${formatProofReference(leadProof)} as the anchor proof item.`
            : "Select one anchor proof item before you lock the story.",
          "Ghost likely competitor patterns with evidence rather than direct comparison.",
        ],
      },
      hotButtons,
      winThemes: buildWinThemes(opportunity, hotButtons, solution, proofExamples),
      differentiatorOptions: buildDifferentiatorOptions(solution.modules),
      buyerConcerns: buildBuyerConcerns(
        opportunity,
        qualification,
        hotButtons,
        proofExamples,
      ),
      competitorGhostAngles: buildCompetitorGhostAngles(
        opportunity,
        hotButtons,
        proofExamples,
      ),
      transitionAngles: buildTransitionAngles(opportunity, hotButtons, solution),
      proofMatches: buildProofMatches(proofExamples, hotButtons),
      executiveSummaryVariants: buildExecutiveSummaryVariants(
        opportunity,
        hotButtons,
        proofExamples,
      ),
      validationQuestions: buildValidationQuestions(
        qualification,
        context,
        hotButtons,
      ),
    };
  }
}
