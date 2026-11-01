from datetime import datetime

from .business_rules import (
    calculate_priority,
    assign_team,
    assign_agent,
    calculate_sla
)


def apply_business_rules(
    complaints,
    orders,
    rng
):

    order_lookup = {
        order["order_id"]: order
        for order in orders
    }

    assignments = []
    sla_clocks = []

    for complaint in complaints:

        order_id = complaint["order_id"]

        order_value = 0

        if order_id and order_id in order_lookup:
            order_value = order_lookup[
                order_id
            ]["order_total"]

        # ------------------------------------------
        # PRIORITY
        # ------------------------------------------

        priority = calculate_priority(
            severity=complaint["severity"],
            sentiment=complaint["sentiment"],
            safety_issue=complaint["safety_issue_flag"],
            repeat_complaint=complaint[
                "repeat_complaint_flag"
            ],
            order_value=order_value
        )

        complaint["priority"] = priority

        # ------------------------------------------
        # TEAM
        # ------------------------------------------

        team = assign_team(
            complaint["category"],
            complaint["safety_issue_flag"]
        )

        # ------------------------------------------
        # AGENT
        # ------------------------------------------

        agent = assign_agent(
            team,
            rng
        )

        assigned_at = complaint["created_at"]

        assignments.append({
            "assignment_id": (
                f"ASN-{complaint['complaint_id']}"
            ),
            "complaint_id": complaint[
                "complaint_id"
            ],
            "team": team,
            "agent_id": agent,
            "assigned_at": assigned_at,
            "unassigned_at": None,
            "assignment_reason": (
                f"Category={complaint['category']}; "
                f"Priority={priority}"
            )
        })

        # ------------------------------------------
        # SLA
        # ------------------------------------------

        sla = calculate_sla(
            priority,
            complaint["created_at"]
        )

        sla_clocks.append({
            "sla_id": (
                f"SLA-{complaint['complaint_id']}"
            ),
            "complaint_id": complaint[
                "complaint_id"
            ],
            "priority": priority,
            "start_time": complaint[
                "created_at"
            ],
            "sla_hours": sla["sla_hours"],
            "sla_deadline": sla[
                "sla_deadline"
            ],
            "paused_duration_minutes": 0,
            "elapsed_duration_minutes": 0,
            "sla_status": "OPEN"
        })

    return complaints, assignments, sla_clocks