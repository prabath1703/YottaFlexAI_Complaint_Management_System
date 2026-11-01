from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.db.database import create_tables, engine
from app import models
from app.api.complaints import router as complaints_router
from app.api.customers import router as customers_router
from app.api.analytics import router as analytics_router
from app.api.assignments import router as assignments_router
from app.api.sla import router as sla_router
from app.api.messages import router as messages_router
from app.api.resolutions import router as resolutions_router
from app.api.products import router as products_router
from app.api.categories import router as categories_router
from app.api.reports import router as reports_router

from app.services.sla_scheduler import (
    start_sla_scheduler,
    stop_sla_scheduler,
)

app = FastAPI(
    title="Complaint Management System API",
    description="Complaint workflow, assignment and SLA management",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(complaints_router)
app.include_router(customers_router)
app.include_router(analytics_router)
app.include_router(assignments_router)
app.include_router(sla_router)
app.include_router(messages_router)
app.include_router(resolutions_router)
app.include_router(products_router)
app.include_router(categories_router)
app.include_router(reports_router)

@app.on_event("startup")
def startup():
    create_tables()
    start_sla_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    stop_sla_scheduler()

@app.get("/")
def root():
    return {
        "message": "Complaint Management System API",
        "status": "running",
        "documentation": "/docs",
    }



@app.get("/api/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
            "application": "Complaint Management System",
        }
    except Exception as error:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(error),
        }