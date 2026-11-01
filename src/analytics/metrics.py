import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "data" / "output"
GROUND_TRUTH_DIR = BASE_DIR / "data" / "ground_truth"


def load_data():
    data = {}

    files = [
        "complaints",
        "assignments",
        "sla_clocks",
        "status_events",
        "resolutions",
        "surveys",
    ]

    for name in files:
        data[name] = pd.read_csv(OUTPUT_DIR / f"{name}.csv")

    ground_truth_path = GROUND_TRUTH_DIR / "ground_truth.csv"

    if ground_truth_path.exists():
        data["ground_truth"] = pd.read_csv(ground_truth_path)
    else:
        data["ground_truth"] = pd.DataFrame()

    return data


def calculate_metrics(data):
    complaints = data["complaints"]
    assignments = data["assignments"]
    sla_clocks = data["sla_clocks"]
    status_events = data["status_events"]
    resolutions = data["resolutions"]
    surveys = data["surveys"]
    ground_truth = data["ground_truth"]

    metrics = {}

    # ---------------------------------------------------------
    # 1. Complaint volume
    # ---------------------------------------------------------
    metrics["complaint_volume"] = {
        "total_complaints": int(len(complaints)),
        "by_category": (
            complaints["category"]
            .value_counts()
            .to_dict()
        ),
        "by_priority": (
            complaints["priority"]
            .value_counts()
            .to_dict()
        ),
        "by_channel": (
            complaints["channel"]
            .value_counts()
            .to_dict()
        ),
    }

    # ---------------------------------------------------------
    # 2. Complaint status
    # ---------------------------------------------------------
    metrics["complaint_status"] = (
        complaints["status"]
        .value_counts()
        .to_dict()
    )

    # ---------------------------------------------------------
    # 3. Assignment metrics
    # ---------------------------------------------------------
    metrics["assignment"] = {
        "total_assignments": int(len(assignments)),
        "by_team": (
            assignments["team"]
            .value_counts()
            .to_dict()
        ),
    }

    # ---------------------------------------------------------
    # 4. SLA metrics
    # ---------------------------------------------------------
    sla_metrics = {
        "total_sla_clocks": int(len(sla_clocks)),
        "by_priority": (
            sla_clocks["priority"]
            .value_counts()
            .to_dict()
        ),
    }

    # Find CLOSED events to determine actual closure time.
    closure_events = status_events[
        status_events["to_status"] == "CLOSED"
    ].copy()

    if not closure_events.empty:
        closure_events["event_time"] = pd.to_datetime(
            closure_events["event_time"]
        )

        closure_times = (
            closure_events
            .groupby("complaint_id")["event_time"]
            .max()
        )

        sla_clocks["sla_deadline"] = pd.to_datetime(
            sla_clocks["sla_deadline"]
        )

        sla_clocks["start_time"] = pd.to_datetime(
            sla_clocks["start_time"]
        )

        sla_clocks["closure_time"] = (
            sla_clocks["complaint_id"]
            .map(closure_times)
        )

        completed_sla = sla_clocks[
            sla_clocks["closure_time"].notna()
        ].copy()

        if not completed_sla.empty:
            completed_sla["sla_met"] = (
                completed_sla["closure_time"]
                <= completed_sla["sla_deadline"]
            )

            sla_metrics["completed_sla"] = int(
                len(completed_sla)
            )

            sla_metrics["sla_met"] = int(
                completed_sla["sla_met"].sum()
            )

            sla_metrics["sla_breached"] = int(
                (~completed_sla["sla_met"]).sum()
            )

            sla_metrics["sla_compliance_percentage"] = round(
                completed_sla["sla_met"].mean() * 100,
                2,
            )

    metrics["sla"] = sla_metrics

    # ---------------------------------------------------------
    # 5. Resolution metrics
    # ---------------------------------------------------------
    metrics["resolution"] = {
        "total_resolutions": int(len(resolutions)),
        "by_resolution_type": (
            resolutions["resolution_type"]
            .value_counts()
            .to_dict()
        ),
    }

    # ---------------------------------------------------------
    # 6. Survey metrics
    # ---------------------------------------------------------
    survey_metrics = {
        "total_surveys": int(len(surveys)),
    }

    if "rating" in surveys.columns:
        ratings = pd.to_numeric(
            surveys["rating"],
            errors="coerce"
        )

        valid_ratings = ratings.dropna()

        if not valid_ratings.empty:
            survey_metrics["response_count"] = int(
                len(valid_ratings)
            )

            survey_metrics["average_rating"] = round(
                valid_ratings.mean(),
                2,
            )

            survey_metrics["rating_distribution"] = (
                valid_ratings
                .value_counts()
                .sort_index()
                .to_dict()
            )

    metrics["survey"] = survey_metrics

    # ---------------------------------------------------------
    # 7. Ground-truth anomaly metrics
    # ---------------------------------------------------------
    metrics["anomalies"] = {
        "total_known_anomalies": int(len(ground_truth)),
    }

    if not ground_truth.empty:
        metrics["anomalies"]["by_issue_type"] = (
            ground_truth["issue_type"]
            .value_counts()
            .to_dict()
        )

    return metrics


def save_metrics(metrics):
    output_path = OUTPUT_DIR / "metrics_summary.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            metrics,
            file,
            indent=4,
            default=str,
        )

    return output_path


def main():
    data = load_data()
    metrics = calculate_metrics(data)
    output_path = save_metrics(metrics)

    print("=" * 60)
    print("METRICS GENERATION COMPLETE")
    print("=" * 60)

    print(f"Total complaints : {metrics['complaint_volume']['total_complaints']}")
    print(f"Total assignments: {metrics['assignment']['total_assignments']}")
    print(f"Total resolutions: {metrics['resolution']['total_resolutions']}")
    print(f"Total surveys    : {metrics['survey']['total_surveys']}")
    print(
        f"Known anomalies  : "
        f"{metrics['anomalies']['total_known_anomalies']}"
    )

    if "sla_compliance_percentage" in metrics["sla"]:
        print(
            f"SLA compliance   : "
            f"{metrics['sla']['sla_compliance_percentage']}%"
        )

    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    main()