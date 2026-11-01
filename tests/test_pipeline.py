from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "data" / "output"
GROUND_TRUTH_DIR = BASE_DIR / "data" / "ground_truth"


def load_csv(name):
    return pd.read_csv(OUTPUT_DIR / f"{name}.csv")


def test_customer_ids_are_unique():
    customers = load_csv("customers")

    assert customers["customer_id"].is_unique
    assert customers["customer_id"].notna().all()


def test_order_ids_are_unique():
    orders = load_csv("orders")

    assert orders["order_id"].is_unique
    assert orders["order_id"].notna().all()


def test_complaint_ids_are_unique():
    complaints = load_csv("complaints")

    assert complaints["complaint_id"].is_unique
    assert complaints["complaint_id"].notna().all()


def test_order_customer_foreign_keys():
    customers = load_csv("customers")
    orders = load_csv("orders")

    valid_customer_ids = set(customers["customer_id"])

    invalid_ids = set(orders["customer_id"]) - valid_customer_ids

    assert not invalid_ids


def test_complaint_order_foreign_keys():
    orders = load_csv("orders")
    complaints = load_csv("complaints")

    valid_order_ids = set(orders["order_id"])

    linked_orders = complaints["order_id"].dropna()

    invalid_ids = set(linked_orders) - valid_order_ids

    # The deliberate missing-order anomaly is a complaint/customer
    # relationship issue, so ordinary valid order references must remain valid.
    assert not invalid_ids


def test_priority_values_are_valid():
    complaints = load_csv("complaints")

    allowed_priorities = {"P1", "P2", "P3", "P4"}

    actual_priorities = set(
        complaints["priority"].dropna()
    )

    assert actual_priorities.issubset(allowed_priorities)


def test_sla_priorities_match_complaints():
    complaints = load_csv("complaints")
    sla = load_csv("sla_clocks")

    complaint_priorities = complaints.set_index(
        "complaint_id"
    )["priority"]

    for _, row in sla.iterrows():
        complaint_id = row["complaint_id"]

        if complaint_id in complaint_priorities.index:
            assert row["priority"] == complaint_priorities.loc[
                complaint_id
            ]


def test_resolutions_are_for_closed_complaints():
    resolutions = load_csv("resolutions")
    status_events = load_csv("status_events")

    closed_complaints = set(
        status_events.loc[
            status_events["to_status"] == "CLOSED",
            "complaint_id",
        ]
    )

    resolution_complaints = set(
        resolutions["complaint_id"]
    )

    assert resolution_complaints.issubset(
        closed_complaints
    )


def test_surveys_are_for_closed_complaints():
    surveys = load_csv("surveys")
    status_events = load_csv("status_events")

    closed_complaints = set(
        status_events.loc[
            status_events["to_status"] == "CLOSED",
            "complaint_id",
        ]
    )

    survey_complaints = set(
        surveys["complaint_id"]
    )

    assert survey_complaints.issubset(
        closed_complaints
    )


def test_ground_truth_contains_six_deliberate_anomalies():
    ground_truth = pd.read_csv(
        GROUND_TRUTH_DIR / "ground_truth.csv"
    )

    assert len(ground_truth) == 6

    expected_issue_types = {
        "COMPLAINT_WITHOUT_CUSTOMER",
        "RESOLUTION_BEFORE_COMPLAINT",
        "SLA_PAUSE_ERROR",
        "REPEAT_ISSUE_NOT_LINKED",
        "SAFETY_WRONG_QUEUE",
        "SURVEY_BEFORE_CLOSURE",
    }

    actual_issue_types = set(
        ground_truth["issue_type"]
    )

    assert actual_issue_types == expected_issue_types