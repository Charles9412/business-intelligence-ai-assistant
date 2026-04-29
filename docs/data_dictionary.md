# Data Dictionary

The FinSight PayOps dataset is synthetic and contains three related tables: `clients`, `providers`, and `payments`. It is designed for local RAG + SQL assistant development and does not include real client or payment data.

## Table: clients

One row per synthetic FinSight PayOps client.

| Field | Type | Description | Example |
| --- | --- | --- | --- |
| `client_id` | TEXT | Stable unique client identifier. Primary key. | `C0001` |
| `client_name` | TEXT | Fictional client display name. | `FinSight Demo Client 0001` |
| `client_type` | TEXT | Business category for the client. Allowed values: Individual, SME, Enterprise. | `SME` |
| `region` | TEXT | Operating region. Allowed values: North, Central, West, South, East. | `Central` |
| `signup_date` | TEXT | Date the client joined the platform in ISO format. | `2024-06-15` |
| `status` | TEXT | Current client status. Allowed values: Active, Inactive, Suspended. | `Active` |
| `risk_level` | TEXT | Synthetic operational risk level. Allowed values: Low, Medium, High. | `Medium` |

## Table: providers

One row per synthetic payment provider or payment rail.

| Field | Type | Description | Example |
| --- | --- | --- | --- |
| `provider_id` | TEXT | Stable unique provider identifier. Primary key. | `P001` |
| `provider_name` | TEXT | Fictional provider name. | `Aurora Card Network` |
| `channel` | TEXT | Payment channel handled by the provider. Allowed values: Card, Bank Transfer, Cash, Wallet, SPEI. | `Card` |
| `region` | TEXT | Main operating region for the provider. | `North` |
| `active_since` | TEXT | Date the provider became active in ISO format. | `2021-03-08` |
| `status` | TEXT | Current provider status. Allowed values: Active, Inactive. | `Active` |

## Table: payments

One row per synthetic payment attempt.

| Field | Type | Description | Example |
| --- | --- | --- | --- |
| `payment_id` | TEXT | Stable unique payment identifier. Primary key. | `PMT000001` |
| `client_id` | TEXT | Client that initiated the payment. Foreign key to `clients.client_id`. | `C0042` |
| `provider_id` | TEXT | Provider used for the payment attempt. Foreign key to `providers.provider_id`. | `P007` |
| `payment_date` | TEXT | Business date for the payment in ISO format. | `2025-11-28` |
| `amount` | REAL | Payment amount in the stated currency. | `1845.72` |
| `currency` | TEXT | Payment currency. Synthetic data uses mostly MXN and some USD. | `MXN` |
| `status` | TEXT | Payment lifecycle status. Allowed values: Successful, Failed, Pending, Reversed. | `Successful` |
| `failure_reason` | TEXT | Reason for failure. Populated only when `status = Failed`; otherwise blank or null. | `Provider timeout` |
| `created_at` | TEXT | Timestamp when the payment record was created. | `2025-11-28T14:35:12` |

## Relationships

`clients` has a one-to-many relationship with `payments`: one client can have many payment attempts, and each payment belongs to exactly one client.

`providers` has a one-to-many relationship with `payments`: one provider can process many payment attempts, and each payment uses exactly one provider.

The main analytical table is `payments`. Join it to `clients` for client type, client region, status, and risk analysis. Join it to `providers` for channel, provider region, and provider performance analysis.

Example join pattern:

```sql
SELECT
    c.client_type,
    p.channel,
    COUNT(*) AS payment_attempts,
    SUM(pay.amount) AS total_amount
FROM payments AS pay
JOIN clients AS c ON pay.client_id = c.client_id
JOIN providers AS p ON pay.provider_id = p.provider_id
GROUP BY c.client_type, p.channel;
```
