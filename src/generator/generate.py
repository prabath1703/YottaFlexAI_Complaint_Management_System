import json
import random
from pathlib import Path

import pandas as pd

from .master_data import (
    generate_customers,
    generate_products,
    generate_categories,
)

from .transaction_data import (
    generate_orders,
    generate_complaints,
)

from .apply_rules import (
    apply_business_rules,
)

from .workflow_data import (
    generate_messages,
    generate_status_events,
    generate_resolutions,
    generate_surveys,
)

from .edge_cases import (
    inject_anomalies,
)


# ============================================================
# PROJECT PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

CONFIG_PATH = ROOT / "config" / "config.json"

OUTPUT_DIR = ROOT / "data" / "output"

GROUND_TRUTH_DIR = ROOT / "data" / "ground_truth"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

GROUND_TRUTH_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# LOAD CONFIGURATION
# ============================================================

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    config = json.load(file)


SEED = config["seed"]

rng = random.Random(SEED)


# ============================================================
# PIPELINE START
# ============================================================

print("=" * 60)
print("COMPLAINT MANAGEMENT DATA PIPELINE")
print("=" * 60)


# ============================================================
# GENERATE MASTER DATA
# ============================================================

print("\nGenerating master data...")

customers = generate_customers(
    config["scale"]["customers"],
    rng,
)

products = generate_products(
    config["scale"]["products"],
    rng,
)

categories = generate_categories()


# ============================================================
# GENERATE TRANSACTION DATA
# ============================================================

print("\nGenerating transaction data...")

orders = generate_orders(
    customers,
    products,
    config["scale"]["orders"],
    rng,
)

complaints = generate_complaints(
    customers,
    products,
    orders,
    categories,
    config["scale"]["complaints"],
    rng,
)


# ============================================================
# APPLY BUSINESS RULES
# ============================================================

print("\nApplying business rules...")

complaints, assignments, sla_clocks = apply_business_rules(
    complaints,
    orders,
    rng,
)


# ============================================================
# GENERATE WORKFLOW DATA
# ============================================================

print("\nGenerating workflow events...")

messages = generate_messages(
    complaints,
    config["scale"]["messages"],
    rng,
)

status_events = generate_status_events(
    complaints,
    rng,
)

resolutions = generate_resolutions(
    complaints,
    status_events,
    rng,
)

surveys = generate_surveys(
    complaints,
    status_events,
    rng,
)


# ============================================================
# INJECT DELIBERATE ANOMALIES
# ============================================================

print("\nInjecting deliberate edge cases...")

ground_truth = inject_anomalies(
    customers,
    complaints,
    assignments,
    sla_clocks,
    resolutions,
    surveys,
    status_events,
)


# ============================================================
# CONVERT TO DATAFRAMES
# ============================================================

customers_df = pd.DataFrame(customers)

products_df = pd.DataFrame(products)

categories_df = pd.DataFrame(categories)

orders_df = pd.DataFrame(orders)

complaints_df = pd.DataFrame(complaints)

assignments_df = pd.DataFrame(assignments)

sla_df = pd.DataFrame(sla_clocks)

messages_df = pd.DataFrame(messages)

status_events_df = pd.DataFrame(status_events)

resolutions_df = pd.DataFrame(resolutions)

surveys_df = pd.DataFrame(surveys)

ground_truth_df = pd.DataFrame(ground_truth)


# ============================================================
# SAVE OUTPUT DATA
# ============================================================

customers_df.to_csv(
    OUTPUT_DIR / "customers.csv",
    index=False,
)

products_df.to_csv(
    OUTPUT_DIR / "products.csv",
    index=False,
)

categories_df.to_csv(
    OUTPUT_DIR / "categories.csv",
    index=False,
)

orders_df.to_csv(
    OUTPUT_DIR / "orders.csv",
    index=False,
)

complaints_df.to_csv(
    OUTPUT_DIR / "complaints.csv",
    index=False,
)

assignments_df.to_csv(
    OUTPUT_DIR / "assignments.csv",
    index=False,
)

sla_df.to_csv(
    OUTPUT_DIR / "sla_clocks.csv",
    index=False,
)

messages_df.to_csv(
    OUTPUT_DIR / "complaint_messages.csv",
    index=False,
)

status_events_df.to_csv(
    OUTPUT_DIR / "status_events.csv",
    index=False,
)

resolutions_df.to_csv(
    OUTPUT_DIR / "resolutions.csv",
    index=False,
)

surveys_df.to_csv(
    OUTPUT_DIR / "surveys.csv",
    index=False,
)

ground_truth_df.to_csv(
    GROUND_TRUTH_DIR / "ground_truth.csv",
    index=False,
)


# ============================================================
# SUMMARY
# ============================================================

print("\nMASTER DATA GENERATED")
print("-" * 40)

print(f"Customers  : {len(customers_df)}")
print(f"Products   : {len(products_df)}")
print(f"Categories : {len(categories_df)}")
print(f"Orders     : {len(orders_df)}")
print(f"Complaints : {len(complaints_df)}")
print(f"Messages   : {len(messages_df)}")
print(f"Events     : {len(status_events_df)}")
print(f"Resolutions: {len(resolutions_df)}")
print(f"Surveys    : {len(surveys_df)}")


print("\nFiles created:")

print("  data/output/customers.csv")
print("  data/output/products.csv")
print("  data/output/categories.csv")
print("  data/output/orders.csv")
print("  data/output/complaints.csv")
print("  data/output/assignments.csv")
print("  data/output/sla_clocks.csv")
print("  data/output/complaint_messages.csv")
print("  data/output/status_events.csv")
print("  data/output/resolutions.csv")
print("  data/output/surveys.csv")

print("\nGround truth anomalies:")
print(f"  {len(ground_truth_df)} deliberate anomalies")

print("  data/ground_truth/ground_truth.csv")

print("\nPipeline generation completed successfully.")