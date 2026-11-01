import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import Boolean, Date, DateTime, Float, Integer

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.db.database import Base, engine, SessionLocal
from app import models


OUTPUT_DIR = ROOT_DIR / "data" / "output"


def read_csv(filename):
    path = OUTPUT_DIR / filename
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def convert_value(value, column):
    if value == "":
        return None

    column_type = column.type

    if isinstance(column_type, Boolean):
        return value.strip().lower() in ("true", "1", "yes")

    if isinstance(column_type, DateTime):
        return pd.to_datetime(value).to_pydatetime()

    if isinstance(column_type, Date):
        return pd.to_datetime(value).date()

    if isinstance(column_type, Integer):
        return int(float(value))

    if isinstance(column_type, Float):
        return float(value)

    return value


def import_table(session, filename, model):
    dataframe = read_csv(filename)
    records = []

    model_columns = {
        column.name: column
        for column in model.__table__.columns
    }

    for row in dataframe.to_dict(orient="records"):
        record = {}

        for column_name, column in model_columns.items():
            if column_name in row:
                record[column_name] = convert_value(
                    row[column_name], column
                )

        records.append(record)

    if records:
        session.bulk_insert_mappings(model, records)

    print(f"Imported {len(records):,} records into {model.__tablename__}")


def main():
    print("\nStarting CSV import...\n")

    # WARNING: This resets the application database.
    # Run this for the initial import, not after users start managing complaints.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    try:
        customers = read_csv("customers.csv")
        valid_customer_ids = set(customers["customer_id"])

        # Import parent/master tables first.
        import_table(session, "customers.csv", models.Customer)
        import_table(session, "products.csv", models.Product)
        import_table(session, "categories.csv", models.Category)
        import_table(session, "orders.csv", models.Order)

        # Handle the intentionally invalid customer reference.
        complaints = read_csv("complaints.csv")
        complaints["source_customer_id"] = complaints["customer_id"]

        complaints["customer_id"] = complaints["customer_id"].apply(
            lambda value: value if value in valid_customer_ids else ""
        )

        model_columns = {
            column.name: column
            for column in models.Complaint.__table__.columns
        }

        complaint_records = []

        for row in complaints.to_dict(orient="records"):
            record = {}

            for column_name, column in model_columns.items():
                if column_name in row:
                    record[column_name] = convert_value(
                        row[column_name], column
                    )

            complaint_records.append(record)

        session.bulk_insert_mappings(
            models.Complaint,
            complaint_records,
        )

        print(
            f"Imported {len(complaint_records):,} records "
            "into complaints"
        )

        # Import dependent workflow tables.
        import_table(
            session, "complaint_messages.csv",
            models.ComplaintMessage
        )
        import_table(
            session, "assignments.csv",
            models.Assignment
        )
        import_table(
            session, "sla_clocks.csv",
            models.SLAClock
        )
        import_table(
            session, "status_events.csv",
            models.StatusEvent
        )
        import_table(
            session, "resolutions.csv",
            models.Resolution
        )
        import_table(
            session, "surveys.csv",
            models.Survey
        )

        session.commit()

        print("\nCSV import completed successfully!")
        print("Database: data/complaint_management.db")

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    main()