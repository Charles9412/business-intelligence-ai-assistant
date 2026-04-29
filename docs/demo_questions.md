# Demo Questions

These questions are designed for later RAG, SQL, and hybrid routing tests. The assistant logic is not implemented yet.

## Document-Only Questions

- How does FinSight PayOps define Total Payment Volume?
- What is the difference between Payment Success Rate and Payment Failure Rate?
- When should a provider failure rate be escalated for operational review?
- How should pending payments be interpreted in dashboards?
- What makes a client strategic according to the segmentation rules?
- How should risk level influence client segmentation analysis?

## SQL-Only Questions

- How many clients are active, inactive, and suspended?
- What is the total payment amount by month for the last 12 months in the dataset?
- Which providers have the highest failed payment counts?
- What is the payment success rate by provider channel?
- What is the average payment amount by client type?
- Which regions have the highest total successful payment amount?
- How many payments are pending or reversed by month?

## Hybrid Questions

- Which providers exceed the policy threshold for operational review based on their failure rate?
- Which high-value clients have elevated failure rates and should be prioritized for review?
- Based on the segmentation rules, how many clients appear low-value, standard, high-value, and strategic?
- Are any regions showing abnormal payment behavior compared with the policy definition?
- Which client types contribute the most successful payment amount, and how should that affect KPI interpretation?
- How should reversed payments affect total payment amount reporting for the current dataset?
