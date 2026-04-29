# KPI Definitions

FinSight PayOps uses the following synthetic KPI definitions for demo analysis. These definitions are fictional and intended for local assistant development only.

## Total Payment Volume

Total Payment Volume is the count of payment records in the selected period.

Formula: `COUNT(payment_id)`

Recommended dimensions: payment date, client type, client region, provider, provider channel, payment status, and currency.

## Total Payment Amount

Total Payment Amount is the sum of payment amounts in the selected period.

Formula: `SUM(amount)`

Unless a question asks for gross submitted value, operational reports should usually focus on successful payments. Pending, failed, and reversed payments should be shown separately when the distinction matters.

## Average Payment Value

Average Payment Value is the mean payment amount for the selected population.

Formula: `SUM(amount) / COUNT(payment_id)`

For performance dashboards, calculate this separately by client type because Enterprise payments are intentionally much larger than Individual payments in the synthetic dataset.

## Payment Success Rate

Payment Success Rate measures the share of payment attempts that completed successfully.

Formula: `Successful payments / Total payment attempts`

Payment attempts include Successful, Failed, Pending, and Reversed records unless a report explicitly excludes unresolved pending payments.

## Payment Failure Rate

Payment Failure Rate measures the share of payment attempts that failed.

Formula: `Failed payments / Total payment attempts`

Failure rate should be reviewed by provider, channel, region, and risk level. A higher failure rate can indicate provider instability, network issues, client input problems, or risk-rule declines.

## Active Client Count

Active Client Count is the number of clients with `status = Active`.

Formula: `COUNT(DISTINCT client_id)` where client status is Active.

For transaction-based activity, use clients with at least one payment in the selected period and state that the metric is active-by-usage rather than active-by-status.

## High-Value Client

A High-Value Client is a client whose successful payment amount is materially above the standard portfolio level.

Default synthetic threshold: at least `250,000` in successful payment amount over the trailing 12 months, or at least `50` successful payments over the trailing 12 months.

High-value classification is operational, not a credit or compliance decision. Risk level and recent failure patterns should be reviewed before prioritizing outreach.
