import type { PursuitRecommendation, RiskSeverity } from "../domain/qualification";

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export function formatCurrency(value: number): string {
  return currencyFormatter.format(value);
}

export function formatPercent(value: number): string {
  return `${value}%`;
}

export function formatRecommendation(
  recommendation: PursuitRecommendation,
): string {
  if (recommendation === "no-bid") {
    return "No-bid";
  }

  if (recommendation === "pursue") {
    return "Pursue";
  }

  return "Review";
}

export function formatSeverity(severity: RiskSeverity): string {
  return severity.charAt(0).toUpperCase() + severity.slice(1);
}

