# Client Segmentation Rules

FinSight PayOps uses synthetic segmentation rules to group demo clients for business intelligence analysis. These rules are fictional and designed for assistant development.

## Segment Inputs

Client segmentation should consider successful payment amount, successful payment count, recent activity, client type, and risk level.

Recommended activity window: trailing 12 months from the reporting date.

## Low-Value Client

A Low-Value Client has limited successful payment activity.

Example threshold: less than `25,000` in successful payment amount and fewer than `10` successful payments over the trailing 12 months.

Low-value clients may still require support if they have high failure rates or a high risk level.

## Standard Client

A Standard Client has consistent but moderate payment activity.

Example threshold: at least `25,000` and less than `250,000` in successful payment amount over the trailing 12 months, or between `10` and `49` successful payments.

This segment is useful for baseline operational comparisons.

## High-Value Client

A High-Value Client has strong payment activity and should be monitored for service quality.

Example threshold: at least `250,000` in successful payment amount or at least `50` successful payments over the trailing 12 months.

High-value clients with rising failure rates should be prioritized for operational review.

## Strategic Client

A Strategic Client has enterprise-scale activity or unusually high operational importance.

Example threshold: Enterprise client type plus at least `1,000,000` in successful payment amount over the trailing 12 months, or at least `150` successful payments.

Strategic clients should be reviewed with both payment performance and risk context.

## Risk-Level Interpretation

Low risk indicates normal monitoring. Medium risk indicates the client should be reviewed when failure rates, reversals, or payment spikes increase. High risk indicates closer monitoring and stronger review of abnormal behavior.

Risk level should not be used by itself to classify value. A high-risk client can be low-value, standard, high-value, or strategic depending on payment activity.
