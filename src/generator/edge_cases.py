from datetime import datetime, timedelta


def inject_anomalies(
    customers,
    complaints,
    assignments,
    sla_clocks,
    resolutions,
    surveys,
    status_events
):

    ground_truth = []

    # ==================================================
    # 1. COMPLAINT WITHOUT CUSTOMER
    # ==================================================

    complaint = complaints[0]

    complaint["customer_id"] = "CUS-999999"

    ground_truth.append({
        "anomaly_id": "ANOM-001",
        "complaint_id": complaint["complaint_id"],
        "issue_type": "COMPLAINT_WITHOUT_CUSTOMER",
        "severity": "HIGH",
        "expected_result": "INVALID_FOREIGN_KEY",
        "description": (
            "Complaint references a customer ID "
            "that does not exist."
        )
    })

    # ==================================================
    # 2. RESOLUTION BEFORE COMPLAINT
    # ==================================================

    if resolutions:

        resolution = resolutions[0]

        complaint_id = resolution["complaint_id"]

        complaint_lookup = {
            c["complaint_id"]: c
            for c in complaints
        }

        complaint = complaint_lookup[complaint_id]

        complaint_time = datetime.strptime(
            complaint["created_at"],
            "%Y-%m-%d %H:%M:%S"
        )

        invalid_resolution_time = (
            complaint_time - timedelta(hours=2)
        )

        resolution["resolved_at"] = (
            invalid_resolution_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        ground_truth.append({
            "anomaly_id": "ANOM-002",
            "complaint_id": complaint_id,
            "issue_type": "RESOLUTION_BEFORE_COMPLAINT",
            "severity": "HIGH",
            "expected_result": "INVALID_DATE_ORDER",
            "description": (
                "Resolution timestamp occurs before "
                "complaint creation."
            )
        })

    # ==================================================
    # 3. SLA CLOCK PAUSES INCORRECTLY
    # ==================================================

    if sla_clocks:

        sla = sla_clocks[0]

        sla["paused_duration_minutes"] = 120

        # Deliberately leave elapsed duration unchanged.
        sla["elapsed_duration_minutes"] = 0

        ground_truth.append({
            "anomaly_id": "ANOM-003",
            "complaint_id": sla["complaint_id"],
            "issue_type": "SLA_PAUSE_ERROR",
            "severity": "MEDIUM",
            "expected_result": "INVALID_SLA_CALCULATION",
            "description": (
                "SLA has a pause duration but the "
                "elapsed duration was not adjusted."
            )
        })

    # ==================================================
    # 4. REPEAT COMPLAINT NOT LINKED
    # ==================================================

    repeat_complaint = complaints[1]

    repeat_complaint["repeat_complaint_flag"] = True

    # We intentionally don't create a related complaint link.
    repeat_complaint["related_complaint_id"] = None

    ground_truth.append({
        "anomaly_id": "ANOM-004",
        "complaint_id": repeat_complaint[
            "complaint_id"
        ],
        "issue_type": "REPEAT_ISSUE_NOT_LINKED",
        "severity": "MEDIUM",
        "expected_result": "MISSING_PARENT_COMPLAINT",
        "description": (
            "Complaint is marked as a repeat issue "
            "but has no related complaint reference."
        )
    })

    # ==================================================
    # 5. CRITICAL SAFETY ISSUE WRONG QUEUE
    # ==================================================

    safety_complaint = None

    for c in complaints:

        if c["safety_issue_flag"]:

            safety_complaint = c
            break

    if safety_complaint:

        safety_complaint["priority"] = "P1"

        for assignment in assignments:

            if (
                assignment["complaint_id"]
                == safety_complaint["complaint_id"]
            ):

                # Deliberately wrong team.
                assignment["team"] = "CUSTOMER_SUPPORT"

                assignment["assignment_reason"] = (
                    "DELIBERATE ANOMALY: "
                    "Critical safety complaint "
                    "assigned to wrong queue."
                )

                break

        ground_truth.append({
            "anomaly_id": "ANOM-005",
            "complaint_id": safety_complaint[
                "complaint_id"
            ],
            "issue_type": "SAFETY_WRONG_QUEUE",
            "severity": "CRITICAL",
            "expected_result": "INVALID_ASSIGNMENT",
            "description": (
                "Critical safety complaint was assigned "
                "to CUSTOMER_SUPPORT instead of "
                "PRODUCT_SAFETY."
            )
        })

    # ==================================================
    # 6. SURVEY BEFORE CLOSURE
    # ==================================================

    if surveys:

        survey = surveys[0]

        complaint_id = survey["complaint_id"]

        complaint_lookup = {
            c["complaint_id"]: c
            for c in complaints
        }

        complaint = complaint_lookup[complaint_id]

        complaint_time = datetime.strptime(
            complaint["created_at"],
            "%Y-%m-%d %H:%M:%S"
        )

        invalid_survey_time = (
            complaint_time + timedelta(minutes=10)
        )

        survey["survey_sent_at"] = (
            invalid_survey_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        ground_truth.append({
            "anomaly_id": "ANOM-006",
            "complaint_id": complaint_id,
            "issue_type": "SURVEY_BEFORE_CLOSURE",
            "severity": "HIGH",
            "expected_result": "INVALID_LIFECYCLE",
            "description": (
                "Survey was sent before complaint closure."
            )
        })

    return ground_truth