import {
  PRICING_PRESSURE_LEVELS,
  RELATIONSHIP_STRENGTHS,
  SERVICE_TYPES,
  STRATEGIC_FIT_LEVELS,
  serviceTypeLabels,
  type Opportunity,
  type ServiceType,
} from "../../domain/opportunity";

interface OpportunityFieldsFormProps {
  opportunity: Opportunity;
  onOpportunityChange: (nextOpportunity: Opportunity) => void;
}

function parseNumber(value: string, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function OpportunityFieldsForm({
  opportunity,
  onOpportunityChange,
}: OpportunityFieldsFormProps) {
  function updateService(service: ServiceType) {
    const current = opportunity.requirements.requiredServices;
    const nextServices = current.includes(service)
      ? current.filter((item) => item !== service)
      : [...current, service];

    if (nextServices.length === 0) {
      return;
    }

    onOpportunityChange({
      ...opportunity,
      requirements: {
        ...opportunity.requirements,
        requiredServices: nextServices,
      },
    });
  }

  return (
    <>
      <div className="form-grid">
        <label className="field">
          <span>Opportunity name</span>
          <input
            type="text"
            value={opportunity.opportunityName}
            onChange={(event) =>
              onOpportunityChange({
                ...opportunity,
                opportunityName: event.target.value,
              })
            }
          />
        </label>

        <label className="field">
          <span>Buyer</span>
          <input
            type="text"
            value={opportunity.buyerName}
            onChange={(event) =>
              onOpportunityChange({
                ...opportunity,
                buyerName: event.target.value,
              })
            }
          />
        </label>

        <label className="field">
          <span>Sites</span>
          <input
            type="number"
            min="1"
            value={opportunity.siteProfile.siteCount}
            onChange={(event) =>
              onOpportunityChange({
                ...opportunity,
                siteProfile: {
                  ...opportunity.siteProfile,
                  siteCount: parseNumber(
                    event.target.value,
                    opportunity.siteProfile.siteCount,
                  ),
                },
              })
            }
          />
        </label>

        <label className="field">
          <span>Total square feet</span>
          <input
            type="number"
            min="1000"
            step="1000"
            value={opportunity.siteProfile.totalSquareFeet}
            onChange={(event) =>
              onOpportunityChange({
                ...opportunity,
                siteProfile: {
                  ...opportunity.siteProfile,
                  totalSquareFeet: parseNumber(
                    event.target.value,
                    opportunity.siteProfile.totalSquareFeet,
                  ),
                },
              })
            }
          />
        </label>

        <label className="field">
          <span>Annual value estimate</span>
          <input
            type="number"
            min="10000"
            step="10000"
            value={opportunity.contract.annualValueEstimate}
            onChange={(event) =>
              onOpportunityChange({
                ...opportunity,
                contract: {
                  ...opportunity.contract,
                  annualValueEstimate: parseNumber(
                    event.target.value,
                    opportunity.contract.annualValueEstimate,
                  ),
                },
              })
            }
          />
        </label>

        <label className="field">
          <span>Target gross margin %</span>
          <input
            type="number"
            min="0"
            max="100"
            value={opportunity.contract.targetGrossMarginPercent}
            onChange={(event) =>
              onOpportunityChange({
                ...opportunity,
                contract: {
                  ...opportunity.contract,
                  targetGrossMarginPercent: parseNumber(
                    event.target.value,
                    opportunity.contract.targetGrossMarginPercent,
                  ),
                },
              })
            }
          />
        </label>

        <label className="field">
          <span>Transition days</span>
          <input
            type="number"
            min="1"
            value={opportunity.contract.transitionDays}
            onChange={(event) =>
              onOpportunityChange({
                ...opportunity,
                contract: {
                  ...opportunity.contract,
                  transitionDays: parseNumber(
                    event.target.value,
                    opportunity.contract.transitionDays,
                  ),
                },
              })
            }
          />
        </label>

        <label className="field">
          <span>Strategic fit</span>
          <select
            value={opportunity.pursuitContext.strategicFit}
            onChange={(event) =>
              onOpportunityChange({
                ...opportunity,
                pursuitContext: {
                  ...opportunity.pursuitContext,
                  strategicFit:
                    event.target.value as Opportunity["pursuitContext"]["strategicFit"],
                },
              })
            }
          >
            {STRATEGIC_FIT_LEVELS.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Relationship strength</span>
          <select
            value={opportunity.pursuitContext.relationshipStrength}
            onChange={(event) =>
              onOpportunityChange({
                ...opportunity,
                pursuitContext: {
                  ...opportunity.pursuitContext,
                  relationshipStrength:
                    event.target.value as Opportunity["pursuitContext"]["relationshipStrength"],
                },
              })
            }
          >
            {RELATIONSHIP_STRENGTHS.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Pricing pressure</span>
          <select
            value={opportunity.pursuitContext.pricingPressure}
            onChange={(event) =>
              onOpportunityChange({
                ...opportunity,
                pursuitContext: {
                  ...opportunity.pursuitContext,
                  pricingPressure:
                    event.target.value as Opportunity["pursuitContext"]["pricingPressure"],
                },
              })
            }
          >
            {PRICING_PRESSURE_LEVELS.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </label>

        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={opportunity.siteProfile.dayPorterRequired}
            onChange={(event) =>
              onOpportunityChange({
                ...opportunity,
                siteProfile: {
                  ...opportunity.siteProfile,
                  dayPorterRequired: event.target.checked,
                },
              })
            }
          />
          <span>Day porter required</span>
        </label>

        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={opportunity.siteProfile.weekendCoverageRequired}
            onChange={(event) =>
              onOpportunityChange({
                ...opportunity,
                siteProfile: {
                  ...opportunity.siteProfile,
                  weekendCoverageRequired: event.target.checked,
                },
              })
            }
          />
          <span>Weekend coverage required</span>
        </label>

        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={opportunity.requirements.sustainabilityExpectation}
            onChange={(event) =>
              onOpportunityChange({
                ...opportunity,
                requirements: {
                  ...opportunity.requirements,
                  sustainabilityExpectation: event.target.checked,
                },
              })
            }
          />
          <span>Sustainability expectation</span>
        </label>

        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={opportunity.geography.inPreferredRegion}
            onChange={(event) =>
              onOpportunityChange({
                ...opportunity,
                geography: {
                  ...opportunity.geography,
                  inPreferredRegion: event.target.checked,
                },
              })
            }
          />
          <span>In preferred region</span>
        </label>
      </div>

      <div className="service-picker">
        <p className="service-picker-label">Required services</p>
        <div className="service-chip-list">
          {SERVICE_TYPES.map((service) => {
            const selected =
              opportunity.requirements.requiredServices.includes(service);

            return (
              <button
                key={service}
                type="button"
                className={selected ? "service-chip active" : "service-chip"}
                onClick={() => updateService(service)}
              >
                {serviceTypeLabels[service]}
              </button>
            );
          })}
        </div>
      </div>
    </>
  );
}
