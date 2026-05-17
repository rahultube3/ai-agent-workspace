# Payment System

## Overview

A payment system handles the end-to-end flow of financial transactions between payers and payees, including authorization, processing, settlement, and reconciliation.

---

## Core Functionalities

### 1. Payment Initiation

- Accept payment requests from users or systems
- Support multiple payment methods: credit/debit cards, bank transfers, wallets, UPI
- Validate payment details before submission (amount, currency, recipient)
- Generate a unique transaction ID for each payment request

### 2. Authentication & Authorization

- Verify the identity of the payer (OTP, PIN, biometric, token)
- Check payer's account balance or credit limit
- Apply fraud detection rules before authorizing the transaction
- Enforce spending limits and velocity checks (e.g., max N transactions per hour)

### 3. Transaction Processing

- Route the transaction to the appropriate payment network or bank
- Handle synchronous and asynchronous payment flows
- Support retries for transient failures with idempotency guarantees
- Update transaction status: `PENDING → PROCESSING → SUCCESS / FAILED`

### 4. Settlement

- Batch or real-time settlement between financial institutions
- Calculate and deduct processing fees
- Reconcile settled amounts against initiated transactions
- Generate settlement reports for each settlement cycle

### 5. Refunds & Reversals

- Full and partial refund support
- Initiate chargebacks on disputed transactions
- Reverse failed or erroneous transactions within allowed timeframes
- Notify both payer and payee on refund completion

### 6. Notifications

- Send real-time alerts via SMS, email, or push notification on:
  - Transaction success or failure
  - Refund initiated/completed
  - Suspicious activity detected
- Provide webhook callbacks for merchant/system integrations

### 7. Reporting & Reconciliation

- Generate transaction history with filters (date range, status, method)
- Produce daily/monthly statements for users and merchants
- Flag and investigate unmatched or disputed entries
- Export reports in CSV, PDF, or JSON formats

### 8. Security

- Encrypt data in transit (TLS 1.2+) and at rest (AES-256)
- Tokenize sensitive card or account data (PCI-DSS compliance)
- Log all access and transaction events for audit trails
- Implement rate limiting and anomaly detection

---

## Transaction Lifecycle

```
Initiate → Validate → Authorize → Process → Settle → Notify → Reconcile
                          |
                     (Fraud Check)
                          |
                     FAILED / BLOCKED
```

---

## Transaction Statuses

| Status       | Description                                      |
|--------------|--------------------------------------------------|
| `PENDING`    | Request received, awaiting processing            |
| `PROCESSING` | Submitted to payment network                     |
| `SUCCESS`    | Transaction completed and settled                |
| `FAILED`     | Transaction could not be completed               |
| `REVERSED`   | Transaction rolled back                          |
| `REFUNDED`   | Amount returned to payer                         |
| `DISPUTED`   | Under chargeback or investigation                |

---

## Supported Payment Methods

- Credit / Debit Cards (Visa, Mastercard, Amex)
- Bank Transfers (ACH, NEFT, RTGS, IMPS)
- Digital Wallets (PayPal, Apple Pay, Google Pay)
- UPI / QR Code Payments
- Buy Now Pay Later (BNPL)

---

## Error Handling

| Error Code | Meaning                        | Action                          |
|------------|--------------------------------|---------------------------------|
| `INSUF_FUNDS` | Insufficient balance        | Notify payer, abort             |
| `INVALID_ACCT` | Account not found          | Validate and retry with correct details |
| `TIMEOUT`  | Network or gateway timeout     | Retry with exponential backoff  |
| `DECLINED` | Issuer declined transaction    | Notify payer, suggest alternate method |
| `DUPLICATE` | Duplicate transaction detected | Return existing transaction ID  |

---

## Compliance & Standards

- **PCI-DSS** — Card data security
- **AML** — Anti-money laundering checks
- **KYC** — Know Your Customer verification
- **GDPR / Data Privacy** — Secure storage and right to erasure

---

## Key Non-Functional Requirements

- **Availability**: 99.99% uptime SLA
- **Latency**: Authorization response within 2 seconds
- **Throughput**: Support 10,000+ transactions per second at peak
- **Idempotency**: Duplicate requests return the same result without double-processing
- **Auditability**: Full audit log retained for 7 years

---

## Fraud Detection & Risk Management

### Risk Scoring Engine

Every transaction is scored 0–100 before authorization. Scores above threshold trigger additional verification or blocking.

| Score Range | Risk Level | Action                          |
|-------------|------------|---------------------------------|
| 0 – 30      | Low        | Auto-approve                    |
| 31 – 60     | Medium     | Step-up authentication (OTP)    |
| 61 – 85     | High       | Manual review queue             |
| 86 – 100    | Critical   | Block transaction, alert team   |

### Fraud Detection Rules

- **Velocity checks** — Flag if > 5 transactions in 10 minutes from the same card
- **Geo-anomaly** — Alert when transaction originates from a country not in user's history
- **Device fingerprinting** — Detect unfamiliar devices or emulators
- **Amount anomaly** — Flag transactions 3x above the user's average spend
- **Card testing** — Detect rapid low-value transactions used to verify stolen cards
- **BIN attack detection** — Block burst of sequential card number attempts

### Machine Learning Models

- **Supervised model** — Trained on labeled fraud/non-fraud transaction history
- **Unsupervised model** — Detects anomalies in spending patterns
- **Graph model** — Maps relationships between accounts, devices, and IPs to detect rings
- Model retrained weekly with fresh labeled data; real-time scoring via low-latency API

### Chargeback & Dispute Management

- Merchants notified within 24 hours of a dispute being filed
- Evidence submission window: 7 calendar days
- Auto-collect evidence: transaction logs, device data, delivery proof, communication history
- Dispute statuses: `OPEN → UNDER_REVIEW → RESOLVED_WIN / RESOLVED_LOSS`
- Pre-arbitration available before escalating to card network

---

## Multi-Currency & FX Support

### Supported Currencies

- 135+ currencies supported including USD, EUR, GBP, INR, JPY, AED, SGD
- Cryptocurrencies: BTC, ETH, USDC (via licensed exchange partners)

### FX Rate Management

- Rates fetched from tier-1 FX providers every 60 seconds
- Spread applied: 0.5% – 1.5% depending on currency pair and merchant tier
- Rate lock available for 30 seconds during checkout to prevent slippage
- Fallback to last known rate if provider is unavailable (max 5 minutes stale)

### Currency Conversion Flow

```
Buyer pays in USD → System fetches live rate → Converts to merchant currency
                 → Displays exact amount to buyer before confirm
                 → Locks rate on confirmation → Settles in merchant's base currency
```

### Dynamic Currency Conversion (DCC)

- Cardholders abroad can pay in their home currency
- Merchant earns markup on DCC; rate disclosed to cardholder at checkout
- Compliant with Visa and Mastercard DCC rules

---

## Subscription & Recurring Payments

### Billing Models

| Model           | Description                                      | Example            |
|-----------------|--------------------------------------------------|--------------------|
| Fixed recurring | Same amount billed on a set schedule             | Netflix $15/month  |
| Usage-based     | Billed based on consumption metered each cycle   | AWS, Twilio        |
| Tiered          | Price changes at consumption thresholds          | SaaS seats pricing |
| Hybrid          | Base fee + usage overage charges                 | Mobile data plans  |

### Subscription Lifecycle

```
Trial → Active → Past Due → Cancelled / Paused
                    ↓
              Retry Logic (Smart Dunning)
```

### Smart Dunning (Retry Logic)

When a recurring charge fails, the system retries automatically:

- **Day 0**: First attempt fails → notify user
- **Day 3**: Retry with updated card details if available
- **Day 7**: Second retry + escalation email
- **Day 14**: Final retry + subscription suspension warning
- **Day 21**: Subscription cancelled if unpaid

### Proration

- Upgrades: charge the difference for remaining days in current cycle
- Downgrades: credit applied to next billing cycle
- Mid-cycle cancellation: refund unused days (configurable per merchant)

---

## Payment Gateway Integration

### Integration Methods

| Method       | Use Case                              | Latency  |
|--------------|---------------------------------------|----------|
| REST API     | Server-to-server payments             | < 300ms  |
| JS SDK       | Browser-side card capture (PCI scope) | < 500ms  |
| Mobile SDK   | iOS / Android native apps             | < 400ms  |
| Hosted Page  | Redirect-based checkout               | < 1s     |
| Webhook      | Async event delivery to merchants     | Variable |

### API Authentication

- **API Keys** — Static key-pair (public + secret); secret never sent client-side
- **OAuth 2.0** — For third-party platform integrations
- **JWT tokens** — Short-lived (15 min), signed with RS256 for session auth
- **HMAC signatures** — All webhook payloads signed with SHA-256; merchants verify before processing

### Idempotency

Every `POST` request must include an `Idempotency-Key` header (UUID). The server returns the same response for duplicate keys within 24 hours, preventing double charges on retries.

```
POST /v1/payments
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

### Webhook Events

| Event                      | Trigger                                    |
|----------------------------|--------------------------------------------|
| `payment.success`          | Transaction authorized and captured        |
| `payment.failed`           | Authorization declined                     |
| `payment.refunded`         | Refund processed                           |
| `dispute.created`          | Chargeback filed by cardholder             |
| `subscription.renewed`     | Recurring payment successfully charged     |
| `subscription.past_due`    | Recurring payment failed                   |
| `payout.completed`         | Merchant settlement transferred            |

### Rate Limits

| Endpoint Group     | Limit              |
|--------------------|--------------------|
| Payment creation   | 1,000 req/min      |
| Refund creation    | 200 req/min        |
| Webhook delivery   | 500 events/min     |
| Reporting APIs     | 100 req/min        |

Exceeded limits return `HTTP 429` with `Retry-After` header.

---

## Payment Analytics & Reporting

### Key Metrics

| Metric                  | Description                                              |
|-------------------------|----------------------------------------------------------|
| **Authorization Rate**  | % of transactions approved by issuer                    |
| **Decline Rate**        | % of transactions declined; segmented by decline reason |
| **Chargeback Rate**     | Chargebacks / total transactions (keep < 1% per Visa)   |
| **Refund Rate**         | Refunds issued as % of total volume                     |
| **Processing Time**     | p50 / p95 / p99 latency for end-to-end authorization    |
| **Settlement Lag**      | Time from capture to funds in merchant account          |
| **FX Loss/Gain**        | Net impact of currency fluctuation on settled amounts   |

### Real-Time Dashboard

- Live transaction feed with status, amount, method, country
- Alert rules: spike in failures > 5%, fraud score > threshold, settlement delay
- Funnel view: initiated → authorized → captured → settled

### Scheduled Reports

- **Daily**: Transaction summary, failed payment log, payout confirmation
- **Weekly**: Fraud summary, chargeback report, revenue by method
- **Monthly**: Full reconciliation report, fee invoice, compliance attestation
- Export formats: CSV, PDF, Excel, JSON via API

### Data Retention

| Data Type            | Retention Period |
|----------------------|------------------|
| Transaction records  | 7 years          |
| Audit logs           | 7 years          |
| PII (card data)      | Tokenized only   |
| Webhook logs         | 90 days          |
| Analytics snapshots  | 2 years          |
