from datetime import datetime, timedelta


# --------------------------------------------------
# PRIORITY RULE
# --------------------------------------------------

def calculate_priority(
    severity,
    sentiment,
    safety_issue,
    repeat_complaint,
    order_value
):
    """
    Calculate complaint priority using business rules.

    P1 = Critical / Safety
    P2 = High severity / Very negative / High-value repeat
    P3 = Medium
    P4 = Low
    """

    # Rule 1: Safety issues are always highest priority
    if safety_issue:
        return "P1"

    # Rule 2: Critical severity
    if severity == "CRITICAL":
        return "P1"

    # Rule 3: High severity
    if severity == "HIGH":
        return "P2"

    # Rule 4: Very negative customer sentiment
    if sentiment == "VERY_NEGATIVE":
        return "P2"

    # Rule 5: Repeat complaint involving high-value order
    if repeat_complaint and order_value >= 25000:
        return "P2"

    # Rule 6: Medium severity
    if severity == "MEDIUM":
        return "P3"

    # Default
    return "P4"


# --------------------------------------------------
# TEAM ASSIGNMENT
# --------------------------------------------------

def assign_team(category, safety_issue):

    if safety_issue or category == "PRODUCT_SAFETY":
        return "PRODUCT_SAFETY"

    if category == "DELIVERY":
        return "LOGISTICS"

    if category == "PAYMENT" or category == "BILLING":
        return "PAYMENTS"

    if category == "REFUND":
        return "REFUNDS"

    return "CUSTOMER_SUPPORT"


# --------------------------------------------------
# AGENTS
# --------------------------------------------------

AGENTS = {
    "CUSTOMER_SUPPORT": [
        "CS-001",
        "CS-002",
        "CS-003",
        "CS-004"
    ],

    "LOGISTICS": [
        "LG-001",
        "LG-002",
        "LG-003"
    ],

    "PAYMENTS": [
        "PY-001",
        "PY-002",
        "PY-003"
    ],

    "REFUNDS": [
        "RF-001",
        "RF-002",
        "RF-003"
    ],

    "PRODUCT_SAFETY": [
        "PS-001",
        "PS-002"
    ]
}


def assign_agent(team, rng):

    return rng.choice(AGENTS[team])


# --------------------------------------------------
# SLA
# --------------------------------------------------

SLA_HOURS = {
    "P1": 4,
    "P2": 12,
    "P3": 24,
    "P4": 72
}


def calculate_sla(priority, complaint_time):

    if isinstance(complaint_time, str):
        complaint_time = datetime.strptime(
            complaint_time,
            "%Y-%m-%d %H:%M:%S"
        )

    hours = SLA_HOURS[priority]

    deadline = complaint_time + timedelta(
        hours=hours
    )

    return {
        "sla_hours": hours,
        "sla_deadline": deadline.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }