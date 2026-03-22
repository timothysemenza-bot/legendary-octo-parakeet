# Token Usage Billing Model

Last updated: 2026-03-20

## Goal

Track OpenAI usage at the request and workflow level, turn it into an internal cost ledger, and then wrap that raw cost in a client-facing commercial model that matches Boss Key's setup-fee, retainer, and overage structure.

This should be treated as a billing and pricing layer, not just a token counter.

## What to meter

For every OpenAI request, store:

- `tenant_id` or `client_id`
- `project_id`
- `workflow_id`
- `feature_name`
- `user_id`
- `request_id`
- `openai_response_id`
- `model`
- `input_tokens`
- `cached_input_tokens`
- `output_tokens`
- `reasoning_tokens`
- `tool_name`
- `tool_cost_usd`
- `api_cost_usd`
- `billed_cost_usd`
- `pricing_version`
- `created_at`

If the app uses the Responses API, the usage object should be captured directly from the API response and normalized into this table.

## Raw cost formula

For text calls, calculate raw OpenAI cost as:

```text
raw_cost_usd =
  (uncached_input_tokens / 1_000_000 * input_rate_per_million) +
  (cached_input_tokens / 1_000_000 * cached_input_rate_per_million) +
  (output_tokens / 1_000_000 * output_rate_per_million) +
  tool_cost_usd
```

Where:

- `uncached_input_tokens = input_tokens - cached_input_tokens`
- `tool_cost_usd` is tracked separately for tools like web search, file search, or computer use when applicable

## Suggested ledger tables

1. `llm_usage_events`
- one row per OpenAI request

2. `llm_usage_rollups`
- daily and monthly summaries by client, project, workflow, and feature

3. `billing_line_items`
- the customer-facing billable items that may or may not map 1:1 to usage events

4. `pricing_versions`
- preserves the token rates, markup rules, included usage allowance, and packaging rules that were active when an event was billed

## Recommended billing modes

Use one of these commercial modes per client:

1. `usage_included`
- token cost is absorbed inside a fixed fee or monthly retainer
- best for premium managed-service packaging

2. `usage_allowance_plus_overage`
- monthly retainer includes a usage credit or workflow allowance
- overages bill separately once the allowance is exceeded

3. `pass_through_plus_markup`
- raw API spend is billed with a markup multiplier or platform fee
- best for highly variable or client-owned-key environments

## Best fit for Boss Key

Based on the current repo pricing assets, the strongest default is:

- fixed setup fee
- monthly retainer
- included usage allowance
- overage for heavy proposal cycles or extra regeneration

That matches the current business structure better than pure pass-through billing.

## How to map this to current pricing strategy

These repo files already point to the commercial wrapper:

- `marketing-agents/BOSS-KEY-PRICING-MODEL.md`
  - uses `price_to_win_usd`, `minimum_acceptable_price_usd`, and offer shaping
- `apmp-foundation-business-blueprint.md`
  - emphasizes gross margin per engagement and monthly retainers
- `projects/pipeline/revenue-iq-mvp/docs/05-margin-calculator.csv`
  - already contains `setup_fee`, `monthly_retainer`, `target_gross_margin`, and `overage_per_rfp_cycle`

So the token ledger should feed internal cost and margin visibility, while the client invoice still follows the offer structure.

## Practical pricing wrapper

Recommended packaging rule:

```text
customer_price =
  setup_fee +
  monthly_retainer +
  usage_overage +
  special_tooling_overage
```

Where:

- `monthly_retainer` includes a target amount of AI usage
- `usage_overage` begins only after the allowance is exceeded
- `special_tooling_overage` covers unusually expensive actions like high-volume document processing, deep research, or repeated full-package rebuilds

## Estimation model

Estimate usage per workflow instead of per prompt.

Example workflow buckets:

1. `light`
- intake, extraction, summaries, short rewrites

2. `medium`
- structured drafting, section generation, iterative refinement

3. `heavy`
- full proposal package generation, multi-stage reviews, repeated regenerations

For each workflow, estimate:

- average input tokens per call
- average cached input tokens per call
- average output tokens per call
- calls per run
- expected reruns per month

Then compute:

```text
estimated_monthly_ai_cost =
  sum(workflow_cost_per_run * monthly_run_count)
```

Add a planning buffer for retries and user-driven iteration:

- `15%` buffer for stable internal workflows
- `25% to 35%` buffer for user-facing generative apps

## Example request math

If a request uses:

- `1060` input tokens
- `0` cached input tokens
- `784` output tokens

Then a rough cost at GPT-5.4 rates is:

```text
input  = 1060 / 1_000_000 * 2.50  = 0.00265
output =  784 / 1_000_000 * 15.00 = 0.01176
total  = 0.01441
```

That is about `1.4 cents` for that request, before any tool charges.

At GPT-5 mini rates, the same request is materially cheaper:

```text
input  = 1060 / 1_000_000 * 0.25 = 0.000265
output =  784 / 1_000_000 * 2.00 = 0.001568
total  = 0.001833
```

That is about `0.18 cents`.

## Implementation guidance

1. Capture usage on every API response.
- Do not estimate tokens when the API already returned usage.

2. Persist both raw usage and derived cost.
- Raw usage is your audit trail.
- Derived cost is your billable/internal reporting layer.

3. Version your rates.
- Never recalculate old bills against new pricing.

4. Keep tool charges separate.
- Text token charges and tool charges should not be blended invisibly.

5. Log request identifiers.
- Store both your internal trace id and the OpenAI request/response ids for support and reconciliation.

6. Separate internal margin from client invoice logic.
- The token ledger drives cost visibility.
- The commercial package determines what the client sees.

## Recommended first implementation

Build v1 in this order:

1. usage event capture
2. raw cost calculation
3. daily and monthly rollups
4. client allowance and overage rules
5. invoice line item generation

Do not start with dynamic client invoices. Start with an internal cost dashboard and a shadow billing report first.

## Official OpenAI references

- Pricing: https://openai.com/api/pricing/
- Prompt caching: https://platform.openai.com/docs/guides/prompt-caching
- API overview, request IDs, and admin usage/cost endpoints: https://developers.openai.com/api/reference/overview
