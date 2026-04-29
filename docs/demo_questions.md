# Demo Questions

Use these questions to demonstrate the three assistant routes: document RAG, SQL analytics, and hybrid reasoning.

## RAG Questions

- What is payment success rate?
- How are failed payments reviewed?
- How are high-value clients classified?
- What is Total Payment Amount?
- How is Average Payment Value calculated?
- What provider failure-rate thresholds trigger monitoring or escalation?
- What counts as abnormal payment behavior?
- How should pending payments be interpreted?
- How should reversed payments be interpreted?
- What makes a client strategic?

## SQL Questions

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

## Hybrid Questions

- Using the KPI definition, calculate the payment success rate from the database.
- According to the client segmentation rules, how many high-value clients do we have?
- Based on the provider failure-rate threshold in the policy, which providers should be reviewed?
- Based on the segmentation rules, how many clients appear low-value, standard, high-value, and strategic?
- Which high-value clients have elevated failure rates and should be prioritized for review?
- Which providers exceed the policy threshold for operational review based on their failure rate?
- Are any regions showing abnormal payment behavior compared with the policy definition?
- Which client types contribute the most successful payment amount, and how should that affect KPI interpretation?
- How should reversed payments affect total payment amount reporting for the current dataset?
- Using the documents and database, summarize whether payment operations need attention.
