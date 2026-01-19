"""
FastAPI application entry point.

This module initializes the FastAPI application with CORS, exception handlers,
and API routers.
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy.exc import IntegrityError

from mybudget.api import (
    accounts,
    auth,
    budget,
    categories,
    categorization_rules,
    health,
    reconciliation,
    targets,
    transactions,
)
from mybudget.config import settings
from mybudget.lib.logging import configure_logging

# Configure structured logging
configure_logging(json_logs=not settings.DEBUG, log_level="DEBUG" if settings.DEBUG else "INFO")

# Create FastAPI app
app = FastAPI(
    title="MyBudget API",
    version="0.1.0",
    description="Bank-sync budgeting app with intelligent spending targets",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup Prometheus metrics instrumentation
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/health", "/health/", "/metrics"],
    inprogress_name="mybudget_inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=True)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors with detailed error messages."""
    # Convert errors to JSON-serializable format
    errors = []
    for error in exc.errors():
        err = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": error.get("input"),
        }
        # Don't include 'ctx' as it may contain non-serializable objects
        errors.append(err)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "errors": errors,
        },
    )


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(
    _request: Request, _exc: IntegrityError
) -> JSONResponse:
    """Handle database integrity errors (e.g., unique constraint violations)."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "Database integrity error",
            "error_code": "INTEGRITY_ERROR",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    if settings.DEBUG:
        # In debug mode, show detailed error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": str(exc),
                "error_code": "INTERNAL_ERROR",
                "type": type(exc).__name__,
            },
        )
    else:
        # In production, hide details
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "error_code": "INTERNAL_ERROR",
            },
        )


# Include health router (no prefix, top-level)
app.include_router(health.router, tags=["Health"])

app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["Auth"])
app.include_router(
    accounts.router, prefix=f"{settings.API_V1_PREFIX}/accounts", tags=["Accounts"]
)
app.include_router(
    transactions.router,
    prefix=f"{settings.API_V1_PREFIX}/transactions",
    tags=["Transactions"],
)
app.include_router(
    categories.router,
    prefix=f"{settings.API_V1_PREFIX}/categories",
    tags=["Categories"],
)
app.include_router(
    targets.router, prefix=f"{settings.API_V1_PREFIX}/targets", tags=["Targets"]
)
app.include_router(
    budget.router, prefix=f"{settings.API_V1_PREFIX}/budget", tags=["Budget"]
)
app.include_router(
    reconciliation.router,
    prefix=f"{settings.API_V1_PREFIX}/reconciliations",
    tags=["Reconciliation"],
)
app.include_router(
    categorization_rules.router,
    prefix=f"{settings.API_V1_PREFIX}/rules",
    tags=["Rules"],
)
