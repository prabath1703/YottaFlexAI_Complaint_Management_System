from apscheduler.schedulers.background import BackgroundScheduler

from app.db.database import SessionLocal
from app.models.entities import SLAClock
from app.services.sla_service import evaluate_sla


scheduler = BackgroundScheduler()


def check_sla_deadlines():
    db = SessionLocal()

    try:
        active_clocks = (
            db.query(SLAClock)
            .filter(SLAClock.sla_status.in_(["ACTIVE", "OPEN"]))
            .all()
        )

        for clock in active_clocks:
            evaluate_sla(db, clock)

    except Exception as error:
        print(f"SLA monitoring error: {error}")

    finally:
        db.close()


def start_sla_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            check_sla_deadlines,
            trigger="interval",
            seconds=60,
            id="sla_deadline_monitor",
            replace_existing=True,
        )
        scheduler.start()


def stop_sla_scheduler():
    if scheduler.running:
        scheduler.shutdown()