from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Date, DateTime,
    Text, ForeignKey
)
from app.db.database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    customer_since = Column(Date)
    vulnerable_customer_flag = Column(Boolean, default=False)
    created_at = Column(DateTime)


class Product(Base):
    __tablename__ = "products"

    product_id = Column(String, primary_key=True)
    product_name = Column(String)
    product_category = Column(String)
    unit_price = Column(Float)
    safety_risk_level = Column(String)
    active_flag = Column(Boolean, default=True)


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"))
    product_id = Column(String, ForeignKey("products.product_id"))
    order_date = Column(DateTime)
    quantity = Column(Integer)
    unit_price = Column(Float)
    order_total = Column(Float)
    order_status = Column(String)


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(String, primary_key=True)
    category_name = Column(String)
    description = Column(Text)


class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id = Column(String, primary_key=True)

    # Validated FK used by the application
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=True)

    # Original value from CSV, retained for data-quality investigation
    source_customer_id = Column(String, nullable=True)

    order_id = Column(String, ForeignKey("orders.order_id"), nullable=True)
    product_id = Column(String, ForeignKey("products.product_id"), nullable=True)

    channel = Column(String)
    created_at = Column(DateTime)
    description = Column(Text)

    category_id = Column(String, ForeignKey("categories.category_id"))
    category = Column(String)

    severity = Column(String)
    sentiment = Column(String)
    repeat_complaint_flag = Column(Boolean, default=False)
    related_complaint_id = Column(
        String, ForeignKey("complaints.complaint_id"), nullable=True
    )
    safety_issue_flag = Column(Boolean, default=False)
    priority = Column(String)
    status = Column(String)


class ComplaintMessage(Base):
    __tablename__ = "complaint_messages"

    message_id = Column(String, primary_key=True)
    complaint_id = Column(String, ForeignKey("complaints.complaint_id"))
    sender_type = Column(String)
    message_time = Column(DateTime)
    message_text = Column(Text)
    channel = Column(String)


class Assignment(Base):
    __tablename__ = "assignments"

    assignment_id = Column(String, primary_key=True)
    complaint_id = Column(String, ForeignKey("complaints.complaint_id"))
    team = Column(String)
    agent_id = Column(String)
    assigned_at = Column(DateTime)
    unassigned_at = Column(DateTime, nullable=True)
    assignment_reason = Column(Text)


class SLAClock(Base):
    __tablename__ = "sla_clocks"

    sla_id = Column(String, primary_key=True)
    complaint_id = Column(String, ForeignKey("complaints.complaint_id"))
    priority = Column(String)
    start_time = Column(DateTime)
    sla_hours = Column(Integer)
    sla_deadline = Column(DateTime)
    paused_duration_minutes = Column(Integer)
    elapsed_duration_minutes = Column(Integer)
    sla_status = Column(String)

    paused_at = Column(DateTime, nullable=True)
    breached_at = Column(DateTime, nullable=True)

class StatusEvent(Base):
    __tablename__ = "status_events"

    event_id = Column(String, primary_key=True)
    complaint_id = Column(String, ForeignKey("complaints.complaint_id"))
    event_type = Column(String)
    from_status = Column(String)
    to_status = Column(String)
    event_time = Column(DateTime)
    performed_by = Column(String)


class Resolution(Base):
    __tablename__ = "resolutions"

    resolution_id = Column(String, primary_key=True)
    complaint_id = Column(String, ForeignKey("complaints.complaint_id"))
    resolution_type = Column(String)
    resolution_description = Column(Text)
    resolved_at = Column(DateTime)
    resolved_by = Column(String)
    refund_amount = Column(Float)


class Survey(Base):
    __tablename__ = "surveys"

    survey_id = Column(String, primary_key=True)
    complaint_id = Column(String, ForeignKey("complaints.complaint_id"))
    survey_sent_at = Column(DateTime)
    response_at = Column(DateTime, nullable=True)
    rating = Column(Integer, nullable=True)
    feedback = Column(Text)