"""
FastAPI Main Application

This is the entry point for the FastAPI web server.
It defines all HTTP endpoints and integrates:
- Slack webhooks
- Admin API
- Expense system webhooks
- Health checks
- Metrics

API Documentation available at: http://localhost:8080/docs
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.db.connection import get_db, init_db
from app.db.schema import BatchCreateRequest, BatchResponse
from app.agent.graph import run_payroll_workflow
from app.agent.policies import PayrollPolicy
from app.onchain.service import OnchainService

# Setup logging first
setup_logging()
logger = get_logger(__name__)
settings = get_settings()

# ========================================
# CREATE FASTAPI APP
# ========================================
app = FastAPI(
    title="Arc Payroll AI Agent",
    description="Automated payroll processing with AI and blockchain",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ========================================
# CORS MIDDLEWARE
# ========================================
# Allow cross-origin requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================
# STARTUP / SHUTDOWN
# ========================================

@app.on_event("startup")
async def startup_event():
    """
    Run when application starts
    
    Initialize:
    - Database tables
    - Log startup message
    """
    logger.info("Application starting up")
    
    # Initialize database (create tables if needed)
    # In production, use Alembic migrations instead
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """
    Run when application shuts down
    """
    logger.info("Application shutting down")


# ========================================
# HEALTH CHECK
# ========================================

@app.get("/healthz")
async def health_check():
    """
    Health check endpoint
    
    Used by:
    - Docker healthcheck
    - Load balancers
    - Monitoring systems
    
    Returns:
        {"status": "ok"}
    """
    return {"status": "ok"}


@app.get("/")
async def root():
    """
    Root endpoint
    
    Returns basic information about the API
    """
    return {
        "name": "Arc Payroll AI Agent",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/healthz"
    }


# ========================================
# ADMIN ENDPOINTS
# ========================================

@app.post("/admin/trigger")
async def trigger_payroll_batch(
    month: str = Query(..., description="Payroll month (YYYY-MM)")
):
    """
    Trigger a payroll batch manually
    
    This starts the complete LangGraph workflow:
    1. Ingest data
    2. Clean & validate
    3. Compute amounts
    4. Detect anomalies
    5. Summarize
    6. Send to Slack for approval
    7. (After approval) Execute blockchain transactions
    8. Writeback results
    9. Reconcile
    
    Args:
        month: Payroll month in YYYY-MM format
        
    Returns:
        Batch information
        
    Example:
        POST /admin/trigger?month=2025-11
        
        Response:
        {
            "batch_id": "batch_abc123",
            "month": "2025-11",
            "status": "pending_approval",
            "line_count": 5
        }
    """
    logger.info(f"Manual trigger requested for month: {month}")
    
    # Validate month format
    import re
    if not re.match(r'^\d{4}-\d{2}$', month):
        raise HTTPException(
            status_code=400,
            detail="Invalid month format. Use YYYY-MM (e.g., 2025-11)"
        )
    
    try:
        # Generate batch ID
        import uuid
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        
        # Create services
        policy = PayrollPolicy()
        onchain_service = OnchainService()
        
        # TODO: Initialize other services (Slack, database repo, etc.)
        
        # Run workflow
        # Note: This runs synchronously and blocks the request
        # In production, use background tasks or Celery
        final_state = run_payroll_workflow(
            batch_id=batch_id,
            month=month,
            policy=policy,
            onchain_service=onchain_service
        )
        
        # Return response
        return {
            "batch_id": final_state.batch_id,
            "month": final_state.month,
            "status": final_state.metadata.get("final_status", "unknown"),
            "line_count": len(final_state.lines),
            "tx_hashes": final_state.tx_hashes,
            "errors": final_state.errors
        }
    
    except Exception as e:
        logger.error(
            "Failed to trigger payroll batch",
            extra={"month": month, "error": str(e)},
            exc_info=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger batch: {str(e)}"
        )


@app.get("/batches/{batch_id}")
async def get_batch(
    batch_id: str,
    db: Session = Depends(get_db)
):
    """
    Get batch details by ID
    
    Returns information about a specific payroll batch.
    
    Args:
        batch_id: Batch identifier
        
    Returns:
        Batch details including lines and transactions
        
    Example:
        GET /batches/batch_abc123
        
        Response:
        {
            "id": "batch_abc123",
            "month": "2025-11",
            "status": "completed",
            "total_amount": "27500.00",
            "line_count": 5,
            ...
        }
    """
    # TODO: Query database for batch
    # from app.db.models import PayrollBatch
    # batch = db.query(PayrollBatch).filter(PayrollBatch.id == batch_id).first()
    # if not batch:
    #     raise HTTPException(status_code=404, detail="Batch not found")
    # return BatchResponse.from_orm(batch)
    
    # Placeholder response
    return {
        "id": batch_id,
        "status": "not_implemented",
        "message": "Database query not implemented yet"
    }


@app.get("/batches")
async def list_batches(
    month: str = Query(None, description="Filter by month (YYYY-MM)"),
    status: str = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Max results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    List payroll batches
    
    Returns a paginated list of payroll batches.
    Can filter by month and status.
    
    Args:
        month: Optional month filter
        status: Optional status filter
        limit: Maximum results per page
        offset: Offset for pagination
        
    Returns:
        List of batches
        
    Example:
        GET /batches?month=2025-11&status=completed&limit=10
    """
    # TODO: Query database
    # from app.db.models import PayrollBatch
    # query = db.query(PayrollBatch)
    # if month:
    #     query = query.filter(PayrollBatch.month == month)
    # if status:
    #     query = query.filter(PayrollBatch.status == status)
    # batches = query.offset(offset).limit(limit).all()
    # return {"batches": [BatchResponse.from_orm(b) for b in batches]}
    
    return {
        "batches": [],
        "total": 0,
        "message": "Database query not implemented yet"
    }


# ========================================
# SLACK ENDPOINTS
# ========================================

@app.post("/slack/events")
async def slack_events(request):
    """
    Slack events endpoint
    
    Handles:
    - Interactive component actions (button clicks)
    - Slash commands
    - Events (messages, etc.)
    
    This endpoint is configured in your Slack app settings.
    """
    from app.slack.app import slack_handler
    
    # Use Slack Bolt's FastAPI adapter to handle the request
    return await slack_handler.handle(request)


@app.post("/slack/commands")
async def slack_commands(request):
    """
    Slack slash commands endpoint
    
    Handles commands like:
    - /payroll status <batch_id>
    - /payroll trigger <month>
    """
    from app.slack.app import slack_handler
    return await slack_handler.handle(request)


# ========================================
# EXPENSE SYSTEM WEBHOOK
# ========================================

@app.post("/expense/webhook")
async def expense_webhook(payload: dict):
    """
    Receive callbacks from expense system
    
    After we send transaction results to the expense system,
    they might send callbacks with status updates.
    
    Args:
        payload: Callback data from expense system
        
    Returns:
        Acknowledgment
    """
    logger.info("Expense webhook received", extra={"payload": payload})
    
    # TODO: Process expense system callback
    # Update database with expense record status
    
    return {"status": "received"}


# ========================================
# REPORTS ENDPOINTS
# ========================================

@app.get("/reports/{month}/reconcile")
async def get_reconciliation_report(
    month: str,
    format: str = Query("json", description="Response format: json or csv")
):
    """
    Get reconciliation report for a specific month
    
    Args:
        month: Payroll month (YYYY-MM)
        format: Response format (json or csv)
        
    Returns:
        Reconciliation report
    """
    # TODO: Generate reconciliation report from database
    
    if format == "csv":
        # Return CSV file
        from fastapi.responses import Response
        csv_content = "employee_id,wallet,amount,tx_hash,status\n"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=payroll_{month}.csv"
            }
        )
    
    return {
        "month": month,
        "status": "not_implemented",
        "message": "Report generation not implemented yet"
    }


# ========================================
# METRICS ENDPOINT
# ========================================

@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus text format.
    Scraped by Prometheus server for monitoring.
    """
    from prometheus_client import generate_latest
    
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )


if __name__ == "__main__":
    # For development only
    # In production, use uvicorn command:
    # uvicorn app.api.main:app --host 0.0.0.0 --port 8080
    
    import uvicorn
    
    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_dev
    )

