from datetime import datetime
import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Complaint, Assignment


TEAM_AGENTS = {
    "CUSTOMER_SUPPORT": ["CS-001", "CS-002", "CS-003", "CS-004"],
    "LOGISTICS": ["LG-001", "LG-002", "LG-003"],
    "PAYMENTS": ["PY-001", "PY-002", "PY-003"],
    "REFUNDS": ["RF-001", "RF-002", "RF-003"],
    "PRODUCT_SAFETY": ["PS-001", "PS-002"],
}


def determine_team(category: str, safety_issue: bool) -> str:
    if safety_issue or category == "PRODUCT_SAFETY":
        return "PRODUCT_SAFETY"

    if category == "DELIVERY":
        return "LOGISTICS"

    if category in ("PAYMENT", "BILLING"):
        return "PAYMENTS"

    if category == "REFUND":
        return "REFUNDS"

    return "CUSTOMER_SUPPORT"


def assign_complaint(
    db: Session,
    complaint_id: str,
    assigned_by: str = "SYSTEM",
    requested_team: str | None = None,
    requested_agent: str | None = None,
):
    complaint = db.query(Complaint).filter(
        Complaint.complaint_id == complaint_id
    ).first()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    team = requested_team or determine_team(
        complaint.category,
        bool(complaint.safety_issue_flag),
    )

    if team not in TEAM_AGENTS:
        raise HTTPException(status_code=400, detail="Invalid team")

    # Safety complaints must always go to the safety team.
    if complaint.safety_issue_flag and team != "PRODUCT_SAFETY":
        raise HTTPException(
            status_code=400,
            detail="Safety complaints must be assigned to PRODUCT_SAFETY",
        )

    if requested_agent:
        if requested_agent not in TEAM_AGENTS[team]:
            raise HTTPException(
                status_code=400,
                detail="Agent does not belong to the selected team",
            )
        agent = requested_agent
    else:
        # Simple deterministic selection for this initial version.
        agent = TEAM_AGENTS[team][0]

    now = datetime.utcnow()

    active_assignment = (
        db.query(Assignment)
        .filter(
            Assignment.complaint_id == complaint_id,
            Assignment.unassigned_at.is_(None),
        )
        .first()
    )

    if active_assignment:
        active_assignment.unassigned_at = now

    assignment = Assignment(
        assignment_id=f"ASN-{secrets.token_hex(8).upper()}",
        complaint_id=complaint_id,
        team=team,
        agent_id=agent,
        assigned_at=now,
        unassigned_at=None,
        assignment_reason=(
            f"Assigned by {assigned_by}; "
            f"category={complaint.category}; "
            f"priority={complaint.priority}"
        ),
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment