# Payment Operations Policy

This synthetic policy describes how FinSight PayOps reviews payment activity in the demo environment. It is fictional and should not be used as real operational, legal, compliance, or risk guidance.

## Failed Payment Review

Failed payments should be reviewed daily by provider, channel, region, and failure reason. The first review should separate client-correctable issues from provider or network issues.

Client-correctable failures include insufficient funds, invalid account details, and expired authorization. Operations should summarize these patterns for client success teams when repeated failures affect the same client.

Provider or network failures include provider timeout and network error. These should be grouped by provider and channel to detect instability.

Risk rule declines should be reviewed with the risk operations queue. A risk rule decline is not automatically an incident, but repeated spikes should be investigated.

## Provider Failure-Rate Thresholds

Provider failure rates are reviewed using total payment attempts as the denominator.

- Below 5%: normal operating range.
- 5% to 8%: monitor and compare with the previous seven days.
- Above 8%: open an operational review for the provider and channel.
- Above 12%: escalate to incident triage if the pattern affects multiple clients or regions.

Thresholds should be interpreted with payment volume. A small provider with very few attempts can cross a threshold because of a small number of failures.

## Abnormal Payment Behavior

Payment behavior is abnormal when it differs materially from the client's usual pattern or the portfolio baseline.

Examples include a sudden payment amount increase above three times the client's trailing average, a same-day spike in failed attempts, repeated reversals after successful payments, or a rapid shift to a new provider channel.

Abnormal behavior does not always indicate fraud. It can also reflect a seasonal campaign, onboarding of a new merchant flow, client growth, or provider instability.

## Pending Payments

Pending payments are unresolved attempts. They should not be counted as successful revenue until completed. Dashboards should either show pending payments separately or clearly state whether they are excluded.

A high pending rate can indicate delayed provider confirmation, reconciliation lag, or incomplete downstream processing.

## Reversed Payments

Reversed payments are payments that were later undone. They should be separated from failed payments because a reversal happens after an initial payment lifecycle event.

Reversed payment amounts should not be treated as retained payment value. When calculating net payment amount, subtract reversed amounts or report them as a separate adjustment, depending on the metric definition used.
