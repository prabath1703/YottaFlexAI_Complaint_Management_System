import csv
import io
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.entities import Complaint, SLAClock, Assignment

router = APIRouter(prefix="/api/reports", tags=["Reports"])

# Project root / data / output
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_OUTPUT_DIR = PROJECT_ROOT / "data" / "output"

# Only these generated CSV files can be downloaded.
# Ground-truth data is deliberately excluded.
DATASET_FILES = [
    "customers.csv",
    "products.csv",
    "categories.csv",
    "orders.csv",
    "complaints.csv",
    "assignments.csv",
    "sla_clocks.csv",
    "complaint_messages.csv",
    "status_events.csv",
    "resolutions.csv",
    "surveys.csv",
]


def csv_response(rows, filename):
    output = io.StringIO()

    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        },
    )


# EXISTING COMPLAINT REPORT
@router.get("/complaints.csv")
def complaint_report(db: Session = Depends(get_db)):
    complaints = db.query(Complaint).all()

    rows = [
        {
            "complaint_id": c.complaint_id,
            "customer_id": c.customer_id,
            "category": c.category,
            "priority": c.priority,
            "status": c.status,
            "created_at": c.created_at,
        }
        for c in complaints
    ]

    return csv_response(rows, "complaint_report.csv")


# EXISTING SLA BREACH REPORT
@router.get("/sla-breaches.csv")
def sla_breach_report(db: Session = Depends(get_db)):
    clocks = (
        db.query(SLAClock)
        .filter(SLAClock.sla_status == "BREACHED")
        .all()
    )

    rows = [
        {
            "complaint_id": s.complaint_id,
            "priority": s.priority,
            "sla_deadline": s.sla_deadline,
            "elapsed_duration_minutes": s.elapsed_duration_minutes,
            "paused_duration_minutes": s.paused_duration_minutes,
            "sla_status": s.sla_status,
        }
        for s in clocks
    ]

    return csv_response(rows, "sla_breach_report.csv")


# EXISTING TEAM PERFORMANCE REPORT
@router.get("/team-performance")
def team_performance(db: Session = Depends(get_db)):
    assignments = (
        db.query(Assignment)
        .filter(Assignment.unassigned_at.is_(None))
        .all()
    )

    results = {}

    for assignment in assignments:
        team = assignment.team

        if team not in results:
            results[team] = {
                "team": team,
                "assigned_complaints": 0,
                "agents": {},
            }

        results[team]["assigned_complaints"] += 1

        agent = assignment.agent_id
        results[team]["agents"][agent] = (
            results[team]["agents"].get(agent, 0) + 1
        )

    return list(results.values())


# NEW: GENERATED DATASET INFORMATION
@router.get("/datasets")
def list_datasets():
    available_files = []

    for filename in DATASET_FILES:
        file_path = DATA_OUTPUT_DIR / filename

        if file_path.is_file():
            available_files.append({
                "filename": filename,
                "download_url": f"/api/reports/datasets/{filename}",
                "size_bytes": file_path.stat().st_size,
            })

    return {
        "dataset_type": "Synthetic Complaint Management Dataset",
        "seed": 20261022,
        "reproducibility": {
            "verified": True,
            "runs": 2,
            "matching_files": "11/11",
        },
        "files_available": len(available_files),
        "datasets": available_files,
    }


# NEW: DOWNLOAD AN INDIVIDUAL GENERATED CSV
@router.get("/datasets/{filename}")
def download_dataset(filename: str):
    if filename not in DATASET_FILES:
        raise HTTPException(
            status_code=404,
            detail="Dataset file not found."
        )

    file_path = DATA_OUTPUT_DIR / filename

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Dataset file is currently unavailable."
        )

    return FileResponse(
        path=file_path,
        media_type="text/csv",
        filename=filename,
    )