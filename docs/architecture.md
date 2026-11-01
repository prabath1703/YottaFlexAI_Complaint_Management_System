# Complaint Management Data Pipeline — Architecture

## 1. Overview

The Complaint Management Data Pipeline generates a reproducible synthetic complaint-management dataset and processes it through business rules, workflow events, anomaly injection, validation, and analytics.

The architecture follows a **parent-first and dependency-aware generation model**. Master entities are created before transaction entities, and transaction entities are created before workflow records.

The pipeline is deterministic through a configured random seed and produces measurable outputs that can be independently validated.

---

## 2. High-Level Architecture

```text
                         ┌──────────────────────┐
                         │   config/config.json │
                         │ Seed + Scale + Rules  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │       MASTER DATA            │
                    │                              │
                    │ Customers                    │
                    │ Products                     │
                    │ Categories                   │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │     TRANSACTION DATA         │
                    │                              │
                    │ Orders                       │
                    │ Complaints                   │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │      BUSINESS RULES          │
                    │                              │
                    │ Priority calculation         │
                    │ Team assignment              │
                    │ Agent assignment              │
                    │ SLA calculation               │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │      WORKFLOW EVENTS         │
                    │                              │
                    │ Messages                     │
                    │ Status events                │
                    │ Resolutions                  │
                    │ Surveys                      │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │     EDGE CASE INJECTION      │
                    │                              │
                    │ 6 deliberate anomalies       │
                    └──────────────┬───────────────┘
                                   │
                     ┌─────────────┴──────────────┐
                     ▼                            ▼
          ┌─────────────────────┐       ┌─────────────────────┐
          │     VALIDATION      │       │      ANALYTICS      │
          │                     │       │                     │
          │ PK/FK checks        │       │ Volume metrics      │
          │ Date checks         │       │ SLA metrics         │
          │ Lifecycle checks    │       │ Resolution metrics  │
          │ Ground truth checks │       │ Survey metrics      │
          └──────────┬──────────┘       └──────────┬──────────┘
                     │                             │
                     └──────────────┬──────────────┘
                                    ▼
                         ┌────────────────────────┐
                         │       OUTPUT DATA      │
                         │                        │
                         │ CSV datasets           │
                         │ Ground truth           │
                         │ Metrics summary        │
                         └────────────────────────┘
```

---

## 3. Pipeline Stages

### Stage A — Configuration

The pipeline reads `config/config.json`.

Configuration controls:

- Random seed
- Dataset scale
- Priority levels
- Complaint channels
- Complaint categories
- Operational teams
- SLA duration by priority

The configured seed is:

```text
20261022
```

This makes the generated dataset reproducible.

---

### Stage B — Master Data Generation

Master data is generated first because other entities depend on these records.

Generated entities:

```text
Customers
Products
Categories
```

Example dependency:

```text
Customer
   │
   └── customer_id
          │
          ▼
        Order
```

Each master entity receives a unique identifier.

---

### Stage C — Transaction Data Generation

Transaction records are generated using valid master-data identifiers.

Generated entities:

```text
Orders
Complaints
```

Orders reference:

- `customer_id`
- `product_id`

Complaints reference:

- `customer_id`
- `order_id` (optional)
- `product_id`
- `category_id`

This allows the pipeline to represent realistic relationships between customers, purchases, and complaints.

---

### Stage D — Business Rule Processing

Each complaint is processed using deterministic business rules.

#### Priority calculation

Priority is derived from complaint characteristics.

The current rule order is:

```text
Safety issue
      ↓
     P1

Critical severity
      ↓
     P1

High severity
      ↓
     P2

Very negative sentiment
      ↓
     P2

Repeat complaint + high order value
      ↓
     P2

Medium severity
      ↓
     P3

Otherwise
      ↓
     P4
```

This means priority is **derived from source attributes**, rather than independently randomly assigned.

---

## 4. Team Assignment

The complaint category and safety flag determine the responsible team.

```text
Safety issue / PRODUCT_SAFETY
            ↓
     PRODUCT_SAFETY

DELIVERY
    ↓
 LOGISTICS

PAYMENT / BILLING
    ↓
  PAYMENTS

REFUND
    ↓
  REFUNDS

Other categories
    ↓
CUSTOMER_SUPPORT
```

After determining the team, an agent is selected from the configured agent pool for that team.

---

## 5. SLA Calculation

Each complaint receives an SLA based on its calculated priority.

```text
Priority     SLA
------------------
P1           4 hours
P2           12 hours
P3           24 hours
P4           72 hours
```

The SLA deadline is calculated as:

```text
SLA Deadline = Complaint Creation Time + SLA Duration
```

The SLA record is stored separately so that SLA tracking can be analyzed independently from the complaint record.

---

## 6. Workflow Generation

After business rules are applied, workflow records are generated.

### Communication

`complaint_messages.csv` stores complaint-related communication history.

### Lifecycle

`status_events.csv` stores explicit status transitions.

Example:

```text
CREATED
   ↓
ASSIGNED
   ↓
IN_PROGRESS
   ↓
RESOLVED
   ↓
CLOSED
```

The event history preserves the lifecycle instead of overwriting historical states.

### Resolution

A resolution record is generated for complaints that reach the closed state.

Possible resolution types include:

```text
REFUND
REPLACEMENT
EXPLANATION
CREDIT
CORRECTION
NO_ACTION
```

### Survey

Post-resolution surveys are generated for closed complaints.

This creates the final part of the traceability chain:

```text
Complaint
    ↓
Resolution
    ↓
Survey
```

---

# 7. Deliberate Anomaly Injection

The pipeline intentionally introduces six known anomalies after normal workflow generation.

This allows the validation layer to demonstrate that it can detect realistic data-quality and process exceptions.

| ID | Issue |
|---|---|
| ANOM-001 | Complaint without valid customer |
| ANOM-002 | Resolution before complaint |
| ANOM-003 | Incorrect SLA pause |
| ANOM-004 | Repeat issue not linked |
| ANOM-005 | Safety complaint assigned to wrong queue |
| ANOM-006 | Survey before closure |

The expected anomalies are stored separately in:

```text
data/ground_truth/ground_truth.csv
```

Ground truth is not used to generate normal business decisions. It exists to verify that the validation system detects the intentionally introduced exceptions.

---

# 8. Validation Layer

The validation layer checks structural, relational, business, and lifecycle integrity.

### Primary-key validation

Checks that identifiers are:

- Unique
- Non-null

### Foreign-key validation

Checks relationships such as:

```text
Order.customer_id → Customer.customer_id

Order.product_id → Product.product_id

Complaint.customer_id → Customer.customer_id

Complaint.order_id → Order.order_id
```

### Business validation

Checks:

- Valid priority values
- SLA priority consistency
- Lifecycle consistency
- Resolution timing
- Survey timing

### Ground-truth validation

Checks that all six deliberate anomaly types are detected.

---

# 9. Analytics Layer

The analytics module calculates summary metrics from the generated datasets.

Current metric groups include:

- Complaint volume by category
- Complaint volume by priority
- Complaint volume by channel
- Complaint status distribution
- Assignment distribution by team
- SLA compliance
- Resolution type distribution
- Survey rating distribution
- Ground-truth anomaly counts

The resulting summary is stored in:

```text
data/output/metrics_summary.json
```

---

# 10. Traceability Model

The pipeline supports end-to-end traceability.

```text
Customer
   │
   └── Order
         │
         └── Complaint
               │
               ├── Assignment
               │
               ├── SLA Clock
               │
               ├── Messages
               │
               ├── Status Events
               │
               ├── Resolution
               │
               └── Survey
```

A reviewer can therefore trace a complaint from its customer and order context through operational assignment, SLA tracking, communication, lifecycle events, resolution, and customer feedback.

---

# 11. Data Generation Order

The dependency order is intentional:

```text
1. Configuration
       ↓
2. Customers / Products / Categories
       ↓
3. Orders
       ↓
4. Complaints
       ↓
5. Priority / Assignment / SLA
       ↓
6. Messages / Status Events
       ↓
7. Resolutions / Surveys
       ↓
8. Deliberate Anomalies
       ↓
9. Validation
       ↓
10. Analytics
```

Generating data in this order reduces invalid relationships and makes foreign-key validation possible.

---

# 12. Reproducibility

The pipeline uses a fixed random seed from the configuration.

The reproducibility test executes the generator twice and compares SHA-256 checksums of the generated datasets.

Current result:

```text
REPRODUCIBILITY CHECK PASSED
Same seed produced identical datasets.
```

This demonstrates deterministic dataset generation.

---

# 13. Testing

The automated test suite validates core pipeline properties.

Current test result:

```text
10 passed
```

The tests cover:

- Primary-key uniqueness
- Foreign-key integrity
- Priority validity
- SLA consistency
- Resolution lifecycle
- Survey lifecycle
- Ground-truth anomaly coverage

---

# 14. Output Structure

```text
data/
├── output/
│   ├── customers.csv
│   ├── products.csv
│   ├── categories.csv
│   ├── orders.csv
│   ├── complaints.csv
│   ├── assignments.csv
│   ├── sla_clocks.csv
│   ├── complaint_messages.csv
│   ├── status_events.csv
│   ├── resolutions.csv
│   ├── surveys.csv
│   └── metrics_summary.json
│
└── ground_truth/
    └── ground_truth.csv
```

---

# 15. Design Principles

The pipeline follows these core design principles:

1. **Generate parent entities before dependent entities.**
2. **Use foreign keys to preserve relationships.**
3. **Derive business decisions from source attributes.**
4. **Preserve workflow history as explicit events.**
5. **Separate deliberate anomalies from normal generated data.**
6. **Validate relationships and business rules automatically.**
7. **Produce measurable analytics outputs.**
8. **Use a fixed seed for reproducibility.**
9. **Keep generation, validation, analytics, and configuration separated by responsibility.**
10. **Make the complete customer-to-resolution journey traceable.**