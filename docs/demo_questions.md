# Demo Questions

These questions are designed for later RAG, SQL, and hybrid routing tests. The assistant logic is not implemented yet.

## Document-Only Questions

- How does FinSight PayOps define Total Payment Volume?
- What is the difference between Payment Success Rate and Payment Failure Rate?
- When should a provider failure rate be escalated for operational review?
- How should pending payments be interpreted in dashboards?
- What makes a client strategic according to the segmentation rules?
- How should risk level influence client segmentation analysis?

## Document RAG Questions

- What is Total Payment Amount?
- How is Average Payment Value calculated?
- What is payment success rate?
- What is payment failure rate?
- How should pending payments be interpreted?
- How should reversed payments be interpreted?
- How are failed payments reviewed?
- What provider failure-rate thresholds trigger monitoring or escalation?
- What counts as abnormal payment behavior?
- How are low-value clients classified?
- How are high-value clients classified?
- What makes a client strategic?
- How should risk level be interpreted during segmentation?

## SQL-Only Questions

- How many clients are active, inactive, and suspended?
- What is the total payment amount by month for the last 12 months in the dataset?
- Which providers have the highest failed payment counts?
- What is the payment success rate by provider channel?
- What is the average payment amount by client type?
- Which regions have the highest total successful payment amount?
- How many payments are pending or reversed by month?

## SQL Agent Questions

- Show total payment amount by provider.
- Which month had the highest number of failed payments?
- List the top 10 clients by total payment amount.
- Show payment success rate by provider.
- How many active clients are there by region?
- What is total payment amount by client type?
- Which provider channels have the highest average payment amount?
- How many payments are successful, failed, pending, and reversed?
- What are the top 10 providers by payment volume?
- What is the failed payment count by failure reason?
- Which regions have the highest number of high-risk clients?
- What is the monthly payment success rate?

## Hybrid Questions

- Which providers exceed the policy threshold for operational review based on their failure rate?
- Which high-value clients have elevated failure rates and should be prioritized for review?
- Based on the segmentation rules, how many clients appear low-value, standard, high-value, and strategic?
- Are any regions showing abnormal payment behavior compared with the policy definition?
- Which client types contribute the most successful payment amount, and how should that affect KPI interpretation?
- How should reversed payments affect total payment amount reporting for the current dataset?

## Router and Hybrid Questions

- What is payment success rate?
- How are failed payments reviewed?
- How are high-value clients classified?
- Show total payment amount by provider.
- Which month had the highest number of failed payments?
- List the top 10 clients by total payment amount.
- Using the KPI definition, calculate the payment success rate from the database.
- According to the client segmentation rules, how many high-value clients do we have?
- Based on the provider failure-rate threshold in the policy, which providers should be reviewed?
- Using the documents and database, summarize whether payment operations need attention.
