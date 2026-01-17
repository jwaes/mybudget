"""
FastAPI application entry point.

This module initializes the FastAPI application with CORS, exception handlers,
and API routers.
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from mybudget.api import (
    accounts,
    auth,
    budget,
    categories,
    reconciliation,
    targets,
    transactions,
)
from mybudget.config import settings

# Create FastAPI app
app = FastAPI(
    title="MyBudget API",
    version="0.1.0",
    description="Bank-sync budgeting app with intelligent spending targets",
    docs_url="/docs",
    redoc_url="/redoc",
)

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


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


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
