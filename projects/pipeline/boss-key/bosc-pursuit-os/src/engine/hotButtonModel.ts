import type { Opportunity } from "../domain/opportunity";
import type { HotButton } from "../domain/pursuitIdeaPack";

interface HotButtonCandidate extends HotButton {}

function includesAny(haystack: string, needles: string[]): boolean {
  return needles.some((needle) => haystack.includes(needle));
}

export function buildHotButtons(opportunity: Opportunity): HotButton[] {
  const notes = opportunity.pursuitContext.notes.map((note) => note.trim());
  const notesText = notes.join(" ").toLowerCase();
  const proofPriorities = opportunity.pursuitContext.proofPriority.map((item) =>
    item.toLowerCase(),
  );
  const requiredServices = new Set(opportunity.requirements.requiredServices);
  const candidates: HotButtonCandidate[] = [];

  const addCandidate = (
    candidate: Omit<HotButtonCandidate, "weight" | "sourceSignals">,
    rules: Array<{ active: boolean; points: number; signal: string }>,
  ) => {
    const sourceSignals = rules.filter((rule) => rule.active).map((rule) => rule.signal);
    const weight = rules.reduce(
      (total, rule) => total + (rule.active ? rule.points : 0),
      0,
    );

    if (weight > 0) {
      candidates.push({
        ...candidate,
        weight,
        sourceSignals,
      });
    }
  };

  addCandidate(
    {
      key: "low-disruption-transition",
      title: "Low-disruption transition",
      buyerSignal:
        "The buyer wants a provider change without an ugly first month, badge chaos, or tenant noise.",
      winLeverage:
        "Position Boss Key as the safer switch because launch ownership, staffing lock, and first-30-day visibility are explicit.",
      proofFocus:
        "Use roster-readiness, launch dashboards, and first-30-day issue-closure proof.",
    },
    [
      {
        active: opportunity.pursuitContext.incumbentPresent,
        points: 3,
        signal: "Incumbent is in place.",
      },
      {
        active: opportunity.contract.transitionDays <= 30,
        points: 3,
        signal: `Transition window is ${opportunity.contract.transitionDays} days.`,
      },
      {
        active: proofPriorities.includes("transition speed"),
        points: 2,
        signal: "Proof priorities emphasize transition speed.",
      },
      {
        active: includesAny(notesText, ["incumbent", "switch", "takeover", "transition"]),
        points: 1,
        signal: "Notes imply switching risk.",
      },
      {
        active: includesAny(notesText, ["first 30 days", "ugly first month", "day one", "startup"]),
        points: 2,
        signal: "Notes explicitly call out early-launch risk.",
      },
    ],
  );

  addCandidate(
    {
      key: "visible-daytime-support",
      title: "Visible daytime support",
      buyerSignal:
        "Executive floors, lobbies, and occupied spaces have to look serviced during the day, not after complaints.",
      winLeverage:
        "Make day porter coverage feel like a managed response layer with named zones and visible standards.",
      proofFocus:
        "Use occupied-hours response proof, reset standards, and same-shift issue-closure evidence.",
    },
    [
      {
        active:
          opportunity.siteProfile.dayPorterRequired ||
          requiredServices.has("day-porter") ||
          requiredServices.has("daytime-support"),
        points: 3,
        signal: "Occupied-hours support is required.",
      },
      {
        active: includesAny(notesText, ["executive", "visible daytime", "occupied", "lobby", "tenant emails"]),
        points: 3,
        signal: "Notes call out executive or visible daytime needs.",
      },
      {
        active: proofPriorities.includes("quality visibility"),
        points: 1,
        signal: "Proof priorities emphasize quality visibility.",
      },
    ],
  );

  addCandidate(
    {
      key: "floor-care-recovery",
      title: "Floor care recovery",
      buyerSignal:
        "Visible appearance misses on floors and common areas are already hurting confidence with the property team.",
      winLeverage:
        "Show how floor care gets its own recovery rhythm instead of being buried inside nightly scope.",
      proofFocus:
        "Use proof that ties floor-care control to appearance recovery and fewer callbacks.",
    },
    [
      {
        active: requiredServices.has("floor-care"),
        points: 2,
        signal: "Floor care is in scope.",
      },
      {
        active: includesAny(notesText, ["floor care", "inspection misses", "appearance", "floor"]),
        points: 3,
        signal: "Notes mention floor-care misses or appearance issues.",
      },
      {
        active: proofPriorities.includes("quality visibility"),
        points: 1,
        signal: "Proof priorities emphasize quality visibility.",
      },
    ],
  );

  addCandidate(
    {
      key: "consumables-reliability",
      title: "Consumables reliability",
      buyerSignal:
        "Restroom and breakroom basics need to stay stocked without the buyer chasing the account team.",
      winLeverage:
        "Present restocking as a route, trigger, and verification system instead of an informal porter habit.",
      proofFocus:
        "Use restroom compliance, replenishment discipline, and occupied-hours response proof.",
    },
    [
      {
        active: requiredServices.has("consumables-management"),
        points: 2,
        signal: "Consumables management is required.",
      },
      {
        active: includesAny(notesText, ["restocking", "consumable", "restroom", "stock"]),
        points: 3,
        signal: "Notes point to restocking problems.",
      },
      {
        active: proofPriorities.includes("quality visibility"),
        points: 1,
        signal: "Proof priorities emphasize quality visibility.",
      },
    ],
  );

  addCandidate(
    {
      key: "self-performed-accountability",
      title: "Self-performed accountability",
      buyerSignal:
        "The buyer wants staffing, supervision, and service recovery to sit inside one operating chain.",
      winLeverage:
        "Ghost subcontractor distance and make accountability a visible reason to trust the service model.",
      proofFocus:
        "Use staffing continuity, named supervision, and launch ownership proof.",
    },
    [
      {
        active: opportunity.requirements.selfPerformedPreference,
        points: 3,
        signal: "Self-performed delivery is preferred.",
      },
      {
        active: includesAny(notesText, ["self-performed", "brokered labor", "brokered"]),
        points: 3,
        signal: "Notes explicitly reject brokered labor.",
      },
      {
        active: proofPriorities.includes("labor stability"),
        points: 2,
        signal: "Proof priorities emphasize labor stability.",
      },
    ],
  );

  addCandidate(
    {
      key: "sustainability-without-instability",
      title: "Sustainability without instability",
      buyerSignal:
        "Green-cleaning expectations cannot come at the expense of reliability, chemistry control, or stocking discipline.",
      winLeverage:
        "Treat sustainability as disciplined operations rather than generic ESG language.",
      proofFocus:
        "Use chemistry, dilution, and supply-variance proof that shows control.",
    },
    [
      {
        active: opportunity.requirements.sustainabilityExpectation,
        points: 2,
        signal: "Sustainability is a stated requirement.",
      },
      {
        active: requiredServices.has("consumables-management"),
        points: 1,
        signal: "Consumables control makes sustainability operationally relevant.",
      },
      {
        active: includesAny(notesText, ["sustainability", "green", "chemistry"]),
        points: 1,
        signal: "Notes mention sustainability concerns.",
      },
    ],
  );

  addCandidate(
    {
      key: "operating-value-under-price-pressure",
      title: "Value without service erosion",
      buyerSignal:
        "The buyer is price-conscious but will punish visible misses and management drag more than a small rate delta.",
      winLeverage:
        "Defend rate by showing the management time, callbacks, and launch friction Boss Key keeps off the buyer's plate.",
      proofFocus:
        "Use complaint stability, launch control, and route-efficiency proof rather than rate talk alone.",
    },
    [
      {
        active: opportunity.pursuitContext.pricingPressure !== "low",
        points: 3,
        signal: `Pricing pressure is ${opportunity.pursuitContext.pricingPressure}.`,
      },
      {
        active: includesAny(notesText, ["rate", "price", "budget", "cost"]),
        points: 3,
        signal: "Notes explicitly mention rate sensitivity or value pressure.",
      },
      {
        active:
          opportunity.siteProfile.dayPorterRequired ||
          opportunity.siteProfile.weekendCoverageRequired,
        points: 1,
        signal: "Coverage requirements make under-scoped labor risky.",
      },
      {
        active: opportunity.contract.annualValueEstimate >= 500000,
        points: 1,
        signal: "Contract value makes switching-risk economics meaningful.",
      },
    ],
  );

  addCandidate(
    {
      key: "portfolio-consistency",
      title: "Portfolio consistency",
      buyerSignal:
        "A four-site service program only feels strong if standards, supervision, and reporting stay consistent across the portfolio.",
      winLeverage:
        "Tell a portfolio-control story instead of letting the pursuit read like four separate site promises.",
      proofFocus:
        "Use multi-site proof and cross-portfolio control metrics.",
    },
    [
      {
        active: opportunity.siteProfile.siteCount > 1,
        points: 2,
        signal: `Portfolio spans ${opportunity.siteProfile.siteCount} sites.`,
      },
      {
        active: opportunity.siteProfile.totalSquareFeet >= 200000,
        points: 1,
        signal: "Square footage is large enough that drift across sites matters.",
      },
    ],
  );

  return candidates
    .sort((left, right) => {
      if (right.weight !== left.weight) {
        return right.weight - left.weight;
      }

      return left.title.localeCompare(right.title);
    })
    .slice(0, 6);
}
