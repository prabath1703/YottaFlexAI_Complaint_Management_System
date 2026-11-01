import json
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data" / "output"
GROUND_TRUTH_FILE = ROOT / "data" / "ground_truth" / "ground_truth.csv"
REPORT_FILE = DATA_DIR / "validation_report.json"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    return {
        "customers": pd.read_csv(DATA_DIR / "customers.csv"),
        "products": pd.read_csv(DATA_DIR / "products.csv"),
        "categories": pd.read_csv(DATA_DIR / "categories.csv"),
        "orders": pd.read_csv(DATA_DIR / "orders.csv"),
        "complaints": pd.read_csv(DATA_DIR / "complaints.csv"),
        "assignments": pd.read_csv(DATA_DIR / "assignments.csv"),
        "sla_clocks": pd.read_csv(DATA_DIR / "sla_clocks.csv"),
        "messages": pd.read_csv(DATA_DIR / "complaint_messages.csv"),
        "status_events": pd.read_csv(DATA_DIR / "status_events.csv"),
        "resolutions": pd.read_csv(DATA_DIR / "resolutions.csv"),
        "surveys": pd.read_csv(DATA_DIR / "surveys.csv"),
        "ground_truth": pd.read_csv(GROUND_TRUTH_FILE),
    }


# ============================================================
# RESULT HELPER
# ============================================================

def add_result(results, check_name, passed, details, errors_found=0):
    results.append(
        {
            "check": check_name,
            "status": "PASS" if passed else "FAIL",
            "errors_found": int(errors_found),
            "details": details,
        }
    )


# ============================================================
# 1. PRIMARY KEYS
# ============================================================

def validate_primary_keys(data, results):

    primary_keys = {
        "customers": "customer_id",
        "products": "product_id",
        "categories": "category_id",
        "orders": "order_id",
        "complaints": "complaint_id",
        "assignments": "assignment_id",
        "sla_clocks": "sla_id",
        "messages": "message_id",
        "status_events": "event_id",
        "resolutions": "resolution_id",
        "surveys": "survey_id",
    }

    for table_name, pk in primary_keys.items():

        df = data[table_name]

        duplicate_count = int(df[pk].duplicated().sum())
        null_count = int(df[pk].isna().sum())

        passed = duplicate_count == 0 and null_count == 0

        add_result(
            results,
            f"PK: {table_name}.{pk}",
            passed,
            (
                f"Rows={len(df)}, "
                f"duplicates={duplicate_count}, "
                f"nulls={null_count}"
            ),
            duplicate_count + null_count,
        )


# ============================================================
# 2. FOREIGN KEYS
# ============================================================

def validate_foreign_keys(data, results):

    relationships = [
        ("orders", "customer_id", "customers", "customer_id"),
        ("orders", "product_id", "products", "product_id"),
        ("complaints", "order_id", "orders", "order_id"),
        ("complaints", "product_id", "products", "product_id"),
        ("complaints", "category_id", "categories", "category_id"),
        ("assignments", "complaint_id", "complaints", "complaint_id"),
        ("sla_clocks", "complaint_id", "complaints", "complaint_id"),
        ("messages", "complaint_id", "complaints", "complaint_id"),
        ("status_events", "complaint_id", "complaints", "complaint_id"),
        ("resolutions", "complaint_id", "complaints", "complaint_id"),
        ("surveys", "complaint_id", "complaints", "complaint_id"),
    ]

    for child_table, child_column, parent_table, parent_column in relationships:

        child_df = data[child_table]
        parent_df = data[parent_table]

        valid_parent_ids = set(
            parent_df[parent_column].dropna()
        )

        non_null_values = child_df[child_column].dropna()

        invalid_count = int(
            (~non_null_values.isin(valid_parent_ids)).sum()
        )

        passed = invalid_count == 0

        add_result(
            results,
            (
                f"FK: {child_table}.{child_column} "
                f"-> {parent_table}.{parent_column}"
            ),
            passed,
            f"Invalid references={invalid_count}",
            invalid_count,
        )


# ============================================================
# 3. REQUIRED FIELDS
# ============================================================

def validate_required_fields(data, results):

    required_fields = {
        "customers": [
            "customer_id",
            "name",
            "email",
        ],
        "products": [
            "product_id",
            "product_name",
            "unit_price",
        ],
        "orders": [
            "order_id",
            "customer_id",
            "product_id",
            "order_date",
        ],
        "complaints": [
            "complaint_id",
            "created_at",
            "category",
            "severity",
            "priority",
        ],
        "assignments": [
            "assignment_id",
            "complaint_id",
            "team",
            "agent_id",
        ],
        "sla_clocks": [
            "sla_id",
            "complaint_id",
            "priority",
            "sla_deadline",
        ],
    }

    for table_name, columns in required_fields.items():

        df = data[table_name]

        missing_count = 0
        missing_details = []

        for column in columns:

            if column not in df.columns:

                missing_count += len(df)

                missing_details.append(
                    f"{column}: COLUMN_MISSING"
                )

                continue

            null_count = int(df[column].isna().sum())

            if null_count > 0:

                missing_count += null_count

                missing_details.append(
                    f"{column}: {null_count} nulls"
                )

        passed = missing_count == 0

        add_result(
            results,
            f"Required fields: {table_name}",
            passed,
            (
                "All required fields populated"
                if passed
                else "; ".join(missing_details)
            ),
            missing_count,
        )


# ============================================================
# 4. ENUMS
# ============================================================

def validate_enums(data, results):

    allowed_values = {
        "complaints": {
            "priority": {"P1", "P2", "P3", "P4"},
            "severity": {
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
            },
            "channel": {
                "EMAIL",
                "PHONE",
                "CHAT",
                "WEB",
            },
        },
        "assignments": {
            "team": {
                "CUSTOMER_SUPPORT",
                "LOGISTICS",
                "PAYMENTS",
                "REFUNDS",
                "PRODUCT_SAFETY",
            },
        },
    }

    for table_name, columns in allowed_values.items():

        df = data[table_name]

        for column, allowed in columns.items():

            invalid_count = int(
                (~df[column].isin(allowed)).sum()
            )

            passed = invalid_count == 0

            add_result(
                results,
                f"ENUM: {table_name}.{column}",
                passed,
                f"Invalid values={invalid_count}",
                invalid_count,
            )


# ============================================================
# 5. ORDER TOTALS
# ============================================================

def validate_order_totals(data, results):

    orders = data["orders"]

    calculated_total = (
        orders["quantity"] * orders["unit_price"]
    )

    mismatch = (
        (calculated_total - orders["order_total"])
        .abs()
        > 0.01
    )

    error_count = int(mismatch.sum())

    add_result(
        results,
        "Order total reconciliation",
        error_count == 0,
        f"Mismatched totals={error_count}",
        error_count,
    )


# ============================================================
# 6. DATE / LIFECYCLE VALIDATION
# ============================================================

def validate_dates(data, results):

    complaints = data["complaints"].copy()
    resolutions = data["resolutions"].copy()
    surveys = data["surveys"].copy()
    status_events = data["status_events"].copy()

    complaints["created_at"] = pd.to_datetime(
        complaints["created_at"]
    )

    resolutions["resolved_at"] = pd.to_datetime(
        resolutions["resolved_at"]
    )

    surveys["survey_sent_at"] = pd.to_datetime(
        surveys["survey_sent_at"]
    )

    status_events["event_time"] = pd.to_datetime(
        status_events["event_time"]
    )

    complaint_times = complaints.set_index(
        "complaint_id"
    )["created_at"]

    # --------------------------------------------------------
    # Resolution after complaint
    # --------------------------------------------------------

    resolution_errors = 0

    for _, row in resolutions.iterrows():

        complaint_time = complaint_times.get(
            row["complaint_id"]
        )

        if (
            complaint_time is not None
            and row["resolved_at"] < complaint_time
        ):
            resolution_errors += 1

    add_result(
        results,
        "Resolution after complaint",
        resolution_errors == 0,
        f"Invalid resolution timestamps={resolution_errors}",
        resolution_errors,
    )

    # --------------------------------------------------------
    # Survey after closure
    # --------------------------------------------------------

    closure_times = (
    status_events[
        status_events["to_status"] == "CLOSED"
    ]
    .groupby("complaint_id")["event_time"]
    .max()
)

    survey_errors = 0

    for _, row in surveys.iterrows():

        closure_time = closure_times.get(
            row["complaint_id"]
        )

        if closure_time is None:
            continue

        if row["survey_sent_at"] < closure_time:
            survey_errors += 1

    add_result(
        results,
        "Survey after complaint closure",
        survey_errors == 0,
        f"Surveys before closure={survey_errors}",
        survey_errors,
    )


# ============================================================
# 7. REPEAT COMPLAINT LINKAGE
# ============================================================

def validate_repeat_complaints(data, results):

    complaints = data["complaints"]

    if "related_complaint_id" not in complaints.columns:

        add_result(
            results,
            "Repeat complaint linkage",
            False,
            "related_complaint_id column missing",
            1,
        )

        return

    add_result(
        results,
        "Repeat complaint linkage",
        True,
        "Repeat complaint relationship field present",
        0,
    )


# ============================================================
# 8. SAFETY ASSIGNMENT
# ============================================================

def validate_safety_assignment(data, results):

    complaints = data["complaints"]
    assignments = data["assignments"]

    merged = complaints[
        [
            "complaint_id",
            "safety_issue_flag",
            "category",
            "priority",
        ]
    ].merge(
        assignments[
            [
                "complaint_id",
                "team",
            ]
        ],
        on="complaint_id",
        how="left",
    )

    safety_cases = merged[
        (
            merged["safety_issue_flag"] == True
        )
        |
        (
            merged["category"] == "PRODUCT_SAFETY"
        )
    ]

    errors = int(
        (
            safety_cases["team"]
            != "PRODUCT_SAFETY"
        ).sum()
    )

    add_result(
        results,
        "Safety complaint assignment",
        errors == 0,
        f"Safety complaints assigned to wrong team={errors}",
        errors,
    )


# ============================================================
# 9. SLA
# ============================================================

def validate_sla(data, results):

    sla = data["sla_clocks"]

    errors = 0

    for _, row in sla.iterrows():

        paused = row.get(
            "paused_duration_minutes",
            0,
        )

        elapsed = row.get(
            "elapsed_duration_minutes",
            0,
        )

        if pd.isna(paused):
            paused = 0

        if pd.isna(elapsed):
            elapsed = 0

        if paused > 0 and elapsed == 0:
            errors += 1

    add_result(
        results,
        "SLA pause calculation",
        errors == 0,
        f"Suspicious SLA pause records={errors}",
        errors,
    )


# ============================================================
# 10. GROUND TRUTH
# ============================================================

def validate_ground_truth(data, results):

    ground_truth = data["ground_truth"]

    expected_anomalies = len(ground_truth)

    detected = 0

    complaints = data["complaints"]
    customers = data["customers"]
    resolutions = data["resolutions"]
    sla_clocks = data["sla_clocks"]
    assignments = data["assignments"]
    surveys = data["surveys"]
    status_events = data["status_events"]

    # --------------------------------------------------------
    # ANOMALY 1: invalid customer reference
    # --------------------------------------------------------

    valid_customer_ids = set(
        customers["customer_id"].dropna()
    )

    invalid_customer_cases = complaints[
        complaints["customer_id"].notna()
        &
        ~complaints["customer_id"].isin(valid_customer_ids)
    ]

    if len(invalid_customer_cases) > 0:
        detected += 1

    # --------------------------------------------------------
    # ANOMALY 2: resolution before complaint
    # --------------------------------------------------------

    complaint_times = {
        row["complaint_id"]: pd.to_datetime(
            row["created_at"]
        )
        for _, row in complaints.iterrows()
    }

    date_errors = 0

    for _, row in resolutions.iterrows():

        complaint_time = complaint_times.get(
            row["complaint_id"]
        )

        resolution_time = pd.to_datetime(
            row["resolved_at"]
        )

        if (
            complaint_time is not None
            and resolution_time < complaint_time
        ):
            date_errors += 1

    if date_errors > 0:
        detected += 1

    # --------------------------------------------------------
    # ANOMALY 3: incorrect SLA pause
    # --------------------------------------------------------

    sla_errors = sla_clocks[
        (
            sla_clocks["paused_duration_minutes"] > 0
        )
        &
        (
            sla_clocks["elapsed_duration_minutes"] == 0
        )
    ]

    if len(sla_errors) > 0:
        detected += 1

    # --------------------------------------------------------
    # ANOMALY 4: repeat issue not linked
    # --------------------------------------------------------

    repeat_errors = complaints[
        (
            complaints["repeat_complaint_flag"] == True
        )
        &
        (
            complaints["related_complaint_id"].isna()
        )
    ]

    if len(repeat_errors) > 0:
        detected += 1

    # --------------------------------------------------------
    # ANOMALY 5: safety wrong queue
    # --------------------------------------------------------

    safety_merged = complaints.merge(
        assignments[
            [
                "complaint_id",
                "team",
            ]
        ],
        on="complaint_id",
        how="left",
    )

    safety_errors = safety_merged[
        (
            safety_merged["safety_issue_flag"] == True
        )
        &
        (
            safety_merged["team"] != "PRODUCT_SAFETY"
        )
    ]

    if len(safety_errors) > 0:
        detected += 1

    # --------------------------------------------------------
    # ANOMALY 6: survey before closure
    # --------------------------------------------------------

    status_events = status_events.copy()
    status_events["event_time"] = pd.to_datetime(
        status_events["event_time"]
    )

    surveys = surveys.copy()
    surveys["survey_sent_at"] = pd.to_datetime(
        surveys["survey_sent_at"]
    )

    closure_times = (
    status_events[
        status_events["to_status"] == "CLOSED"
    ]
    .groupby("complaint_id")["event_time"]
    .max()
)

    survey_errors = 0

    for _, row in surveys.iterrows():

        closure_time = closure_times.get(
            row["complaint_id"]
        )

        if closure_time is None:
            continue

        if row["survey_sent_at"] < closure_time:
            survey_errors += 1

    if survey_errors > 0:
        detected += 1

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    passed = detected == expected_anomalies

    add_result(
        results,
        "Ground-truth anomaly detection",
        passed,
        (
            f"Expected={expected_anomalies}, "
            f"Detected={detected}"
        ),
        abs(expected_anomalies - detected),
    )


# ============================================================
# MAIN
# ============================================================

def run_validation():

    print("=" * 60)
    print("COMPLAINT MANAGEMENT DATA VALIDATION")
    print("=" * 60)

    data = load_data()

    results = []

    validate_primary_keys(data, results)
    validate_foreign_keys(data, results)
    validate_required_fields(data, results)
    validate_enums(data, results)
    validate_order_totals(data, results)
    validate_dates(data, results)
    validate_repeat_complaints(data, results)
    validate_safety_assignment(data, results)
    validate_sla(data, results)
    validate_ground_truth(data, results)

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    total_checks = len(results)

    passed_checks = sum(
        r["status"] == "PASS"
        for r in results
    )

    failed_checks = total_checks - passed_checks

    total_errors = sum(
        r["errors_found"]
        for r in results
    )

    report = {
        "summary": {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "total_errors": int(total_errors),
        },
        "checks": results,
    }

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
        )

    # --------------------------------------------------------
    # PRINT RESULTS
    # --------------------------------------------------------

    print()

    for result in results:

        symbol = (
            "PASS"
            if result["status"] == "PASS"
            else "FAIL"
        )

        print(
            f"[{symbol}] "
            f"{result['check']} "
            f"-> {result['details']}"
        )

    print()
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    print(
        f"Total checks : {total_checks}"
    )

    print(
        f"Passed       : {passed_checks}"
    )

    print(
        f"Failed       : {failed_checks}"
    )

    print(
        f"Total errors : {total_errors}"
    )

    print()
    print(
        f"Report saved: {REPORT_FILE}"
    )


if __name__ == "__main__":
    run_validation()