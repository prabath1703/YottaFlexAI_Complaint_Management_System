
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Complaint, Assignment, SLAClock

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def count_values(rows):
    result = {}

    for key, _ in rows:
        label = key or "Unknown"
        result[label] = result.get(label, 0) + 1

    return result


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    # Total complaints
    total = db.query(Complaint).count()

    # Complaint distribution
    status_rows = db.query(
        Complaint.status, Complaint.complaint_id
    ).all()

    priority_rows = db.query(
        Complaint.priority, Complaint.complaint_id
    ).all()

    category_rows = db.query(
        Complaint.category, Complaint.complaint_id
    ).all()

    by_status = count_values(status_rows)
    by_priority = count_values(priority_rows)
    by_category = count_values(category_rows)

    # Resolution metrics
    resolved = (
        by_status.get("RESOLVED", 0)
        + by_status.get("CLOSED", 0)
    )

    resolution_rate = round(
        (resolved / total) * 100, 2
    ) if total else 0

    # SLA metrics
    sla_clocks = db.query(SLAClock).all()

    total_sla = len(sla_clocks)

    breached_sla = sum(
        1 for clock in sla_clocks
        if (clock.sla_status or "").upper() == "BREACHED"
    )

    completed_sla = sum(
        1 for clock in sla_clocks
        if (clock.sla_status or "").upper() == "COMPLETED"
    )

    evaluated_sla = breached_sla + completed_sla

    sla_compliance_rate = round(
        (completed_sla / evaluated_sla) * 100, 2
    ) if evaluated_sla else 0

    # Current team workload
    assignments = (
        db.query(Assignment)
        .filter(Assignment.unassigned_at.is_(None))
        .all()
    )

    team_workload = {}

    for assignment in assignments:
        team = assignment.team or "Unassigned"
        team_workload[team] = team_workload.get(team, 0) + 1

    # Response
    return {
        "total_complaints": total,

        "by_status": by_status,
        "by_priority": by_priority,
        "by_category": by_category,

        "resolution_metrics": {
            "resolved_complaints": resolved,
            "resolution_rate": resolution_rate,
        },

        "sla_metrics": {
            "total_sla_clocks": total_sla,
            "breached_sla": breached_sla,
            "completed_sla": completed_sla,
            "sla_compliance_rate": sla_compliance_rate,
        },

        "team_workload": team_workload,
    }
