from datetime import datetime, timedelta


# --------------------------------------------------
# COMPLAINT MESSAGE GENERATION
# --------------------------------------------------

def generate_messages(
    complaints,
    count,
    rng
):

    messages = []

    sender_types = [
        "CUSTOMER",
        "AGENT",
        "SYSTEM"
    ]

    channels = [
        "EMAIL",
        "PHONE",
        "CHAT",
        "WEB"
    ]

    message_templates = {
        "CUSTOMER": [
            "I would like an update on my complaint.",
            "I am still waiting for this issue to be resolved.",
            "Please help me resolve this issue.",
            "I need assistance with my order."
        ],

        "AGENT": [
            "We are reviewing your complaint.",
            "Our team is investigating the issue.",
            "We have received your request and will assist you.",
            "The issue has been escalated to the appropriate team."
        ],

        "SYSTEM": [
            "Complaint status was updated.",
            "SLA clock was started.",
            "Complaint was assigned to an agent."
        ]
    }

    # Keep at least some messages for every complaint.
    base_messages = min(count, len(complaints))

    message_number = 1

    for complaint in complaints:

        if message_number > count:
            break

        complaint_time = datetime.strptime(
            complaint["created_at"],
            "%Y-%m-%d %H:%M:%S"
        )

        sender_type = rng.choice(sender_types)

        message_time = complaint_time + timedelta(
            minutes=rng.randint(5, 120)
        )

        messages.append({
            "message_id": (
                f"MSG-{complaint['complaint_id']}-"
                f"{message_number:03d}"
            ),
            "complaint_id": complaint[
                "complaint_id"
            ],
            "sender_type": sender_type,
            "message_time": message_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "message_text": rng.choice(
                message_templates[sender_type]
            ),
            "channel": rng.choice(channels)
        })

        message_number += 1

    # Additional messages until requested count.
    complaint_index = 0

    while message_number <= count:

        complaint = complaints[
            complaint_index % len(complaints)
        ]

        complaint_time = datetime.strptime(
            complaint["created_at"],
            "%Y-%m-%d %H:%M:%S"
        )

        sender_type = rng.choice(sender_types)

        message_time = complaint_time + timedelta(
            minutes=rng.randint(10, 300)
        )

        messages.append({
            "message_id": (
                f"MSG-{complaint['complaint_id']}-"
                f"{message_number:03d}"
            ),
            "complaint_id": complaint[
                "complaint_id"
            ],
            "sender_type": sender_type,
            "message_time": message_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "message_text": rng.choice(
                message_templates[sender_type]
            ),
            "channel": rng.choice(channels)
        })

        message_number += 1
        complaint_index += 1

    return messages


# --------------------------------------------------
# STATUS EVENT HISTORY
# --------------------------------------------------

def generate_status_events(
    complaints,
    rng
):

    status_events = []

    for complaint in complaints:

        complaint_time = datetime.strptime(
            complaint["created_at"],
            "%Y-%m-%d %H:%M:%S"
        )

        complaint_id = complaint["complaint_id"]

        # CREATED
        status_events.append({
            "event_id": f"EVT-{complaint_id}-001",
            "complaint_id": complaint_id,
            "event_type": "STATUS_CHANGE",
            "from_status": None,
            "to_status": "OPEN",
            "event_time": complaint_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "performed_by": "SYSTEM"
        })

        # ASSIGNED
        assigned_time = complaint_time + timedelta(
            minutes=rng.randint(1, 30)
        )

        status_events.append({
            "event_id": f"EVT-{complaint_id}-002",
            "complaint_id": complaint_id,
            "event_type": "STATUS_CHANGE",
            "from_status": "OPEN",
            "to_status": "ASSIGNED",
            "event_time": assigned_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "performed_by": "SYSTEM"
        })

        # IN PROGRESS
        progress_time = assigned_time + timedelta(
            minutes=rng.randint(5, 60)
        )

        status_events.append({
            "event_id": f"EVT-{complaint_id}-003",
            "complaint_id": complaint_id,
            "event_type": "STATUS_CHANGE",
            "from_status": "ASSIGNED",
            "to_status": "IN_PROGRESS",
            "event_time": progress_time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "performed_by": "AGENT"
        })

        # Most complaints reach resolution.
        if rng.random() < 0.90:

            resolved_time = progress_time + timedelta(
                hours=rng.randint(1, 48)
            )

            status_events.append({
                "event_id": f"EVT-{complaint_id}-004",
                "complaint_id": complaint_id,
                "event_type": "STATUS_CHANGE",
                "from_status": "IN_PROGRESS",
                "to_status": "RESOLVED",
                "event_time": resolved_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "performed_by": "AGENT"
            })

            closed_time = resolved_time + timedelta(
                minutes=rng.randint(10, 120)
            )

            status_events.append({
                "event_id": f"EVT-{complaint_id}-005",
                "complaint_id": complaint_id,
                "event_type": "STATUS_CHANGE",
                "from_status": "RESOLVED",
                "to_status": "CLOSED",
                "event_time": closed_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "performed_by": "SYSTEM"
            })

            complaint["status"] = "CLOSED"

        else:

            complaint["status"] = "IN_PROGRESS"

    return status_events


# --------------------------------------------------
# RESOLUTION
# --------------------------------------------------

def generate_resolutions(
    complaints,
    status_events,
    rng
):

    resolutions = []

    resolution_types = [
        "REFUND",
        "REPLACEMENT",
        "EXPLANATION",
        "CREDIT",
        "CORRECTION",
        "NO_ACTION"
    ]

    closed_events = {}

    for event in status_events:

        if event["to_status"] == "CLOSED":
            closed_events[
                event["complaint_id"]
            ] = event["event_time"]

    for complaint in complaints:

        complaint_id = complaint["complaint_id"]

        if complaint_id not in closed_events:
            continue

        resolved_events = [
            event
            for event in status_events
            if (
                event["complaint_id"] == complaint_id
                and event["to_status"] == "RESOLVED"
            )
        ]

        if not resolved_events:
            continue

        resolved_at = resolved_events[-1]["event_time"]

        resolution_type = rng.choice(
            resolution_types
        )

        refund_amount = 0.0

        if resolution_type == "REFUND":
            refund_amount = round(
                rng.uniform(100, 25000),
                2
            )

        resolutions.append({
            "resolution_id": f"RES-{complaint_id}",
            "complaint_id": complaint_id,
            "resolution_type": resolution_type,
            "resolution_description": (
                f"Complaint resolved using "
                f"{resolution_type.lower()}."
            ),
            "resolved_at": resolved_at,
            "resolved_by": "AGENT",
            "refund_amount": refund_amount
        })

    return resolutions


# --------------------------------------------------
# POST-RESOLUTION SURVEY
# --------------------------------------------------

def generate_surveys(
    complaints,
    status_events,
    rng
):

    surveys = []

    closed_events = {}

    for event in status_events:

        if event["to_status"] == "CLOSED":
            closed_events[
                event["complaint_id"]
            ] = event["event_time"]

    for complaint in complaints:

        complaint_id = complaint["complaint_id"]

        if complaint_id not in closed_events:
            continue

        closed_time = datetime.strptime(
            closed_events[complaint_id],
            "%Y-%m-%d %H:%M:%S"
        )

        survey_sent = closed_time + timedelta(
            minutes=rng.randint(5, 60)
        )

        response_time = None
        rating = None
        feedback = None

        # Around 70% respond.
        if rng.random() < 0.70:

            response_time = survey_sent + timedelta(
                hours=rng.randint(1, 72)
            )

            rating = rng.randint(1, 5)

            feedback = rng.choice([
                "Issue resolved successfully.",
                "The response was helpful.",
                "Resolution took too long.",
                "Good support experience.",
                "The issue was only partially resolved."
            ])

        surveys.append({
            "survey_id": f"SRV-{complaint_id}",
            "complaint_id": complaint_id,
            "survey_sent_at": survey_sent.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "response_at": (
                response_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                if response_time
                else None
            ),
            "rating": rating,
            "feedback": feedback
        })

    return surveys