# Complaint Management Data Pipeline

A reproducible synthetic data pipeline for modeling, processing, validating, and analyzing a customer complaint-management workflow.

The project simulates the complete journey from **customer and order data → complaint creation → business-rule decisions → team assignment → SLA tracking → workflow events → resolution → customer survey**, while deliberately introducing known anomalies to demonstrate automated data-quality validation.

---

## 1. Project Objective

The objective is to build a small but realistic complaint-management data pipeline that:

- Generates related synthetic business data.
- Preserves relationships using primary and foreign keys.
- Applies deterministic business rules for priority and assignment.
- Calculates complaint SLAs.
- Preserves complaint lifecycle history as events.
- Generates resolutions and post-resolution surveys.
- Introduces deliberate data-quality and workflow anomalies.
- Validates structural, relational, business, and lifecycle integrity.
- Produces measurable analytics.
- Demonstrates reproducible data generation.

---

## 2. Business Scenario

A customer-support organization receives complaints through multiple channels such as email, phone, chat, and web.

Each complaint may be associated with:

- A customer
- An order
- A product
- A complaint category
- Severity and sentiment
- A safety indicator
- Previous/repeat complaints

The pipeline uses these attributes to determine:

1. Complaint priority
2. Responsible operational team
3. Assigned agent
4. SLA deadline
5. Workflow lifecycle
6. Resolution
7. Customer survey

This creates a traceable representation of the complaint-management process.

---

## 3. End-to-End Pipeline

```text
Configuration
      ↓
Master Data
      ↓
Customers / Products / Categories
      ↓
Orders
      ↓
Complaints
      ↓
Business Rules
      ↓
Priority + Team + Agent + SLA
      ↓
Workflow Events
      ↓
Messages + Status Events
      ↓
Resolution + Survey
      ↓
Deliberate Anomalies
      ↓
Validation
      ↓
Analytics
      ↓
CSV + JSON Outputs
```

---

## 4. Architecture

The detailed architecture and data-flow documentation is available here:

- [Architecture & Data Flow](docs/architecture.md)
- [Data Dictionary](docs/data-dictionary.md)

The architecture follows a **parent-first generation model** so dependent records can reference valid parent identifiers.

---

## 5. Dataset Scale

The default configuration generates:

| Dataset | Records |
|---|---:|
| Customers | 5,000 |
| Products | 100 |
| Categories | 10 |
| Orders | 8,000 |
| Complaints | 2,000 |
| Complaint Messages | 6,000 |
| Status Events | 9,614 |
| Resolutions | 1,807 |
| Surveys | 1,807 |
| Deliberate Anomalies | 6 |

The scale can be changed through:

```text
config/config.json
```

---

## 6. Core Entities

```text
Customer
   │
   ├── Order
   │      └── Product
   │
   └── Complaint
          ├── Assignment
          ├── SLA Clock
          ├── Complaint Messages
          ├── Status Events
          ├── Resolution
          └── Survey
```

### Main entities

- **Customer** — synthetic customer master records.
- **Product** — product and safety-risk information.
- **Category** — complaint category reference data.
- **Order** — customer purchase records.
- **Complaint** — primary business transaction.
- **Assignment** — responsible team and agent.
- **SLA Clock** — priority-based SLA tracking.
- **Complaint Message** — communication history.
- **Status Event** — complaint lifecycle history.
- **Resolution** — final complaint action.
- **Survey** — post-resolution customer feedback.
- **Ground Truth** — known deliberate anomalies.

---

## 7. Business Rules

### Priority

Priority is derived from complaint characteristics rather than independently randomized.

Current decision order:

```text
Safety issue
    → P1

Critical severity
    → P1

High severity
    → P2

Very negative sentiment
    → P2

Repeat complaint + high order value
    → P2

Medium severity
    → P3

Otherwise
    → P4
```

### Team Assignment

```text
Safety / PRODUCT_SAFETY → PRODUCT_SAFETY

DELIVERY → LOGISTICS

PAYMENT / BILLING → PAYMENTS

REFUND → REFUNDS

Other categories → CUSTOMER_SUPPORT
```

### SLA

| Priority | SLA |
|---|---:|
| P1 | 4 hours |
| P2 | 12 hours |
| P3 | 24 hours |
| P4 | 72 hours |

The deadline is calculated from the complaint creation time.

---

## 8. Workflow Lifecycle

Complaint history is represented using explicit status events rather than overwriting historical states.

Typical lifecycle:

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

A closed complaint may then receive:

```text
Resolution
    ↓
Customer Survey
```

This preserves traceability throughout the complaint lifecycle.

---

## 9. Deliberate Anomalies

Six known anomalies are intentionally injected into the generated data.

| ID | Deliberate Issue |
|---|---|
| ANOM-001 | Complaint without valid customer |
| ANOM-002 | Resolution before complaint |
| ANOM-003 | Incorrect SLA pause |
| ANOM-004 | Repeat issue not linked |
| ANOM-005 | Safety complaint assigned to wrong queue |
| ANOM-006 | Survey before closure |

Expected anomaly information is stored separately:

```text
data/ground_truth/ground_truth.csv
```

This allows the validation system to demonstrate that known exceptions can be detected without mixing ground-truth labels into normal business data.

---

## 10. Data Validation

The validation layer checks:

### Structural integrity

- Primary-key uniqueness
- Required fields
- Valid enumerated values

### Referential integrity

- Customer references
- Product references
- Order references
- Complaint references

### Business integrity

- Priority values
- SLA/priority consistency
- Assignment consistency
- Lifecycle rules

### Temporal integrity

- Complaint and resolution ordering
- Survey timing
- Status-event chronology
- SLA timing

### Ground-truth validation

The validator confirms that all six deliberate anomaly types are detected.

---

## 11. Analytics

The analytics layer produces:

- Complaint volume by category
- Complaint volume by priority
- Complaint volume by channel
- Complaint status distribution
- Assignment distribution by team
- SLA compliance
- Resolution type distribution
- Survey rating distribution
- Ground-truth anomaly counts

Output:

```text
data/output/metrics_summary.json
```

---

## 12. Reproducibility

The pipeline uses a fixed random seed:

```text
20261022
```

The reproducibility script generates the dataset twice and compares SHA-256 checksums.

Result:

```text
REPRODUCIBILITY CHECK PASSED
Same seed produced identical datasets.
```

All generated datasets matched between the two runs.

---

## 13. Automated Testing

The project includes a pytest test suite covering core data and workflow integrity.

Current result:

```text
10 passed
```

Tests cover:

- Unique customer IDs
- Unique order IDs
- Unique complaint IDs
- Order/customer foreign-key integrity
- Complaint/order foreign-key integrity
- Valid priority values
- SLA/priority consistency
- Resolution lifecycle
- Survey lifecycle
- Ground-truth anomaly coverage

Run:

```powershell
pytest -v
```

---

## 14. Project Structure

```text
Complaint-Management-Data-Pipeline/
│
├── app/
│
├── config/
│   └── config.json
│
├── data/
│   ├── output/
│   │   ├── customers.csv
│   │   ├── products.csv
│   │   ├── categories.csv
│   │   ├── orders.csv
│   │   ├── complaints.csv
│   │   ├── assignments.csv
│   │   ├── sla_clocks.csv
│   │   ├── complaint_messages.csv
│   │   ├── status_events.csv
│   │   ├── resolutions.csv
│   │   ├── surveys.csv
│   │   └── metrics_summary.json
│   │
│   └── ground_truth/
│       └── ground_truth.csv
│
├── docs/
│   ├── architecture.md
│   └── data-dictionary.md
│
├── scripts/
│   └── check_reproducibility.py
│
├── src/
│   ├── analytics/
│   │   └── metrics.py
│   │
│   ├── generator/
│   │   ├── master_data.py
│   │   ├── transaction_data.py
│   │   ├── business_rules.py
│   │   ├── apply_rules.py
│   │   ├── workflow_data.py
│   │   ├── edge_cases.py
│   │   └── generate.py
│   │
│   └── validation/
│       └── validator.py
│
├── tests/
│   └── test_pipeline.py
│
├── requirements.txt
└── README.md
```

---

## 15. How to Run

### 1. Install dependencies

```powershell
pip install -r requirements.txt
```

### 2. Generate the dataset

```powershell
python -m src.generator.generate
```

### 3. Run validation

```powershell
python -m src.validation.validator
```

### 4. Generate analytics

```powershell
python -m src.analytics.metrics
```

### 5. Run automated tests

```powershell
pytest -v
```

### 6. Check reproducibility

```powershell
python scripts\check_reproducibility.py
```

---

## 16. Key Design Decisions

### Parent-first generation

Master records are generated before dependent records to maintain valid relationships.

### Derived business decisions

Priority, team assignment, and SLA values are calculated from source attributes and documented rules.

### Event-based history

Status changes and communication are stored as records so workflow history is preserved.

### Separate ground truth

Known anomalies are maintained separately from normal generated data.

### Deterministic generation

A fixed seed enables repeatable datasets and reproducible testing.

### Automated validation

The pipeline validates relationships, business rules, temporal consistency, and deliberate exceptions.

---

## 17. Validation Evidence

The current implementation has successfully demonstrated:

```text
Dataset generation          ✓
Business rules              ✓
Workflow generation         ✓
6 deliberate anomalies      ✓
Validation                  ✓
Analytics                   ✓
Automated tests             ✓ 10 passed
Reproducibility              ✓ PASSED
```

---

## 18. Project Status

**Core data pipeline: Complete**

The current implementation provides a reproducible synthetic complaint-management workflow with:

- Related business entities
- Business-rule processing
- SLA calculations
- Workflow event history
- Resolution and survey lifecycle
- Deliberate edge cases
- Automated validation
- Analytics
- Automated tests
- Reproducibility verification

---

## 19. Documentation

| Document | Purpose |
|---|---|
| [Architecture](docs/architecture.md) | Pipeline architecture and data flow |
| [Data Dictionary](docs/data-dictionary.md) | Entity and field definitions |
| `config/config.json` | Pipeline configuration and scale |
| `data/ground_truth/ground_truth.csv` | Deliberate anomaly definitions |

---

## 20. Technology Stack

- **Python 3**
- **Pandas** — data processing
- **Faker** — synthetic data generation
- **Pytest** — automated testing
- **JSON** — configuration and analytics summary
- **CSV** — generated datasets

---

## 21. Summary

This project demonstrates an end-to-end synthetic data pipeline for a complaint-management business process.

It combines relational data generation, deterministic business rules, workflow modeling, SLA tracking, anomaly injection, automated validation, analytics, testing, and reproducibility into one traceable pipeline.

The design emphasizes **data quality, referential integrity, business-rule transparency, lifecycle traceability, and repeatable execution**.