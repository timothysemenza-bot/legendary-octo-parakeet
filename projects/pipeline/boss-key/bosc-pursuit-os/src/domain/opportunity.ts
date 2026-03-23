import { z } from "zod";

export const SERVICE_TYPES = [
  "nightly-cleaning",
  "day-porter",
  "floor-care",
  "daytime-support",
  "consumables-management",
  "window-touchpoint",
] as const;

export const RELATIONSHIP_STRENGTHS = ["low", "medium", "high"] as const;
export const STRATEGIC_FIT_LEVELS = ["low", "medium", "high"] as const;
export const PRICING_PRESSURE_LEVELS = ["low", "medium", "high"] as const;

export type ServiceType = (typeof SERVICE_TYPES)[number];
export type RelationshipStrength = (typeof RELATIONSHIP_STRENGTHS)[number];
export type StrategicFit = (typeof STRATEGIC_FIT_LEVELS)[number];
export type PricingPressure = (typeof PRICING_PRESSURE_LEVELS)[number];

export const serviceTypeLabels: Record<ServiceType, string> = {
  "nightly-cleaning": "Nightly Cleaning",
  "day-porter": "Day Porter",
  "floor-care": "Floor Care",
  "daytime-support": "Daytime Support",
  "consumables-management": "Consumables Management",
  "window-touchpoint": "Window and Touchpoint Care",
};

const serviceTypeSchema = z.enum(SERVICE_TYPES);
const relationshipStrengthSchema = z.enum(RELATIONSHIP_STRENGTHS);
const strategicFitSchema = z.enum(STRATEGIC_FIT_LEVELS);
const pricingPressureSchema = z.enum(PRICING_PRESSURE_LEVELS);

export const opportunitySchema = z.object({
  id: z.string().min(1),
  opportunityName: z.string().min(1),
  buyerName: z.string().min(1),
  sector: z.enum([
    "Class A Office",
    "Medical Office",
    "Mixed Commercial",
    "Industrial Support",
  ]),
  geography: z.object({
    region: z.string().min(1),
    city: z.string().min(1),
    state: z.string().length(2),
    inPreferredRegion: z.boolean(),
  }),
  siteProfile: z.object({
    siteCount: z.number().int().positive(),
    totalSquareFeet: z.number().positive(),
    occupiedHours: z.string().min(1),
    weekendCoverageRequired: z.boolean(),
    dayPorterRequired: z.boolean(),
    unionEnvironment: z.boolean(),
  }),
  contract: z.object({
    annualValueEstimate: z.number().positive(),
    termMonths: z.number().int().positive(),
    targetGrossMarginPercent: z.number().min(0).max(100),
    transitionDays: z.number().int().positive(),
    startDate: z.string().min(1),
  }),
  requirements: z.object({
    requiredServices: z.array(serviceTypeSchema).min(1),
    reportingCadence: z.string().min(1),
    sustainabilityExpectation: z.boolean(),
    selfPerformedPreference: z.boolean(),
    referencesRequired: z.number().int().min(0),
  }),
  pursuitContext: z.object({
    incumbentPresent: z.boolean(),
    relationshipStrength: relationshipStrengthSchema,
    strategicFit: strategicFitSchema,
    pricingPressure: pricingPressureSchema,
    proofPriority: z.array(z.string().min(1)).min(1),
    notes: z.array(z.string().min(1)).min(1),
  }),
});

export type Opportunity = z.infer<typeof opportunitySchema>;

export function parseOpportunity(input: unknown): Opportunity {
  return opportunitySchema.parse(input);
}

export function formatOpportunityValidationError(input: unknown): string | null {
  const result = opportunitySchema.safeParse(input);
  if (result.success) {
    return null;
  }

  return result.error.issues
    .map((issue) => `${issue.path.join(".") || "root"}: ${issue.message}`)
    .join("; ");
}

