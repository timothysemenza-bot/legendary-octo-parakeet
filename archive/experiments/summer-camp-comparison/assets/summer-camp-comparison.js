const CAMPS = [
  {
    id: "westfield-friends",
    name: "Westfield Friends School Summer Camp",
    shortName: "Westfield Friends",
    location: "Cinnaminson, NJ",
    category: "School camp",
    driveMinutes: 4,
    distanceText: "Local",
    ageMin: 2,
    ageMax: 9,
    ageConfidence: "direct",
    ageText: "Ages 2 through rising 4th grade; child must be toilet trained",
    sessionText: "Runs Jun 22 - Aug 14, 2026 with week-by-week enrollment",
    hoursText: "Full day 8:30 AM - 4:00 PM or half day 8:30 AM - 12:30 PM; extended care 7:30 - 8:30 AM and 4:00 - 5:30 PM",
    coreStart: 510,
    coreEnd: 960,
    earliestStart: 450,
    latestEnd: 1050,
    extendedCare: true,
    pricingVisibility: "published",
    weeklyEstimate: 460,
    costText: "$460/week full day, $360/week half day, $125 registration fee; sibling and multi-week discounts",
    focusTags: ["general", "academics"],
    highlights: [
      "Strongest direct fit for both a 3-year-old and a 5-year-old.",
      "Most flexible local schedule because families can register week by week.",
      "Extended care is clearly published instead of hidden behind a phone call."
    ],
    tradeoffs: [
      "Toilet training is required.",
      "Registration fee applies unless the early deadline waiver is still available."
    ],
    constraints: ["Toilet trained"],
    summary: "The most transparent nearby option, with flexible enrollment and clear before/after care.",
    sources: [
      { label: "Westfield Friends School", url: "https://www.westfieldfriends.org/apps/pages/summercamp2026" }
    ]
  },
  {
    id: "st-charles",
    name: "St. Charles Borromeo Parish School Summer Camp",
    shortName: "St. Charles Borromeo",
    location: "Cinnaminson, NJ",
    category: "School camp",
    driveMinutes: 4,
    distanceText: "Local",
    ageMin: 4,
    ageMax: 7,
    ageConfidence: "direct",
    ageText: "Ages 4-7",
    sessionText: "Two sessions: Jun 23 - Jul 18, 2026 and Jul 21 - Aug 15, 2026",
    hoursText: "Monday to Friday; full day 8:00 AM - 4:00 PM with a half-day option",
    coreStart: 480,
    coreEnd: 960,
    earliestStart: 480,
    latestEnd: 960,
    extendedCare: false,
    pricingVisibility: "estimated",
    weeklyEstimate: 375,
    costText: "2025 brochure showed about $1,500 per full-day session, $800 half-day, plus $150 registration fee; 2026 pricing not confirmed",
    focusTags: ["general", "academics"],
    highlights: [
      "Convenient local option for a 5-year-old.",
      "Published full-day and half-day structure gives some schedule choice.",
      "Estimated weekly cost looks moderate if 2026 pricing stayed close to the prior brochure."
    ],
    tradeoffs: [
      "Does not fit a 3-year-old.",
      "The report only had prior-year pricing, so tuition still needs confirmation."
    ],
    constraints: ["Only older child"],
    summary: "A workable local choice for kindergarten age, but not a one-camp answer for both children.",
    sources: [
      {
        label: "St. Charles brochure",
        url: "https://www.scbpschool.com/_files/ugd/148690_2e61c8d9c4b94583b2fe8ede7dea653c.pdf"
      }
    ]
  },
  {
    id: "footlighters",
    name: "Burlington County Footlighters Fledglings Theatre Camp",
    shortName: "Footlighters",
    location: "Cinnaminson, NJ",
    category: "Arts camp",
    driveMinutes: 4,
    distanceText: "Local",
    ageMin: 5,
    ageMax: 7,
    ageConfidence: "direct",
    ageText: "Fledglings program for ages 5-7",
    sessionText: "Two four-week sessions: Jun 22 - Jul 17, 2026 and Jul 27 - Aug 21, 2026",
    hoursText: "Camp day 9:00 AM - 3:00 PM; drop-off 8:30 AM and pickup by 3:30 PM",
    coreStart: 540,
    coreEnd: 900,
    earliestStart: 510,
    latestEnd: 930,
    extendedCare: false,
    pricingVisibility: "published",
    weeklyEstimate: 225,
    costText: "$900 per four-week session with sibling and multi-session discounts",
    focusTags: ["arts"],
    highlights: [
      "Strong low-cost option if your older child would love theater.",
      "Very close to home.",
      "Straightforward published pricing."
    ],
    tradeoffs: [
      "No fit for a 3-year-old.",
      "Shorter 9-to-3 day is harder if you need full workday coverage."
    ],
    constraints: ["Only older child"],
    summary: "Best if you want an arts-heavy option just for the 5-year-old.",
    sources: [{ label: "BC Footlighters", url: "https://www.bcfootlighters.com/summer-camp" }]
  },
  {
    id: "mount-laurel-ymca",
    name: "Mount Laurel YMCA Small Feet Summer Day Camp",
    shortName: "Mount Laurel YMCA",
    location: "Mount Laurel, NJ",
    category: "YMCA day camp",
    driveMinutes: 15,
    distanceText: "~9 miles",
    ageMin: 4,
    ageMax: 5,
    ageConfidence: "direct",
    ageText: "Small Feet program for ages 4-5; toilet trained",
    sessionText: "Weekly sessions from Jun 1 - Sep 4, 2026",
    hoursText: "7:00 AM - 6:00 PM including before and after care; swim transport included",
    coreStart: 420,
    coreEnd: 1080,
    earliestStart: 420,
    latestEnd: 1080,
    extendedCare: true,
    pricingVisibility: "published",
    weeklyEstimate: 335,
    costText: "$285/week for members or $335/week for non-members; early-bird discount available",
    focusTags: ["general", "sports"],
    highlights: [
      "Longest published coverage window in the report.",
      "Transparent weekly pricing and swim time built into the program.",
      "Strong value if you only need a camp for the older child."
    ],
    tradeoffs: [
      "Small Feet starts at age 4, so it does not cover a 3-year-old.",
      "Longer drive than the truly local options."
    ],
    constraints: ["Only older child", "Toilet trained"],
    summary: "A high-coverage value play for the 5-year-old, especially if workday hours matter.",
    sources: [
      {
        label: "Mount Laurel YMCA planner",
        url: "https://www.philaymca.org/sites/default/files/2026-01/Mount%20Laurel%20YMCA%20Summer%20Camp%20Planner%202026%20v2.pdf"
      }
    ]
  },
  {
    id: "riverton-ke-camps",
    name: "Riverton Country Club KE Camps",
    shortName: "Riverton KE Camps",
    location: "Cinnaminson, NJ",
    category: "Country club camp",
    driveMinutes: 5,
    distanceText: "In Cinnaminson",
    ageMin: 5,
    ageMax: 10,
    ageConfidence: "direct",
    ageText: "Ages 5-10; non-member children need member sponsorship",
    sessionText: "Four-week run from Jul 13 - Aug 7, 2026",
    hoursText: "Core hours 9:00 AM - 3:30 PM; drop-off 8:30 - 9:00 AM and pickup 3:30 - 4:00 PM",
    coreStart: 540,
    coreEnd: 930,
    earliestStart: 510,
    latestEnd: 960,
    extendedCare: false,
    pricingVisibility: "published",
    weeklyEstimate: 495,
    costText: "$465/week early member rate, $495/week standard, guest rate $540-$570, plus $45 registration fee",
    focusTags: ["general", "sports"],
    highlights: [
      "Close to home and easy to compare on price.",
      "Good fit for a 5-year-old who wants a more active camp setting.",
      "Pricing and dates are public."
    ],
    tradeoffs: [
      "Not available for a 3-year-old.",
      "Member sponsorship requirement adds friction for non-members."
    ],
    constraints: ["Only older child", "Member sponsorship"],
    summary: "Convenient for the older child, but access rules and age floor make it a split-camp option.",
    sources: [{ label: "KE Camps", url: "https://kecamps.com/camps/riverton-country-club" }]
  },
  {
    id: "red-balloon",
    name: "Red Balloon Preschool and Child Care Summer Camp",
    shortName: "Red Balloon",
    location: "Delran, NJ",
    category: "Preschool center",
    driveMinutes: 8,
    distanceText: "~3 miles",
    ageMin: 3,
    ageMax: 7,
    ageConfidence: "estimated",
    ageText: "Preschool through early elementary ages inferred from the center description",
    sessionText: "Operates through June, July, and August",
    hoursText: "7:30 AM - 6:00 PM",
    coreStart: 450,
    coreEnd: 1080,
    earliestStart: 450,
    latestEnd: 1080,
    extendedCare: true,
    pricingVisibility: "private",
    weeklyEstimate: null,
    costText: "Tuition not published on the public camp page",
    focusTags: ["general", "sports"],
    highlights: [
      "Long published day with pool, sports, and field trips.",
      "Very close to Cinnaminson.",
      "Likely one of the better fits if you want preschool-style care with camp activities."
    ],
    tradeoffs: [
      "Pricing is not public.",
      "The report did not find a precise published age window, so fit is inferred."
    ],
    constraints: ["Call for pricing"],
    summary: "Worth calling if long hours and close distance matter more than upfront tuition clarity.",
    sources: [{ label: "Red Balloon", url: "https://redballoonpreschool.com/summer-camp/" }]
  },
  {
    id: "cinnamon-sticks",
    name: "Cinnamon Sticks Learning Center Summer Program",
    shortName: "Cinnamon Sticks",
    location: "Cinnaminson, NJ",
    category: "Learning center",
    driveMinutes: 5,
    distanceText: "Local",
    ageMin: 3,
    ageMax: 6,
    ageConfidence: "estimated",
    ageText: "Preschool and kindergarten ages inferred from review listings",
    sessionText: "Dates not publicly posted in the source set",
    hoursText: "Daily hours not clearly published",
    coreStart: null,
    coreEnd: null,
    earliestStart: null,
    latestEnd: null,
    extendedCare: false,
    pricingVisibility: "estimated",
    weeklyEstimate: 250,
    costText: "Secondary source listed about $250/week, but official site details were unavailable",
    focusTags: ["general", "academics"],
    highlights: [
      "Local and potentially one of the cheaper programs in the report.",
      "Likely aligned with preschool and kindergarten children.",
      "Could be a practical fallback if you are comfortable confirming details manually."
    ],
    tradeoffs: [
      "Price comes from a review site rather than the camp itself.",
      "Dates and daily schedule need direct confirmation."
    ],
    constraints: ["Verify details directly"],
    summary: "Potential value option, but the report found too many missing official details to treat it as turnkey.",
    sources: [
      {
        label: "Private School Review profile",
        url: "https://www.privateschoolreview.com/cinnamon-sticks-learning-center-profile"
      }
    ]
  },
  {
    id: "kiddie-academy",
    name: "Kiddie Academy of Delran CampVentures",
    shortName: "Kiddie Academy",
    location: "Delran, NJ",
    category: "Child-care center",
    driveMinutes: 5,
    distanceText: "~2 miles",
    ageMin: 2,
    ageMax: 12,
    ageConfidence: "direct",
    ageText: "Ages 2-12",
    sessionText: "Operates during summer months",
    hoursText: "Full-day summer programs are offered, but the public page did not list exact daily hours",
    coreStart: null,
    coreEnd: null,
    earliestStart: null,
    latestEnd: null,
    extendedCare: false,
    pricingVisibility: "private",
    weeklyEstimate: null,
    costText: "Families must contact the center for tuition",
    focusTags: ["general", "stem"],
    highlights: [
      "Direct published age range covers both children easily.",
      "Very close to home.",
      "Program themes include STEM, nature exploration, and field trips."
    ],
    tradeoffs: [
      "No public pricing.",
      "The source set did not provide a full daily schedule."
    ],
    constraints: ["Call for pricing"],
    summary: "Strong age fit and close location, but you need direct outreach to finish the comparison.",
    sources: [
      {
        label: "Kiddie Academy",
        url: "https://kiddieacademy.com/academies/delran/programs/summer-camp/"
      }
    ]
  },
  {
    id: "newman-elc",
    name: "Newman Early Learning Center Summer Camp",
    shortName: "Newman ELC",
    location: "Cinnaminson, NJ",
    category: "Early learning center",
    driveMinutes: 5,
    distanceText: "Local",
    ageMin: 3,
    ageMax: 12,
    ageConfidence: "estimated",
    ageText: "Children up to age 12; younger fit inferred from preschool and child-care positioning",
    sessionText: "Camp runs in summer months, but dates were not listed in the report sources",
    hoursText: "Daily hours were not publicly listed",
    coreStart: null,
    coreEnd: null,
    earliestStart: null,
    latestEnd: null,
    extendedCare: false,
    pricingVisibility: "private",
    weeklyEstimate: null,
    costText: "Pricing not given publicly",
    focusTags: ["general"],
    highlights: [
      "Local and likely flexible for early-childhood care needs.",
      "Upper age cap suggests it can handle siblings in one place.",
      "Could work well if you want a child-care center rather than a themed camp."
    ],
    tradeoffs: [
      "Public details on dates, daily hours, and tuition are thin.",
      "Fit for a younger preschooler is inferred rather than explicitly published."
    ],
    constraints: ["Call for pricing"],
    summary: "A plausible one-site answer for both children, but the report lacked enough hard data to rank it confidently.",
    sources: [{ label: "Newman Early Learning Center", url: "https://www.newmanelc.com/aboutus" }]
  },
  {
    id: "esf-moorestown",
    name: "ESF Camps at William Allen Middle School",
    shortName: "ESF Camps",
    location: "Moorestown, NJ",
    category: "Premium day camp",
    driveMinutes: 10,
    distanceText: "~3.5 miles",
    ageMin: 3,
    ageMax: 6,
    ageConfidence: "direct",
    ageText: "Mini Division for rising preschool and pre-K; child must be age 3 by Jun 1 and potty trained",
    sessionText: "Sessions offered Jun 22 - Aug 21, 2026 with 2-9 week choices",
    hoursText: "Full day 9:00 AM - 3:00 PM or half day 9:00 AM - 1:00 PM; Club OT extended day 7:30 AM - 6:00 PM",
    coreStart: 540,
    coreEnd: 900,
    earliestStart: 450,
    latestEnd: 1080,
    extendedCare: true,
    pricingVisibility: "published",
    weeklyEstimate: 618,
    costText: "About $618/week early or $650/week standard for full day based on multi-week pricing; half day and Club OT sold separately",
    focusTags: ["general", "academics", "sports"],
    highlights: [
      "Direct fit for both children with strong schedule flexibility.",
      "Extensive public detail on tuition, schedule, and extended day.",
      "Good premium option if you want a polished camp experience."
    ],
    tradeoffs: [
      "Highest published tuition in the report.",
      "Requires potty training and is less budget-friendly than the local school options."
    ],
    constraints: ["Premium pricing", "Toilet trained"],
    summary: "One of the clearest apples-to-apples choices if you want both children in the same camp and can absorb the price.",
    sources: [
      { label: "ESF program page", url: "https://www.esfcamps.com/moorestown/programs/mini-camp/" },
      { label: "ESF rates", url: "https://www.esfcamps.com/moorestown/rates/" },
      { label: "ESF extended day", url: "https://www.esfcamps.com/moorestown/rates/extended-day/" }
    ]
  },
  {
    id: "apple-montessori",
    name: "Apple Montessori School Summer Camp",
    shortName: "Apple Montessori",
    location: "Mount Laurel, NJ",
    category: "Montessori camp",
    driveMinutes: 18,
    distanceText: "~10 miles",
    ageMin: 0,
    ageMax: 6,
    ageConfidence: "direct",
    ageText: "Ages 6 weeks - 6 years",
    sessionText: "Camp runs Jul 6 - Aug 28, 2026",
    hoursText: "7:00 AM - 6:30 PM with an academic day from 8:30 AM - 3:30 PM",
    coreStart: 510,
    coreEnd: 930,
    earliestStart: 420,
    latestEnd: 1110,
    extendedCare: true,
    pricingVisibility: "private",
    weeklyEstimate: null,
    costText: "Public pricing was not listed; families need to contact the school",
    focusTags: ["academics", "stem", "sports"],
    highlights: [
      "Direct fit for both children with the longest late pickup in the report.",
      "Montessori-style programming plus swimming, music, and robotics.",
      "Good option if you want an enriched early-childhood environment rather than a basic day camp."
    ],
    tradeoffs: [
      "Tuition is not public.",
      "Drive is near the upper bound of the report's 20-minute range."
    ],
    constraints: ["Call for pricing"],
    summary: "A strong one-camp contender for both children if you value long hours and enrichment and are willing to call for tuition.",
    sources: [
      { label: "Apple Montessori location", url: "https://applemontessorischools.com/locations/mt-laurel" },
      { label: "Apple Montessori summer camp", url: "https://applemontessorischools.com/programs/summer-camp" }
    ]
  },
  {
    id: "life-time",
    name: "Life Time Kids Summer Camp",
    shortName: "Life Time",
    location: "Mount Laurel, NJ",
    category: "Fitness club camp",
    driveMinutes: 20,
    distanceText: "~12 miles",
    ageMin: 4,
    ageMax: 13,
    ageConfidence: "direct",
    ageText: "Junior Camp for ages 4-5 and main camp for ages 6-13",
    sessionText: "Registration for 2026 opened Jan 1-Feb 1 depending on membership tier",
    hoursText: "Core schedule 9:00 AM - 4:00 PM with optional care from 7:00 AM - 6:00 PM",
    coreStart: 540,
    coreEnd: 960,
    earliestStart: 420,
    latestEnd: 1080,
    extendedCare: true,
    pricingVisibility: "private",
    weeklyEstimate: null,
    costText: "Pricing not disclosed publicly",
    focusTags: ["sports", "arts"],
    highlights: [
      "Long workday-friendly hours.",
      "Strong sports and swim orientation for active kids.",
      "A direct fit for the older child and for younger children age 4-5."
    ],
    tradeoffs: [
      "Does not fit a 3-year-old.",
      "Membership structure and private pricing make it harder to compare cleanly."
    ],
    constraints: ["Only older child", "Membership friction"],
    summary: "Useful only if you are comfortable splitting care or your younger child will be older by summer.",
    sources: [
      {
        label: "Life Time Mount Laurel",
        url: "https://my.lifetime.life/clubs/nj/mount-laurel/programs/kids/camps/summer-camps.html"
      }
    ]
  },
  {
    id: "lightbridge",
    name: "Lightbridge Academy Summer Camp",
    shortName: "Lightbridge Academy",
    location: "Mount Laurel, NJ",
    category: "Early childhood academy",
    driveMinutes: 18,
    distanceText: "~11 miles",
    ageMin: 3,
    ageMax: 8,
    ageConfidence: "estimated",
    ageText: "Likely early-childhood through lower elementary ages based on the program description",
    sessionText: "Summer camp with flexible weekly themes",
    hoursText: "Flexible schedule with extended hours and meal plans",
    coreStart: null,
    coreEnd: null,
    earliestStart: 450,
    latestEnd: 1080,
    extendedCare: true,
    pricingVisibility: "private",
    weeklyEstimate: null,
    costText: "Pricing not available publicly",
    focusTags: ["general", "arts", "stem"],
    highlights: [
      "Flexible scheduling plus extended hours.",
      "Themes include science experiments, arts, water play, and field trips.",
      "Promising one-camp fit if you are comfortable confirming details directly."
    ],
    tradeoffs: [
      "Pricing is private.",
      "Exact age range and exact clock times were not fully published in the report sources."
    ],
    constraints: ["Call for pricing"],
    summary: "A good prospect for flexible early-childhood coverage, but not one of the fully transparent options.",
    sources: [
      {
        label: "Lightbridge Academy",
        url: "https://lightbridgeacademy.com/mount-laurel-nj/programs/summer-camp/"
      }
    ]
  },
  {
    id: "creme-de-la-creme",
    name: "Creme de la Creme Summer Camp",
    shortName: "Creme de la Creme",
    location: "Mount Laurel, NJ",
    category: "Private academy camp",
    driveMinutes: 18,
    distanceText: "~11 miles",
    ageMin: 4,
    ageMax: 12,
    ageConfidence: "direct",
    ageText: "Junior camp for 4-year-olds and separate camps for older children",
    sessionText: "Dates and daily hours were not published publicly",
    hoursText: "Schedule not publicly posted in the source set",
    coreStart: null,
    coreEnd: null,
    earliestStart: null,
    latestEnd: null,
    extendedCare: false,
    pricingVisibility: "private",
    weeklyEstimate: null,
    costText: "Families must contact the center for tuition",
    focusTags: ["general", "sports"],
    highlights: [
      "Programing is explicitly built for younger campers starting at age 4.",
      "Activities include water play, sports, and field trips.",
      "Could suit a 5-year-old who wants a broad activity mix."
    ],
    tradeoffs: [
      "No fit for a 3-year-old.",
      "Pricing and schedule transparency are low."
    ],
    constraints: ["Only older child", "Call for pricing"],
    summary: "Another split-camp candidate for the older child, but not a one-stop choice for both kids.",
    sources: [{ label: "Creme de la Creme", url: "https://cremedelacreme.com/summer-camp/" }]
  }
];

const PRIORITY_WEIGHTS = {
  balanced: { age: 38, distance: 14, coverage: 16, budget: 14, pricing: 8, focus: 10 },
  budget: { age: 34, distance: 10, coverage: 10, budget: 28, pricing: 12, focus: 6 },
  coverage: { age: 34, distance: 10, coverage: 26, budget: 10, pricing: 10, focus: 10 },
  transparency: { age: 34, distance: 10, coverage: 12, budget: 10, pricing: 24, focus: 10 },
  enrichment: { age: 30, distance: 10, coverage: 12, budget: 8, pricing: 5, focus: 35 }
};

const VISIBILITY_SCORE = {
  published: 1,
  estimated: 0.72,
  private: 0.35
};

const DEFAULT_STATE = {
  childAgeOne: 3,
  childAgeTwo: 5,
  maxDrive: 20,
  weeklyBudget: "ignore",
  requireAllKids: true,
  needExtendedCare: false,
  needPublicPricing: false,
  priority: "balanced",
  focus: "any",
  sortMode: "fit"
};

const state = {
  ...DEFAULT_STATE,
  selectedIds: new Set()
};

const dom = {};

function formatCurrency(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "Ask camp";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  }).format(value);
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function getActiveAges() {
  return [Number(state.childAgeOne), Number(state.childAgeTwo)];
}

function getEligibility(age, camp) {
  if (age < camp.ageMin || age > camp.ageMax) {
    return { label: "No fit", value: 0 };
  }
  if (camp.ageConfidence === "direct") {
    return { label: "Direct fit", value: 1 };
  }
  return { label: "Likely fit", value: 0.82 };
}

function getAgeBreakdown(camp, ages) {
  const results = ages.map((age) => ({ age, ...getEligibility(age, camp) }));
  const coveredCount = results.filter((item) => item.value >= 0.8).length;
  const directCount = results.filter((item) => item.label === "Direct fit").length;
  const allKids = coveredCount === ages.length;
  const anyKids = coveredCount > 0;

  let badge = "Outside current ages";
  if (allKids && directCount === ages.length) badge = "Fits every child";
  else if (allKids) badge = "Likely fits every child";
  else if (anyKids) badge = "Only fits part of the family";

  let score = 0;
  if (allKids) {
    score = results.reduce((sum, item) => sum + item.value, 0) / results.length;
  } else if (anyKids) {
    score = (results.reduce((sum, item) => sum + item.value, 0) / results.length) * 0.52;
  }

  return { results, coveredCount, allKids, anyKids, badge, score };
}

function getDistanceScore(camp) {
  if (camp.driveMinutes <= state.maxDrive) return 1;
  if (camp.driveMinutes <= state.maxDrive + 5) return 0.55;
  return 0.15;
}

function getCoverageScore(camp) {
  if (!state.needExtendedCare) {
    if (camp.coreStart !== null && camp.coreEnd !== null) {
      const durationHours = (camp.coreEnd - camp.coreStart) / 60;
      if (durationHours >= 7.5) return 1;
      if (durationHours >= 6) return 0.85;
      return 0.55;
    }
    if (camp.latestEnd !== null && camp.earliestStart !== null) {
      const durationHours = (camp.latestEnd - camp.earliestStart) / 60;
      if (durationHours >= 8) return 0.9;
    }
    return 0.62;
  }

  if (camp.extendedCare && camp.latestEnd !== null && camp.latestEnd >= 1050) return 1;
  if (camp.latestEnd !== null && camp.latestEnd >= 1020) return 0.82;
  if (camp.latestEnd === null) return 0.42;
  return 0.2;
}

function getBudgetScore(camp) {
  if (state.weeklyBudget === "ignore") {
    return camp.weeklyEstimate !== null ? 0.85 : 0.6;
  }

  const target = Number(state.weeklyBudget);
  if (camp.weeklyEstimate === null) return 0.28;
  if (camp.weeklyEstimate <= target) return 1;
  if (camp.weeklyEstimate <= target * 1.1) return 0.82;
  if (camp.weeklyEstimate <= target * 1.25) return 0.58;
  return 0.18;
}

function getPricingScore(camp) {
  return VISIBILITY_SCORE[camp.pricingVisibility];
}

function getFocusScore(camp) {
  if (state.focus === "any") return 0.8;
  return camp.focusTags.includes(state.focus) ? 1 : 0.38;
}

function getReasons(camp, ageBreakdown) {
  const reasons = [];
  const cautions = [];

  if (ageBreakdown.allKids) reasons.push(ageBreakdown.badge);
  else if (ageBreakdown.anyKids) cautions.push("Does not cover every child you entered.");
  else cautions.push("Outside the current age range.");

  if (camp.driveMinutes <= 10) reasons.push(`Short drive: ${camp.distanceText} (${camp.driveMinutes} min estimate).`);
  else cautions.push(`${camp.driveMinutes} minute drive may feel long for daily drop-off.`);

  if (camp.extendedCare && camp.latestEnd !== null && camp.latestEnd >= 1050) {
    reasons.push("Workday-friendly coverage with late pickup.");
  } else if (state.needExtendedCare) {
    cautions.push("Schedule is weaker for long workday coverage.");
  }

  if (camp.pricingVisibility === "published") reasons.push("Pricing is public and easy to compare.");
  else if (camp.pricingVisibility === "estimated") cautions.push("Pricing is only estimated from prior or secondary sources.");
  else cautions.push("Tuition requires a direct inquiry.");

  if (state.weeklyBudget !== "ignore" && camp.weeklyEstimate !== null) {
    if (camp.weeklyEstimate <= Number(state.weeklyBudget)) {
      reasons.push(`Published weekly cost lands inside your target (${formatCurrency(camp.weeklyEstimate)}).`);
    } else {
      cautions.push(`Published weekly cost is above your target (${formatCurrency(camp.weeklyEstimate)}).`);
    }
  }

  if (state.focus !== "any") {
    if (camp.focusTags.includes(state.focus)) reasons.push(`Program style matches your "${state.focus}" preference.`);
    else cautions.push(`Program flavor is not a clean match for "${state.focus}".`);
  }

  if (reasons.length < 2) reasons.push(...camp.highlights.slice(0, 2 - reasons.length));
  if (cautions.length < 2) cautions.push(...camp.tradeoffs.slice(0, 2 - cautions.length));

  return { reasons: reasons.slice(0, 3), cautions: cautions.slice(0, 3) };
}

function evaluateCamp(camp) {
  const weights = PRIORITY_WEIGHTS[state.priority];
  const ages = getActiveAges();
  const ageBreakdown = getAgeBreakdown(camp, ages);

  if (state.requireAllKids && !ageBreakdown.allKids) return { camp, ageBreakdown, visible: false };
  if (state.needPublicPricing && camp.pricingVisibility === "private") return { camp, ageBreakdown, visible: false };
  if (camp.driveMinutes > state.maxDrive) return { camp, ageBreakdown, visible: false };

  const components = {
    age: ageBreakdown.score,
    distance: getDistanceScore(camp),
    coverage: getCoverageScore(camp),
    budget: getBudgetScore(camp),
    pricing: getPricingScore(camp),
    focus: getFocusScore(camp)
  };

  const score = Math.round(
    weights.age * components.age +
      weights.distance * components.distance +
      weights.coverage * components.coverage +
      weights.budget * components.budget +
      weights.pricing * components.pricing +
      weights.focus * components.focus
  );

  return { camp, ageBreakdown, components, score, visible: true, ...getReasons(camp, ageBreakdown) };
}

function sortEvaluations(items) {
  const sorted = [...items];
  sorted.sort((left, right) => {
    if (state.sortMode === "cost") {
      const leftCost = left.camp.weeklyEstimate ?? Number.POSITIVE_INFINITY;
      const rightCost = right.camp.weeklyEstimate ?? Number.POSITIVE_INFINITY;
      return leftCost - rightCost || right.score - left.score;
    }
    if (state.sortMode === "distance") {
      return left.camp.driveMinutes - right.camp.driveMinutes || right.score - left.score;
    }
    if (state.sortMode === "coverage") {
      const leftCoverage = left.camp.latestEnd ?? left.camp.coreEnd ?? 0;
      const rightCoverage = right.camp.latestEnd ?? right.camp.coreEnd ?? 0;
      return rightCoverage - leftCoverage || right.score - left.score;
    }
    if (state.sortMode === "pricing") {
      return getPricingScore(right.camp) - getPricingScore(left.camp) || right.score - left.score;
    }
    return right.score - left.score || left.camp.driveMinutes - right.camp.driveMinutes;
  });
  return sorted;
}

function getEvaluations() {
  return sortEvaluations(CAMPS.map(evaluateCamp).filter((item) => item.visible));
}

function getLatePickupCount(items) {
  return items.filter((item) => (item.camp.latestEnd ?? 0) >= 1050).length;
}

function renderSummary(items) {
  const allKidsCount = items.filter((item) => item.ageBreakdown.allKids).length;
  const publishedPricingCount = items.filter((item) => item.camp.pricingVisibility !== "private").length;

  dom.statVisible.textContent = String(items.length);
  dom.statAllKids.textContent = String(allKidsCount);
  dom.statPricing.textContent = String(publishedPricingCount);
  dom.statLatePickup.textContent = String(getLatePickupCount(items));

  if (!items.length) {
    dom.resultsSummary.textContent = "No camps match the current hard filters. Try relaxing drive, pricing, or age requirements.";
    return;
  }

  dom.resultsSummary.textContent = `${items.length} camps match your filters. Current top pick: ${items[0].camp.shortName} at ${items[0].score}/100.`;
}

function renderInsights(items) {
  if (!items.length) {
    dom.insightGrid.innerHTML = "";
    return;
  }

  const top = items[0];
  const valuePick = [...items]
    .filter((item) => item.camp.weeklyEstimate !== null)
    .sort((left, right) => left.camp.weeklyEstimate - right.camp.weeklyEstimate)[0];
  const coveragePick = [...items].sort((left, right) => {
    const leftCoverage = left.camp.latestEnd ?? left.camp.coreEnd ?? 0;
    const rightCoverage = right.camp.latestEnd ?? right.camp.coreEnd ?? 0;
    return rightCoverage - leftCoverage;
  })[0];

  const insightCards = [
    { kicker: "Best overall", title: top.camp.shortName, text: top.reasons[0] || top.camp.summary },
    {
      kicker: "Best value",
      title: valuePick ? `${valuePick.camp.shortName} (${formatCurrency(valuePick.camp.weeklyEstimate)})` : "No priced match",
      text: valuePick ? valuePick.camp.costText : "Every visible option currently needs a direct pricing inquiry."
    },
    { kicker: "Best coverage", title: coveragePick.camp.shortName, text: coveragePick.camp.hoursText }
  ];

  dom.insightGrid.innerHTML = insightCards
    .map(
      (insight, index) => `
        <article class="panel insight-card" style="animation-delay:${index * 70}ms">
          <span class="insight-kicker">${escapeHtml(insight.kicker)}</span>
          <h3>${escapeHtml(insight.title)}</h3>
          <p>${escapeHtml(insight.text)}</p>
        </article>
      `
    )
    .join("");
}

function renderResults(items) {
  if (!items.length) {
    dom.results.innerHTML = `
      <article class="panel empty-state">
        <h3>No camps in play</h3>
        <p>Relax one of the hard filters above and the ranked list will repopulate.</p>
      </article>
    `;
    return;
  }

  dom.results.innerHTML = items
    .map((item, index) => {
      const { camp, ageBreakdown, score, reasons, cautions } = item;
      const selected = state.selectedIds.has(camp.id);
      const pills = [
        `<span class="pill">${escapeHtml(ageBreakdown.badge)}</span>`,
        camp.extendedCare ? '<span class="pill soft">Extended day</span>' : "",
        camp.pricingVisibility === "published"
          ? '<span class="pill soft">Public pricing</span>'
          : camp.pricingVisibility === "estimated"
          ? '<span class="pill warn">Estimated pricing</span>'
          : '<span class="pill warn">Call for pricing</span>',
        camp.constraints.includes("Member sponsorship") || camp.constraints.includes("Membership friction")
          ? '<span class="pill warn">Membership friction</span>'
          : ""
      ]
        .filter(Boolean)
        .join("");

      const sources = camp.sources
        .map(
          (source) =>
            `<a class="source-link" href="${escapeHtml(source.url)}" target="_blank" rel="noreferrer noopener">${escapeHtml(source.label)}</a>`
        )
        .join("");

      return `
        <article class="panel camp-card" style="animation-delay:${index * 45}ms">
          <div class="camp-top">
            <div>
              <p class="eyebrow">${escapeHtml(camp.category)}</p>
              <h3>${escapeHtml(camp.name)}</h3>
              <div class="camp-meta">
                <span>${escapeHtml(camp.location)}</span>
                <span>•</span>
                <span>${escapeHtml(camp.distanceText)} / ${camp.driveMinutes} min</span>
              </div>
            </div>
            <div class="score-badge">
              <div>
                <strong>${score}</strong>
                <span>Fit score</span>
              </div>
            </div>
          </div>

          <div class="pill-row">${pills}</div>
          <p class="camp-summary">${escapeHtml(camp.summary)}</p>

          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">Age window</span>
              <span class="detail-value">${escapeHtml(camp.ageText)}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Tuition snapshot</span>
              <span class="detail-value">${escapeHtml(camp.costText)}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Session timing</span>
              <span class="detail-value">${escapeHtml(camp.sessionText)}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Daily schedule</span>
              <span class="detail-value">${escapeHtml(camp.hoursText)}</span>
            </div>
          </div>

          <div class="reason-block">
            <div>
              <p class="label">Why it rises</p>
              <ul class="reason-list">
                ${reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}
              </ul>
            </div>
            <div>
              <p class="label">Watch-outs</p>
              <ul class="reason-list">
                ${cautions.map((caution) => `<li>${escapeHtml(caution)}</li>`).join("")}
              </ul>
            </div>
          </div>

          <div class="action-row">
            <button type="button" class="compare-toggle ${selected ? "is-selected" : ""}" data-compare-id="${escapeHtml(
              camp.id
            )}">
              ${selected ? "Remove from compare" : "Add to compare"}
            </button>
            <div class="source-row">${sources}</div>
          </div>
        </article>
      `;
    })
    .join("");
}

function getSelectedItems(items) {
  return items.filter((item) => state.selectedIds.has(item.camp.id)).slice(0, 3);
}

function renderComparison(items) {
  const selected = getSelectedItems(items);

  if (!selected.length) {
    dom.comparisonPanel.classList.add("is-hidden");
    dom.comparisonPanel.innerHTML = "";
    return;
  }

  dom.comparisonPanel.classList.remove("is-hidden");
  dom.comparisonPanel.innerHTML = `
    <div class="comparison-head">
      <div>
        <p class="eyebrow">Side-by-side</p>
        <h2>Compare your shortlist</h2>
      </div>
      <button id="clearCompareButton" type="button" class="button ghost compact">Clear compare</button>
    </div>
    <div class="comparison-table-wrap">
      <table class="comparison-table">
        <thead>
          <tr>
            <th scope="col">Attribute</th>
            ${selected.map((item) => `<th scope="col">${escapeHtml(item.camp.shortName)}</th>`).join("")}
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">Fit score</th>
            ${selected.map((item) => `<td>${item.score}/100</td>`).join("")}
          </tr>
          <tr>
            <th scope="row">Family fit</th>
            ${selected.map((item) => `<td>${escapeHtml(item.ageBreakdown.badge)}</td>`).join("")}
          </tr>
          <tr>
            <th scope="row">Age window</th>
            ${selected.map((item) => `<td>${escapeHtml(item.camp.ageText)}</td>`).join("")}
          </tr>
          <tr>
            <th scope="row">Schedule</th>
            ${selected.map((item) => `<td>${escapeHtml(item.camp.hoursText)}</td>`).join("")}
          </tr>
          <tr>
            <th scope="row">Tuition</th>
            ${selected.map((item) => `<td>${escapeHtml(item.camp.costText)}</td>`).join("")}
          </tr>
          <tr>
            <th scope="row">Best reasons</th>
            ${selected
              .map(
                (item) =>
                  `<td><ul class="reason-list">${item.reasons
                    .map((reason) => `<li>${escapeHtml(reason)}</li>`)
                    .join("")}</ul></td>`
              )
              .join("")}
          </tr>
          <tr>
            <th scope="row">Main watch-outs</th>
            ${selected
              .map(
                (item) =>
                  `<td><ul class="reason-list">${item.cautions
                    .map((caution) => `<li>${escapeHtml(caution)}</li>`)
                    .join("")}</ul></td>`
              )
              .join("")}
          </tr>
        </tbody>
      </table>
    </div>
  `;
}

function copySummary(items) {
  if (!items.length) return;

  const lines = [
    "Summer camp shortlist",
    `Filters: ages ${state.childAgeOne} and ${state.childAgeTwo}, max drive ${state.maxDrive} min, priority ${state.priority}.`,
    ""
  ];

  items.slice(0, 3).forEach((item, index) => {
    lines.push(`${index + 1}. ${item.camp.name} - ${item.score}/100`);
    lines.push(`   Why it stands out: ${item.reasons.join(" ")}`);
    lines.push(`   Watch-outs: ${item.cautions.join(" ")}`);
    lines.push(`   Tuition snapshot: ${item.camp.costText}`);
    lines.push("");
  });

  const textarea = document.createElement("textarea");
  textarea.value = lines.join("\n").trim();
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  textarea.remove();

  dom.copySummaryButton.textContent = "Summary copied";
  window.setTimeout(() => {
    dom.copySummaryButton.textContent = "Copy shortlist summary";
  }, 1800);
}

function syncControlValues() {
  dom.childAgeOne.value = String(state.childAgeOne);
  dom.childAgeTwo.value = String(state.childAgeTwo);
  dom.maxDrive.value = String(state.maxDrive);
  dom.weeklyBudget.value = state.weeklyBudget;
  dom.requireAllKids.checked = state.requireAllKids;
  dom.needExtendedCare.checked = state.needExtendedCare;
  dom.needPublicPricing.checked = state.needPublicPricing;
  dom.sortMode.value = state.sortMode;

  dom.priorityPreset.querySelectorAll("[data-priority]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.priority === state.priority);
  });

  dom.focusPreset.querySelectorAll("[data-focus]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.focus === state.focus);
  });
}

function render() {
  syncControlValues();
  const evaluations = getEvaluations();
  renderSummary(evaluations);
  renderInsights(evaluations);
  renderComparison(evaluations);
  renderResults(evaluations);
  dom.copySummaryButton.disabled = evaluations.length === 0;
}

function toggleCompare(id) {
  if (state.selectedIds.has(id)) {
    state.selectedIds.delete(id);
    return;
  }
  if (state.selectedIds.size >= 3) {
    const first = state.selectedIds.values().next().value;
    state.selectedIds.delete(first);
  }
  state.selectedIds.add(id);
}

function attachEvents() {
  dom.decisionForm.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement || target instanceof HTMLSelectElement)) return;

    if (target.id === "childAgeOne") state.childAgeOne = Number(target.value);
    if (target.id === "childAgeTwo") state.childAgeTwo = Number(target.value);
    if (target.id === "maxDrive") state.maxDrive = Number(target.value);
    if (target.id === "weeklyBudget") state.weeklyBudget = target.value;
    if (target.id === "requireAllKids") state.requireAllKids = target.checked;
    if (target.id === "needExtendedCare") state.needExtendedCare = target.checked;
    if (target.id === "needPublicPricing") state.needPublicPricing = target.checked;
    render();
  });

  dom.sortMode.addEventListener("change", (event) => {
    state.sortMode = event.target.value;
    render();
  });

  dom.priorityPreset.addEventListener("click", (event) => {
    const button = event.target.closest("[data-priority]");
    if (!button) return;
    state.priority = button.dataset.priority;
    render();
  });

  dom.focusPreset.addEventListener("click", (event) => {
    const button = event.target.closest("[data-focus]");
    if (!button) return;
    state.focus = button.dataset.focus;
    render();
  });

  dom.results.addEventListener("click", (event) => {
    const button = event.target.closest("[data-compare-id]");
    if (!button) return;
    toggleCompare(button.dataset.compareId);
    render();
  });

  dom.comparisonPanel.addEventListener("click", (event) => {
    if (event.target.closest("#clearCompareButton")) {
      state.selectedIds.clear();
      render();
    }
  });

  dom.copySummaryButton.addEventListener("click", () => {
    copySummary(getEvaluations());
  });

  dom.resetButton.addEventListener("click", () => {
    Object.assign(state, DEFAULT_STATE);
    state.selectedIds.clear();
    render();
  });
}

function init() {
  dom.decisionForm = document.getElementById("decisionForm");
  dom.childAgeOne = document.getElementById("childAgeOne");
  dom.childAgeTwo = document.getElementById("childAgeTwo");
  dom.maxDrive = document.getElementById("maxDrive");
  dom.weeklyBudget = document.getElementById("weeklyBudget");
  dom.requireAllKids = document.getElementById("requireAllKids");
  dom.needExtendedCare = document.getElementById("needExtendedCare");
  dom.needPublicPricing = document.getElementById("needPublicPricing");
  dom.priorityPreset = document.getElementById("priorityPreset");
  dom.focusPreset = document.getElementById("focusPreset");
  dom.sortMode = document.getElementById("sortMode");
  dom.results = document.getElementById("results");
  dom.resultsSummary = document.getElementById("resultsSummary");
  dom.statVisible = document.getElementById("statVisible");
  dom.statAllKids = document.getElementById("statAllKids");
  dom.statPricing = document.getElementById("statPricing");
  dom.statLatePickup = document.getElementById("statLatePickup");
  dom.insightGrid = document.getElementById("insightGrid");
  dom.comparisonPanel = document.getElementById("comparisonPanel");
  dom.copySummaryButton = document.getElementById("copySummaryButton");
  dom.resetButton = document.getElementById("resetButton");

  attachEvents();
  render();
}

document.addEventListener("DOMContentLoaded", init);
